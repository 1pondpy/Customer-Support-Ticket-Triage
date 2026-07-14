from fastapi import APIRouter
from app.schemas.ticket import TicketInput
from app.schemas.triage import TriageResult
from app.services.triage_service import get_mock_triage 

router = APIRouter()

@router.post("/tickets/triage", response_model=TriageResult)

def triage(ticket: TicketInput):
    return get_mock_triage()

@router.post("/tickets/triage/batch")
def triage_batch():
    pass

@router.get("/policies/search")
def search_policies():
    pass

@router.post("/evaluate")
def evaluate_routing():
    pass