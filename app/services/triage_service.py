import os
import json
import asyncio
from typing import List, Dict, Any, Tuple
from google import genai
from google.genai import types

from app.schemas.ticket import TicketInput
from app.schemas.triage import TriageResult, TicketCategory, TicketPriority
from app.services.rag_service import RAGService
from app.config import settings

# 1. Initialize Service
rag_service = RAGService(policy_dir="data/policies")

def get_client() -> genai.Client:
    api_key = settings.GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API Key not found. Please set GEMINI_API_KEY in your .env file.")
    return genai.Client(api_key=api_key)

# ---------------------------------------------------------------------------
# Component 1: Intent Router Agent (แยกประเภทปัญหาหลัก 1 ใน 8 หมวดหมู่)
# ---------------------------------------------------------------------------
def intent_router_agent(ticket: TicketInput) -> TicketCategory:
    text = f"{ticket.subject} {ticket.body}".lower()
    
    # ลำดับการคัดแยกหมวดหมู่ตามคีย์เวิร์ดเฉพาะทาง
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

# ---------------------------------------------------------------------------
# Component 2: Domain Experts System Prompts (กำหนดบทบาทผู้เชี่ยวชาญเฉพาะด้าน)
# ---------------------------------------------------------------------------
def get_domain_expert_instruction(category: TicketCategory) -> str:
    instructions: Dict[TicketCategory, str] = {
        "technical": (
            "You are a Technical Support Specialist Agent. "
            "Analyze system bugs, error codes, crashes, and outages. "
            "Set category='technical', assigned_queue='tech_support_queue', and pick an appropriate macro from macro_catalog.txt."
        ),
        "billing": (
            "You are a Billing Specialist Agent. "
            "Analyze recurring subscriptions, invoice disputes, and erroneous charges. "
            "Set category='billing', assigned_queue='billing_default_queue', and pick an appropriate macro from macro_catalog.txt."
        ),
        "refund": (
            "You are a Refund Specialist Agent. "
            "Evaluate return eligibility, money-back requests, and order cancellations. "
            "Set category='refund', assigned_queue='refund_expert_queue', and pick an appropriate macro from macro_catalog.txt."
        ),
        "account": (
            "You are an Account & Security Specialist Agent. "
            "Analyze credential resets, 2FA/OTP issues, and user lockouts. "
            "Set category='account', assigned_queue='account_security_queue', and pick an appropriate macro from macro_catalog.txt."
        ),
        "shipping": (
            "You are a Shipping & Logistics Specialist Agent. "
            "Analyze parcel tracking, courier delays, and shipment issues. "
            "Set category='shipping', assigned_queue='shipping_logistics_queue', and pick an appropriate macro from macro_catalog.txt."
        ),
        "feedback": (
            "You are a Customer Experience Feedback Agent. "
            "Analyze UX improvements, feature requests, and compliments. "
            "Set category='feedback', assigned_queue='customer_feedback_queue', and pick an appropriate macro from macro_catalog.txt."
        ),
        "security": (
            "You are a Cybersecurity Incident Specialist Agent. "
            "Analyze data compromises, unauthorized logins, and threat alerts. "
            "Set category='security', assigned_queue='security_incident_queue', and pick an appropriate macro from macro_catalog.txt."
        ),
        "other": (
            "You are a General Care Triage Agent. "
            "Handle standard queries that do not belong to specialized queues. "
            "Set category='other', assigned_queue='general_triage_queue', and pick an appropriate macro from macro_catalog.txt."
        )
    }
    return instructions.get(category, instructions["other"])

