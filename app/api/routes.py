from fastapi import APIRouter, Query
from app.schemas.ticket import TicketInput
from app.schemas.triage import TriageResult
from app.services.triage_service import get_mock_triage 
# 🌟 Import RAGService ที่เราเพิ่งเขียนเพิ่มเข้ามา
from app.services.rag_service import RAGService 

router = APIRouter()

@router.post("/tickets/triage", response_model=TriageResult)
def triage(ticket: TicketInput):
    return get_mock_triage()

@router.post("/tickets/triage/batch")
def triage_batch():
    pass

# 🌟 แก้ไขฟังก์ชันนี้เพื่อดึงระบบค้นหา RAG มาทำงานจริง
@router.get("/policies/search")
def search_policies(query: str = Query(..., description="คำสำคัญที่ต้องการทดสอบค้นหาในคลังนโยบาย")):
    # กำหนด Path เป็น "data/policies" เพราะเวลา uvicorn รัน 
    # มันจะมอง Root Directory ข้างนอกสุดเป็นหลัก (ไม่ใช่ในโฟลเดอร์ app หรือ services)
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