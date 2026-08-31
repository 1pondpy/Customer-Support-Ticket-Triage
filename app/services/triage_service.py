import os
import json
import asyncio
from google import genai
from google.genai import types

from app.schemas.ticket import TicketInput
from app.schemas.triage import TriageResult
from app.services.rag_service import RAGService
from app.config import settings

# 1. Initialize RAG Service
rag_service = RAGService(policy_dir="data/policies")

def get_client() -> genai.Client:
    """ดึง API Key และสร้าง Google GenAI Client อย่างปลอดภัย"""
    api_key = settings.GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API Key not found. Please set GEMINI_API_KEY or GOOGLE_API_KEY in your .env file.")
    return genai.Client(api_key=api_key)

# 2. Supervisor Agent: วิเคราะห์และเลือก Specialist Domain
def supervisor_route_domain(ticket: TicketInput) -> str:
    text = f"{ticket.subject} {ticket.body}".lower()
    
    if any(k in text for k in ["charge", "refund", "bill", "invoice", "payment", "money back", "discrepancy"]):
        return "billing"
    elif any(k in text for k in ["bug", "crash", "error", "freeze", "down", "outage", "keyboard", "printhead"]):
        return "technical"
    elif any(k in text for k in ["code", "otp", "login", "password", "account", "access", "verify", "sign out"]):
        return "account"
    
    return "general"

# 3. Specialist Prompts Provider
def get_specialist_instruction(domain: str) -> str:
    instructions = {
        "technical": (
            "You are a Technical Support Specialist Agent. "
            "Analyze software bugs, crashes, hardware defects, outages, and system errors. "
            "Map category to 'technical', assign appropriate sub_intent, and set assigned_queue to 'tech_support_queue'."
        ),
        "billing": (
            "You are a Billing & Refund Specialist Agent. "
            "Analyze invoices, double charges, subscriptions, and refund inquiries. "
            "Map category to 'billing', assign sub_intent (e.g. 'refund_request', 'dispute_charge'), "
            "and assign to 'billing_default_queue' or 'refund_expert_queue'."
        ),
        "account": (
            "You are an Account & Security Specialist Agent. "
            "Analyze login issues, OTP/verification codes, credential resets, and access permissions. "
            "Map category to 'account', assign sub_intent, and set assigned_queue to 'account_security_queue' or 'general_support_queue'."
        ),
        "general": (
            "You are a General Customer Support Specialist Agent. "
            "Analyze delivery schedules, standard inquiries, feedback, and unclassified questions. "
            "Map category to 'general', assign sub_intent, and set assigned_queue to 'general_triage_queue'."
        )
    }
    return instructions.get(domain, instructions["general"])

# 4. SLA & Escalation Engine
def evaluate_sla_and_priority(ticket: TicketInput, domain: str) -> tuple[str, bool]:
    """คำนวณ Priority (P1-P4) และสถานะ Escalate ตาม Customer Tier และ SLA Policy"""
    text = f"{ticket.subject} {ticket.body}".lower()
    is_outage = any(k in text for k in ["outage", "system down", "security breach", "data leak"])
    
    # Priority 1: Enterprise หรือ มีเหตุการณ์ระบบล่ม / ปัญหาความปลอดภัย
    if ticket.customer_tier == "enterprise" or is_outage:
        return "P1", True
    
    # Priority 2: Pro tier หรือ ปัญหาเรื่องเงิน/บั๊กสำคัญ
    if ticket.customer_tier == "pro" or domain in ["billing", "technical"]:
        return "P2", False
        
    # Priority 3: Free tier ปัญหาทั่วไป
    if ticket.customer_tier == "free":
        return "P3", False
        
    return "P4", False

# 5. Core Triage Orchestrator Function
def triage_ticket_with_llm(ticket: TicketInput) -> TriageResult:
    """
    End-to-end Triage Pipeline:
    1. Supervisor Router เลือก Specialist Domain
    2. RAG Retrieval ดึง Chunks นโยบายที่เกี่ยวข้อง
    3. Specialist Agent วิเคราะห์เนื้อหาผ่าน Gemini LLM
    4. SLA Engine กำกับ Priority และ Escalation Matrix
    """
    # Step 1: Supervisor Routing
    domain = supervisor_route_domain(ticket)
    
    # Step 2: RAG Retrieval
    search_query = f"{ticket.subject} {ticket.body} {domain}"
    try:
        retrieved_chunks = rag_service.search_policies(query=search_query, top_k=3)
        context_text = "\n\n".join([f"[{chunk['source']}]\n{chunk['text']}" for chunk in retrieved_chunks])
        policy_citations = list(set([c["source"] for c in retrieved_chunks])) if retrieved_chunks else ["routing_policy.txt"]
    except Exception:
        context_text = "Standard routing and SLA policies apply."
        policy_citations = ["routing_policy.txt"]

    # Step 3: Specialist Agent Prompt
    specialist_prompt = get_specialist_instruction(domain)
    
    ticket_payload = {
        "subject": ticket.subject,
        "body": ticket.body,
        "customer_tier": ticket.customer_tier,
        "metadata": ticket.metadata or {}
    }

    user_content = f"""=== RETRIEVED POLICIES CONTEXT ===
{context_text}

=== INCOMING TICKET ===
{json.dumps(ticket_payload, ensure_ascii=False, indent=2)}
"""

    # Step 4: Gemini LLM Structured Call
    client = get_client()
    model_name = settings.MODEL_NAME or os.getenv("MODEL_NAME") or "gemini-3.6-flash"

    response = client.models.generate_content(
        model=model_name,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=specialist_prompt,
            response_mime_type="application/json",
            response_schema=TriageResult,
            temperature=0.0
        )
    )

    # Step 5: แปลงผลลัพธ์และ Override ด้วย SLA Policy Engine
    result = Tydantic_data = json.loads(response.text)
    priority, escalate = evaluate_sla_and_priority(ticket, domain)
    
    return TriageResult(
        category=result.get("category", domain),
        sub_intent=result.get("sub_intent", "general_inquiry"),
        priority=priority,
        assigned_queue=result.get("assigned_queue", "general_triage_queue"),
        industry=result.get("industry"),
        suggested_macro_id=result.get("suggested_macro_id"),
        internal_notes=f"[{domain.upper()} Specialist]: {result.get('internal_notes', '')}",
        policy_citations=policy_citations,
        confidence=float(result.get("confidence", 0.95)),
        escalate=escalate
    )

# 6. Async Non-blocking Wrapper (สำหรับ Batch Concurrency)
async def triage_ticket_async(ticket: TicketInput) -> TriageResult:
    """รันฟังก์ชัน triage_ticket_with_llm แบบ Non-blocking ผ่าน ThreadPool"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, triage_ticket_with_llm, ticket)