# ---------------------------------------------------------------------------
# Component 3: Priority Scorer (ประเมินระดับความสำคัญ P1-P4 ตาม SLA Matrix)
# ---------------------------------------------------------------------------
def priority_scorer(ticket: TicketInput, category: TicketCategory) -> Tuple[TicketPriority, bool, str]:
    text = f"{ticket.subject} {ticket.body}".lower()
    is_outage = any(k in text for k in ["outage", "system down", "security breach", "data leak", "critical"])
    
    # Priority 1: บังคับ Escalate เมื่อเป็นลูกค้าระดับ Enterprise, ระบบล่ม หรือปัญหาความปลอดภัย
    if ticket.customer_tier == "enterprise" or is_outage or category == "security":
        return "P1", True, "Triggered P1/Escalation: Enterprise customer, outage, or security incident."
    # Priority 2: ลูกค้ากลุ่ม Pro หรือเคสข้อพิพาทการเงิน/เทคนิคเร่งด่วน
    elif ticket.customer_tier == "pro" or category in ["billing", "refund", "technical"]:
        return "P2", False, "Triggered P2: Pro tier or urgent billing/technical dispute."
    # Priority 3: ลูกค้าทั่วไป (Free tier) หรือเคสติดตามพัสดุ/บัญชีทั่วไป
    elif ticket.customer_tier == "free" or category in ["account", "shipping"]:
        return "P3", False, "Triggered P3: Free tier standard inquiry or account/shipping tracking."
    # Priority 4: ข้อเสนอแนะหรือคำถามที่ไม่เร่งด่วน
    return "P4", False, "Triggered P4: Low-urgency feedback or standard general request."

# ---------------------------------------------------------------------------
# Component 4: Judge Agent (ตรวจสอบความถูกต้องของ Policy Citations และผลลัพธ์)
# ---------------------------------------------------------------------------
def judge_agent(draft_result: Dict[str, Any], retrieved_citations: List[str]) -> Tuple[List[str], str]:
    # ตรวจสอบว่า Citation ที่ตอบมามีอยู่ในเอกสาร RAG จริงหรือไม่
    citations = [c for c in draft_result.get("policy_citations", []) if c in retrieved_citations]
    if not citations:
        citations = retrieved_citations if retrieved_citations else ["routing_policy.txt"]
    
    judge_verdict = f"Verified by Judge Agent: Grounded with {len(citations)} policy source(s)."
    return citations, judge_verdict

# ---------------------------------------------------------------------------
# Main Multi-Agent Orchestration Pipeline
# ---------------------------------------------------------------------------
def triage_ticket_with_llm(ticket: TicketInput) -> TriageResult:
    # 1. Intent Router Agent
    category = intent_router_agent(ticket)
    
    # 2. Policy RAG Agent
    query = f"{ticket.subject} {ticket.body} {category}"
    retrieved_chunks = rag_service.search_policies(query=query, top_k=3)
    policy_context = "\n\n".join([f"[{c['source']}]\n{c['text']}" for c in retrieved_chunks])
    retrieved_sources = list(set([c["source"] for c in retrieved_chunks])) if retrieved_chunks else ["routing_policy.txt"]

    # 3. Domain Expert LLM Reasoning
    expert_instruction = get_domain_expert_instruction(category)
    client = get_client()
    model_name = settings.MODEL_NAME or os.getenv("MODEL_NAME") or "gemini-3.6-flash"

    payload = {
        "subject": ticket.subject,
        "body": ticket.body,
        "customer_tier": ticket.customer_tier,
        "metadata": ticket.metadata or {}
    }

    prompt = f"""=== RETRIEVED POLICIES CONTEXT ===
{policy_context}

=== INCOMING TICKET ===
{json.dumps(payload, ensure_ascii=False, indent=2)}

Analyze the ticket and generate JSON strictly matching TriageResult schema.
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=expert_instruction,
            response_mime_type="application/json",
            response_schema=TriageResult,
            temperature=0.0
        )
    )
    draft = json.loads(response.text)

    # 4. Priority Scorer
    priority, escalate, priority_justification = priority_scorer(ticket, category)

    # 5. Judge Agent Grounding Check
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

# ---------------------------------------------------------------------------
# Async Batch Non-blocking Wrapper
# ---------------------------------------------------------------------------
async def triage_ticket_async(ticket: TicketInput) -> TriageResult:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, triage_ticket_with_llm, ticket)