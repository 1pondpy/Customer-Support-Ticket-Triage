from fastapi import APIRouter
from app.schemas.ticket import TicketRequest
from app.services.triage_service import triage_ticket

router = APIRouter()

@router.post("/triage")
def triage(request: TicketRequest):
    return triage_ticket()