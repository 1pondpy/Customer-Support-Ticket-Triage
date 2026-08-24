from fastapi import APIRouter, Query
from app.schemas.ticket import TicketInput
from app.schemas.triage import TriageResult
from app.services.triage_service import triage_ticket_with_llm
from app.services.rag_service import RAGService 

router = APIRouter()

@router.post("/tickets/triage", response_model=TriageResult)
def triage(ticket: TicketInput):
    # สลับจาก Mock เป็นการประมวลผลผ่าน LLM จริง + RAG Context
    return triage_ticket_with_llm(ticket)

@router.post("/tickets/triage/batch")
def triage_batch():
    pass

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