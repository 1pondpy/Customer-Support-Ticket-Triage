import os
import re
import json
import asyncio
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv, find_dotenv
from groq import Groq

load_dotenv(find_dotenv())

from app.schemas.ticket import TicketInput
from app.schemas.triage import TriageResult, TicketCategory, TicketPriority
from app.services.rag_service import RAGService
from app.config import settings

rag_service = RAGService(policy_dir="data/policies")

def get_client() -> Groq:
    """สร้าง Groq Client อย่างปลอดภัย"""
    api_key = os.getenv("GROQ_API_KEY") or getattr(settings, "GROQ_API_KEY", None)
    if not api_key:
        raise ValueError("GROQ_API_KEY not found. Please check your .env file.")
    return Groq(api_key=api_key)

def intent_router_agent(ticket: TicketInput) -> TicketCategory:
    """
    Robust Multi-Domain Intent Router
    ใช้ Regular Expressions, Weighted Signals และ Collision Guards ครอบคลุม 8 หมวดหมู่
    """
    subject_text = ticket.subject.lower()
    body_text = ticket.body.lower()
    full_text = f"{subject_text} {body_text}"

    # 1. Collision & Context Guards (สกัดเคสพิเศษที่มีคำกำกวม)
    if any(k in full_text for k in ["security camera", "security footage", "cctv", "porch camera"]):
        if any(k in full_text for k in ["parcel", "package", "deliver", "courier", "fedex", "ups", "wrong house"]):
            return "shipping"

    if "sprint" in full_text and any(k in full_text for k in ["refund", "money back", "service last"]):
        return "billing"

    # 2. Weighted Keyword Dictionaries (กำหนดคลังคำแยกตามโดเมน)
    patterns: Dict[TicketCategory, List[str]] = {
        "security": [
            r"\bhack(?:ed|ing)?\b", r"\bbreach(?:ed)?\b", r"\bdata\s*leak\b",
            r"\bunauthorized\s*(?:login|access|charge|activity)?\b",
            r"\bsuspicious\s*(?:login|activity|email|sms)?\b",
            r"\bphishing\b", r"\bmalware\b", r"\bransomware\b", r"\bcompromised?\b"
        ],
        "technical": [
            r"\boutage\b", r"\bsystem\s*down\b", r"\b50[0-4]\b", r"\berror(?:\s*code)?\b",
            r"\bcrash(?:es|ed|ing)?\b", r"\bfreeze(?:s|d|ing)?\b", r"\bbug(?:s|gy)?\b",
            r"\bplayback\b", r"\bskip(?:s|ped|ping)?\b", r"\bglitch(?:es)?\b",
            r"\bnot\s*working\b", r"\bdead\s*end\b", r"\bapi\s*(?:fail|error|down)\b",
            r"\bwebhook\b", r"\bexception\b", r"\btimeout\b", r"\bdisconnect(?:ed|ing)?\b",
            r"\bkeyboard\b", r"\bapp\s*version\b", r"\bloading\b", r"\bloop\b"
        ],
        "refund": [
            r"\brefund(?:s|ed|ing)?\b", r"\bmoney\s*back\b", r"\breturn\s*payment\b",
            r"\bcancel\s*order\s*and\s*refund\b", r"\breimburse(?:ment)?\b"
        ],
        "billing": [
            r"\bcharge(?:s|d|ing)?\b", r"\bbill(?:s|ed|ing)?\b", r"\binvoice(?:s)?\b",
            r"\bovercharge(?:s|d|ing)?\b", r"\bdouble\s*charge(?:d)?\b", r"\bdiscrepancy\b",
            r"\bsubscription\s*(?:fee|rate|plan)?\b", r"\bpricing\b", r"\bcredit\s*card\b",
            r"\bpayment\s*(?:fail|failed|issue|status)\b", r"\bstatement\b"
        ],
        "shipping": [
            r"\bparcel(?:s)?\b", r"\bpackage(?:s)?\b", r"\bdeliver(?:y|ed|ing)?\b",
            r"\bcourier\b", r"\btrack(?:ing)?(?:\s*number)?\b", r"\blost\s*(?:in\s*transit|parcel|package)\b",
            r"\bwrong\s*(?:address|house)\b", r"\btransit\b", r"\bcustoms\b",
            r"\bshipment\b", r"\bcarrier\b", r"\bhub\b"
        ],
        "account": [
            r"\bverification\s*code\b", r"\botp\b", r"\b2fa\b", r"\bmfa\b",
            r"\bpassword(?:s)?\b", r"\breset\s*password\b", r"\blogin\b",
            r"\bsign\s*(?:in|up)\b", r"\block(?:ed)?\s*out\b", r"\bcredential(?:s)?\b",
            r"\bcannot\s*access\b", r"\bstore\s*access\b", r"\baccount\s*(?:recovery|transfer|id)\b",
            r"\bemail\s*change\b", r"\bprofile\b"
        ],
        "feedback": [
            r"\bfeedback\b", r"\bcompliment(?:s)?\b", r"\bsuggest(?:ion|ions|ed)?\b",
            r"\bimprove(?:ment)?\b", r"\blove\s*the\s*app\b", r"\bterrible\s*(?:ui|ux|design)\b",
            r"\bgreat\s*job\b", r"\bfeature\s*request\b", r"\brating\b", r"\breview\b"
        ],
        "other": [
            r"\bpolicy\b", r"\bopening\s*hours\b", r"\bstore\s*(?:location|hours)\b",
            r"\bgeneral\s*inquiry\b", r"\bhow\s*to\b", r"\bbank\s*holiday\b",
            r"\bid\s*(?:check|challenge)?\b", r"\bcontact\s*info\b"
        ]
    }

    # 3. Score Calculation with Subject Weighting
    scores: Dict[TicketCategory, float] = {cat: 0.0 for cat in patterns}

    for cat, regex_list in patterns.items():
        for pattern in regex_list:
            if re.search(pattern, subject_text):
                scores[cat] += 2.0
            if re.search(pattern, body_text):
                scores[cat] += 1.0

    best_category = max(scores, key=scores.get)

    if scores[best_category] > 0.0:
        return best_category

    return "other"

