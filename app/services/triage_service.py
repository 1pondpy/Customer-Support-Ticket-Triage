import os
import json
import asyncio
from typing import List, Dict, Any, Tuple
from groq import Groq

from app.schemas.ticket import TicketInput
from app.schemas.triage import TriageResult, TicketCategory, TicketPriority
from app.services.rag_service import RAGService
from app.config import settings

rag_service = RAGService(policy_dir="data/policies")

def get_client() -> Groq:
    """สร้าง Groq Client อย่างปลอดภัย"""
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("API Key not found. Please set GROQ_API_KEY in your .env file.")
    return Groq(api_key=api_key)

def intent_router_agent(ticket: TicketInput) -> TicketCategory:
    text = f"{ticket.subject} {ticket.body}".lower()
    if any(k in text for k in ["refund", "money back", "return payment", "cancel order and refund"]):
        return "refund"
    elif any(k in text for k in ["charge", "bill", "invoice", "overcharge", "double charge", "discrepancy"]):
        return "billing"
    elif any(k in text for k in ["track", "ship", "package", "delivery", "courier", "parcel", "delay"]):
        return "shipping"
    elif any(k in text for k in ["hack", "breach", "security", "leak", "unauthorized", "suspicious", "phishing"]):
        return "security"
    elif any(k in text for k in ["login", "password", "otp", "2fa", "account", "locked", "credential"]):
        return "account"
    elif any(k in text for k in ["bug", "crash", "error", "down", "outage", "500", "api fail", "freeze"]):
        return "technical"
    elif any(k in text for k in ["feedback", "compliment", "suggest", "improve", "love the app", "terrible ui"]):
        return "feedback"
    return "other"

def get_domain_expert_instruction(category: TicketCategory) -> str:
    instructions: Dict[TicketCategory, str] = {
        "technical": (
            "You are a Technical Support Specialist Agent. Analyze system bugs, crashes, and outages. "
            "Set category='technical', assigned_queue='tech_support_queue', and pick an appropriate macro."
        ),
        "billing": (
            "You are a Billing Specialist Agent. Analyze subscriptions and invoice disputes. "
            "Set category='billing', assigned_queue='billing_default_queue', and pick an appropriate macro."
        ),
        "refund": (
            "You are a Refund Specialist Agent. Evaluate return criteria and money-back requests. "
            "Set category='refund', assigned_queue='refund_expert_queue', and pick an appropriate macro."
        ),
        "account": (
            "You are an Account & Security Specialist Agent. Analyze login issues and 2FA/OTP resets. "
            "Set category='account', assigned_queue='account_security_queue', and pick an appropriate macro."
        ),
        "shipping": (
            "You are a Shipping Specialist Agent. Analyze parcel tracking and courier delays. "
            "Set category='shipping', assigned_queue='shipping_logistics_queue', and pick an appropriate macro."
        ),
        "feedback": (
            "You are a Customer Experience Feedback Agent. Analyze suggestions and compliments. "
            "Set category='feedback', assigned_queue='customer_feedback_queue', and pick an appropriate macro."
        ),
        "security": (
            "You are a Cybersecurity Specialist Agent. Analyze data leaks and unauthorized logins. "
            "Set category='security', assigned_queue='security_incident_queue', and pick an appropriate macro."
        ),
        "other": (
            "You are a General Support Agent. Handle inquiries that do not match specialized queues. "
            "Set category='other', assigned_queue='general_triage_queue', and pick an appropriate macro."
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
    # 1. Router
    category = intent_router_agent(ticket)

    # 2. RAG
    query = f"{ticket.subject} {ticket.body} {category}"
    retrieved_chunks = rag_service.search_policies(query=query, top_k=3)
    policy_context = "\n\n".join([f"[{c['source']}]\n{c['text']}" for c in retrieved_chunks])
    retrieved_sources = list(set([c["source"] for c in retrieved_chunks])) if retrieved_chunks else ["routing_policy.txt"]

    # 3. Reasoning via Groq LLM
    expert_instruction = get_domain_expert_instruction(category)
    client = get_client()
    model_name = settings.MODEL_NAME or "llama-3.3-70b-versatile"

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

    # 4. Priority Scorer
    priority, escalate, priority_justification = priority_scorer(ticket, category)

    # 5. Judge Agent
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