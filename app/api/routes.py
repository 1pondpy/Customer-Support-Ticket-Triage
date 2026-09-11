import asyncio
from fastapi import APIRouter, Query
from app.schemas.ticket import TicketInput
from app.schemas.triage import TriageResult, BatchTicketInput, BatchTriageResult
from app.services.triage_service import triage_ticket_with_llm, triage_ticket_async
from app.services.rag_service import RAGService

router = APIRouter()

@router.post("/tickets/triage", response_model=TriageResult)
def triage(ticket: TicketInput):
    """
    Single Ticket Triage Endpoint:
    รับข้อมูลตั๋วปัญหา 1 ใบ เพื่อผ่าน Intent Router, RAG Retrieval, 
    Specialist Agent Reasoning และ Deterministic SLA Priority Scorer
    """
    return triage_ticket_with_llm(ticket)

@router.post("/tickets/triage/batch", response_model=BatchTriageResult)
async def triage_batch(batch_input: BatchTicketInput):
    """
    Asynchronous Parallel Batch Triage Endpoint:
    รับตั๋วหลายใบพร้อมกันเป็น Array และกระจายงานด้วย asyncio.gather
    เพื่อประมวลผลพร้อมกันแบบ Concurrency (Non-blocking)
    """
    tasks = [triage_ticket_async(ticket) for ticket in batch_input.tickets]
    results = await asyncio.gather(*tasks)
    return BatchTriageResult(
        total_processed=len(results),
        results=list(results)
    )

@router.get("/policies/search")
def search_policies(query: str = Query(..., description="คำสำคัญที่ต้องการทดสอบค้นหาในคลังนโยบาย")):
    """
    RAG Debug Endpoint:
    ทดสอบการสืบค้นชิ้นส่วนนโยบาย (Chunks) จากโฟลเดอร์ data/policies/ 
    เพื่อตรวจสอบการทำงานของ Knowledge Base ก่อนส่งต่อให้ AI
    """
    rag = RAGService(policy_dir="data/policies")
    results = rag.search_policies(query)
    return {
        "query": query,
        "results_found": len(results),
        "results": results
    }