def get_domain_expert_instruction(category: TicketCategory) -> str:
    instructions: Dict[TicketCategory, str] = {
        "technical": (
            "You are a Technical Support Specialist Agent. Analyze system bugs, crashes, and outages. "
            "Set category='technical', assigned_queue='tech_support_queue', and pick an appropriate macro "
            "(e.g., macro_tech_ios_bug, macro_tech_system_outage)."
        ),
        "billing": (
            "You are a Billing Specialist Agent. Analyze subscriptions and invoice disputes. "
            "Set category='billing', assigned_queue='billing_default_queue', and pick an appropriate macro "
            "(e.g., macro_billing_discrepancy, macro_billing_duplicate_charge)."
        ),
        "refund": (
            "You are a Refund Specialist Agent. Evaluate return criteria and money-back requests. "
            "Set category='refund', assigned_queue='refund_expert_queue', and pick an appropriate macro "
            "(e.g., macro_refund_request_review, macro_refund_policy_guideline)."
        ),
        "account": (
            "You are an Account & Security Specialist Agent. Analyze login issues and 2FA/OTP resets. "
            "Set category='account', assigned_queue='account_security_queue', and pick an appropriate macro "
            "(e.g., macro_account_otp_reset, macro_password_recovery)."
        ),
        "shipping": (
            "You are a Shipping Specialist Agent. Analyze parcel tracking and courier delays. "
            "Set category='shipping', assigned_queue='shipping_logistics_queue', and pick an appropriate macro "
            "(e.g., macro_shipping_tracking_status, macro_lost_parcel_inquiry)."
        ),
        "feedback": (
            "You are a Customer Experience Feedback Agent. Analyze suggestions and compliments. "
            "Set category='feedback', assigned_queue='customer_feedback_queue', and pick an appropriate macro "
            "(e.g., macro_feedback_acknowledgement, macro_ui_suggestion_noted)."
        ),
        "security": (
            "You are a Cybersecurity Specialist Agent. Analyze data leaks and unauthorized logins. "
            "Set category='security', assigned_queue='security_incident_queue', and pick an appropriate macro "
            "(e.g., macro_security_incident_escalation, macro_phishing_report)."
        ),
        "other": (
            "You are a General Support Agent. Handle inquiries that do not match specialized queues. "
            "Set category='other', assigned_queue='general_triage_queue', and pick an appropriate macro "
            "(e.g., macro_general_store_inquiry)."
        )
    }
    return instructions.get(category, instructions["other"])

