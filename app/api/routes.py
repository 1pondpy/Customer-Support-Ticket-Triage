from fastapi import APIRouter, Query
from app.schemas.ticket import TicketInput
from app.schemas.triage import TriageResult, BatchTicketInput, BatchTriageResult
from app.services.triage_service import triage_ticket_with_llm
from app.services.rag_service import RAGService

router = APIRouter()

@router.post("/tickets/triage", response_model=TriageResult)
def triage(ticket: TicketInput):
    return triage_ticket_with_llm(ticket)

@router.post("/tickets/triage/batch", response_model=BatchTriageResult)
def triage_batch(batch_input: BatchTicketInput):
    # วนลูปประมวลผลตั๋วทีละใบ (Baseline ก่อนทำ Async ใน Step ถัดไป)
    results = [triage_ticket_with_llm(ticket) for ticket in batch_input.tickets]
    return BatchTriageResult(
        total_processed=len(results),
        results=results
    )

@router.get("/policies/search")
def search_policies(query: str = Query(..., description="คำสำคัญที่ต้องการทดสอบค้นหาในคลังนโยบาย")):
    rag = RAGService(policy_dir="data/policies")
    results = rag.search_policies(query)
    return {
        "query": query,
        "results_found": len(results),
        "results": results
    }

@router.post("/evaluate")
def evaluate_routing():
    pass