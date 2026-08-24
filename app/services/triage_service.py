import json
import os
from pathlib import Path
from google import genai
from google.genai import types

from app.schemas.ticket import TicketInput
from app.schemas.triage import TriageResult
from app.services.rag_service import RAGService
from app.config import settings

# 1. Initialize RAG Service
rag_service = RAGService(policy_dir="data/policies")

def get_client() -> genai.Client:
    # ตรวจสอบทั้ง GEMINI_API_KEY และ GOOGLE_API_KEY ป้องกันชื่อไม่ตรงใน .env
    api_key = settings.GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API Key not found. Please set GEMINI_API_KEY or GOOGLE_API_KEY in your .env file.")
    return genai.Client(api_key=api_key)

def triage_ticket_with_llm(ticket: TicketInput) -> TriageResult:
    # Step 1: ค้นหา Policy ผ่าน RAG
    search_query = f"{ticket.subject} {ticket.body}"
    try:
        retrieved_chunks = rag_service.search_policies(query=search_query, top_k=3)
        context_text = "\n\n".join([f"[{chunk['source']}]\n{chunk['text']}" for chunk in retrieved_chunks])
    except Exception:
        context_text = "Standard routing and SLA policies apply."

    # Step 2: โหลด Prompt Template อย่างปลอดภัย
    prompt_file = Path("data/prompt_template.txt")
    if prompt_file.exists():
        system_prompt = prompt_file.read_text(encoding="utf-8")
    else:
        system_prompt = "You are an expert AI customer support triage agent. Classify tickets into structured JSON matching the schema."

    # Step 3: ประกอบ Payload
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

    # Step 4: เรียก Gemini API
    client = get_client()
    model_name = settings.MODEL_NAME or os.getenv("MODEL_NAME") or "gemini-3.6-flash"

    response = client.models.generate_content(
        model=model_name,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=TriageResult,
            temperature=0.0
        )
    )

    # Step 5: แปลงและ Validate เข้า Pydantic Model
    return TriageResult.model_validate_json(response.text)