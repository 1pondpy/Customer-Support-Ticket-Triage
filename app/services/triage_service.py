## ขั้นที่ 1 (Supervisor Routing): สแกนคีย์เวิร์ดใน Subject และ Body เพื่อเลือกสายงาน Specialist ที่เหมาะสม (technical, billing, account, หรือ general)
## ขั้นที่ 2 (RAG Retrieval): ค้นหาข้อความที่ตรงกันจากไฟล์นโยบาย 4 ฉบับ (data/policies/) ดึง Chunks นโยบายที่เกี่ยวข้องมาเตรียมไว้เป็น Context
## ขั้นที่ 3 (Prompt Framing): ประกอบร่างตั๋วลูกค้าเข้ากับบริบทนโยบาย โดยใช้ Delimiters (=== ... ===) ตีกรอบขอบเขตอย่างชัดเจน เพื่อป้องกัน Prompt Injection และลดการเกิดภาพหลอน (Hallucination)
## ขั้นที่ 4 (Gemini LLM Inference): ส่งไปประมวลผลผ่านโมเดล Gemini โดยตั้งค่า temperature=0.0 และบังคับโครงสร้างคำตอบออกมาเป็น JSON รูปแบบ TriageResult
## ขั้นที่ 5 (Deterministic SLA Enforcement): ตรวจเช็ค Customer Tier และปัญหาเร่งด่วน หากเป็น enterprise หรือระบบล่ม (outage) จะปรับเป็น P1 และยกธง escalate=True ทันที พร้อมแนบรายชื่อไฟล์ลงใน policy_citations
## ขั้นที่ 6 (Async Non-blocking Output): ประมวลผลผ่าน ThreadPool แบบ Asynchronous เพื่อรองรับการประมวลผลพร้อมกันหลายตั๋วบนเอนด์พอยต์ Batch และส่งผลลัพธ์กลับแบบ HTTP 200 OK

import os
import json
import asyncio
from google import genai
from google.genai import types

from app.schemas.ticket import TicketInput
from app.schemas.triage import TriageResult
from app.services.rag_service import RAGService
from app.config import settings

# ---------------------------------------------------------
# 1. การตั้งค่าและสร้างการเชื่อมต่อบริการพื้นฐาน (Initialization)
# ---------------------------------------------------------

# โหลดบริการ RAG เพื่อเตรียมพร้อมสำหรับการดึงชิ้นส่วนนโยบายจาก data/policies/
rag_service = RAGService(policy_dir="data/policies")

def get_client() -> genai.Client:
    """ตรวจสอบ API Key จากหลายแหล่งและคืนค่า Google GenAI Client"""
    api_key = settings.GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API Key not found. Please set GEMINI_API_KEY or GOOGLE_API_KEY in your .env file.")
    return genai.Client(api_key=api_key)

# ---------------------------------------------------------
# 2. ตัวกำหนดเส้นทาง Supervisor (Supervisor Router Agent)
# ---------------------------------------------------------

def supervisor_route_domain(ticket: TicketInput) -> str:
    """วิเคราะห์คำสำคัญใน Subject และ Body เพื่อเลือกสายงาน Specialist ที่เหมาะสม"""
    text = f"{ticket.subject} {ticket.body}".lower()
    
    # ตรวจจับปัญหาด้านการเงิน ใบแจ้งหนี้ และการขอเงินคืน
    if any(k in text for k in ["charge", "refund", "bill", "invoice", "payment", "money back", "discrepancy"]):
        return "billing"
    # ตรวจจับปัญหาข้อผิดพลาดเชิงเทคนิค ระบบขัดข้อง หรือบั๊กการทำงาน
    elif any(k in text for k in ["bug", "crash", "error", "freeze", "down", "outage", "keyboard", "printhead"]):
        return "technical"
    # ตรวจจับปัญหาการเข้าสู่ระบบ รหัสยืนยันตัวตน และความปลอดภัยของบัญชี
    elif any(k in text for k in ["code", "otp", "login", "password", "account", "access", "verify", "sign out"]):
        return "account"
    
    # หากไม่ตรงกับคำสำคัญข้างต้น จัดเข้าหมวดหมู่การสอบถามทั่วไป
    return "general"

# ---------------------------------------------------------
# 3. คลังคำสั่งเฉพาะทางสำหรับ Specialist (Specialist Prompts)
# ---------------------------------------------------------

def get_specialist_instruction(domain: str) -> str:
    """ส่งคืน System Instruction ประจำสายงานของผู้เชี่ยวชาญโดเมนนั้น"""
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

# ---------------------------------------------------------
# 4. กลไกกฎควบคุม SLA และความเร่งด่วน (Deterministic SLA Engine)
# ---------------------------------------------------------