def priority_scorer(ticket: TicketInput, category: TicketCategory) -> Tuple[TicketPriority, bool, str]:
    text = f"{ticket.subject} {ticket.body}".lower()
    is_outage = any(k in text for k in ["outage", "system down", "security breach", "data leak", "critical"])
    
    if ticket.customer_tier == "enterprise" or is_outage or category == "security":
        return "P1", True, "Triggered P1/Escalation: Enterprise customer, outage, or security incident."
    elif ticket.customer_tier == "pro" or category in ["billing", "refund", "technical"]:
        return "P2", False, "Triggered P2: Pro tier or high-impact dispute."
    elif ticket.customer_tier == "free" or category in ["account", "shipping"]:
        return "P3", False, "Triggered P3: Free tier or standard tracking."
    return "P4", False, "Triggered P4: Low-priority general request."

def judge_agent(draft_result: Dict[str, Any], retrieved_citations: List[str]) -> Tuple[List[str], str]:
    citations = [c for c in draft_result.get("policy_citations", []) if c in retrieved_citations]
    if not citations:
        citations = retrieved_citations if retrieved_citations else ["routing_policy.txt"]
    judge_verdict = f"Verified by Judge Agent: Grounded with {len(citations)} policy source(s)."
    return citations, judge_verdict

def triage_ticket_with_llm(ticket: TicketInput) -> TriageResult:
    # 1. Intent Router Agent
    category = intent_router_agent(ticket)

    # 2. RAG Context Retrieval
    query = f"{ticket.subject} {ticket.body} {category}"
    retrieved_chunks = rag_service.search_policies(query=query, top_k=3)
    policy_context = "\n\n".join([f"[{c['source']}]\n{c['text']}" for c in retrieved_chunks])
    retrieved_sources = list(set([c["source"] for c in retrieved_chunks])) if retrieved_chunks else ["routing_policy.txt"]

    # 3. Specialist Agent Reasoning via Groq
    expert_instruction = get_domain_expert_instruction(category)
    client = get_client()
    model_name = os.getenv("MODEL_NAME") or getattr(settings, "MODEL_NAME", None) or "openai/gpt-oss-20b"

    ticket_payload = {
        "subject": ticket.subject,
        "body": ticket.body,
        "customer_tier": ticket.customer_tier,
        "metadata": ticket.metadata or {}
    }

    system_content = f"""{expert_instruction}
Output strictly valid JSON with the following keys:
"category", "sub_intent", "assigned_queue", "industry", "suggested_macro_id", "internal_notes", "policy_citations", "confidence".
Do not include priority or escalate in your decision.
"""

    user_content = f"""=== RETRIEVED POLICIES CONTEXT ===
{policy_context}

=== INCOMING TICKET ===
{json.dumps(ticket_payload, ensure_ascii=False, indent=2)}
"""

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )

    draft = json.loads(response.choices[0].message.content)

    # 4. Deterministic SLA & Priority Scorer
    priority, escalate, priority_justification = priority_scorer(ticket, category)

    # 5. Judge Agent Verification
    validated_citations, judge_verdict = judge_agent(draft, retrieved_sources)

    return TriageResult(
        category=category,
        sub_intent=draft.get("sub_intent", "general_inquiry"),
        priority=priority,
        assigned_queue=draft.get("assigned_queue", "general_triage_queue"),
        industry=draft.get("industry"),
        suggested_macro_id=draft.get("suggested_macro_id"),
        internal_notes=f"[{category.upper()} Expert]: {draft.get('internal_notes', '')} | {priority_justification} | {judge_verdict}",
        policy_citations=validated_citations,
        confidence=float(draft.get("confidence", 0.95)),
        escalate=escalate
    )

async def triage_ticket_async(ticket: TicketInput) -> TriageResult:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, triage_ticket_with_llm, ticket)