def evaluate_sla_and_priority(ticket: TicketInput, domain: str) -> tuple[str, bool]:
    """คำนวณระดับความสำคัญ Priority (P1-P4) และสถานะ Escalation ด้วยกฎตายตัวตาม SLA Policy"""
    text = f"{ticket.subject} {ticket.body}".lower()
    # ดักจับคำสำคัญที่ระบุถึงปัญหาระบบล่มหรือความปลอดภัยข้อมูล
    is_outage = any(k in text for k in ["outage", "system down", "security breach", "data leak"])
    
    # Priority 1: บังคับยกระดับเคสด่วนสำหรับลูกค้า Enterprise หรือเมื่อระบบหลักมีปัญหา/ข้อมูลรั่ว
    if ticket.customer_tier == "enterprise" or is_outage:
        return "P1", True
    
    # Priority 2: ลูกค้าระดับ Pro หรือตั๋วสายการเงินและเทคนิคที่มีความเร่งด่วนปานกลาง
    if ticket.customer_tier == "pro" or domain in ["billing", "technical"]:
        return "P2", False
        
    # Priority 3: ตั๋วระดับปกติจากกลุ่มลูกค้าระดับ Free
    if ticket.customer_tier == "free":
        return "P3", False
        
    # Priority 4: กรณีอื่น ๆ ทั่วไปหรือข้อเสนอแนะ
    return "P4", False

# ---------------------------------------------------------
# 5. ท่อประมวลผลหลัก (Core Triage Orchestration Pipeline)
# ---------------------------------------------------------

def triage_ticket_with_llm(ticket: TicketInput) -> TriageResult:
    """ควบคุมลำดับขั้นตอนการคัดแยกตั๋วตั้งแต่ดึงบริบทนโยบาย เรียก LLM ไปจนถึงตรวจทาน SLA"""
    
    # ขั้นตอนที่ 1: ตรวจสอบและส่งต่องานไปยัง Specialist Domain
    domain = supervisor_route_domain(ticket)
    
    # ขั้นตอนที่ 2: ดึงชิ้นส่วนนโยบายที่ตรงกับข้อความตั๋วผ่านระบบ RAG (Policy Grounding)
    search_query = f"{ticket.subject} {ticket.body} {domain}"
    try:
        retrieved_chunks = rag_service.search_policies(query=search_query, top_k=3)
        context_text = "\n\n".join([f"[{chunk['source']}]\n{chunk['text']}" for chunk in retrieved_chunks])
        # รวบรวมรายชื่อไฟล์นโยบายเพื่อนำไปใช้เป็น Policy Citations
        policy_citations = list(set([c["source"] for c in retrieved_chunks])) if retrieved_chunks else ["routing_policy.txt"]
    except Exception:
        context_text = "Standard routing and SLA policies apply."
        policy_citations = ["routing_policy.txt"]

    # ขั้นตอนที่ 3: เลือก Prompt ประจำสายงานและประกอบข้อความตั๋วภายใต้กรอบ Delimiters
    specialist_prompt = get_specialist_instruction(domain)
    
    ticket_payload = {
        "subject": ticket.subject,
        "body": ticket.body,
        "customer_tier": ticket.customer_tier,
        "metadata": ticket.metadata or {}
    }

    # วางกรอบ Delimiters ชัดเจนเพื่อแยกบริบทนโยบายออกจากตั๋วลูกค้า ป้องกันปัญหาภาพหลอน (Hallucination)
    user_content = f"""=== RETRIEVED POLICIES CONTEXT ===
{context_text}

=== INCOMING TICKET ===
{json.dumps(ticket_payload, ensure_ascii=False, indent=2)}
"""

    # ขั้นตอนที่ 4: ส่งประมวลผลผ่าน Gemini API บังคับโครงสร้างผลลัพธ์เป็น JSON และคุมความเสถียร
    client = get_client()
    model_name = settings.MODEL_NAME or os.getenv("MODEL_NAME") or "gemini-3.6-flash"

    response = client.models.generate_content(
        model=model_name,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=specialist_prompt,
            response_mime_type="application/json",
            response_schema=TriageResult,  # ควบคุมโครงสร้างขาออกตาม Pydantic Schema
            temperature=0.0                # ลดความสุ่มเพื่อให้คำตอบมีเสถียรภาพสูงสุด
        )
    )

    # ขั้นตอนที่ 5: นำผลลัพธ์มาตรวจทานและเขียนทับ Priority และ Escalation ด้วย Deterministic SLA Rules
    result = json.loads(response.text)
    priority, escalate = evaluate_sla_and_priority(ticket, domain)
    
    # ประกอบผลลัพธ์สุดท้ายและตรวจสอบความถูกต้องผ่าน Pydantic Model (TriageResult)
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

# ---------------------------------------------------------
# 6. ส่วนประมวลผลแบบอะซิงโครนัส (Async Non-blocking Wrapper)
# ---------------------------------------------------------

async def triage_ticket_async(ticket: TicketInput) -> TriageResult:
    """แปลงการประมวลผลให้เป็นแบบ Non-blocking ผ่าน ThreadPool เพื่อรองรับการทำงานแบบ Batch"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, triage_ticket_with_llm, ticket)