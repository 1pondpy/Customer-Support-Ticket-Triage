from app.schemas.triage import TriageResponse

def triage_ticket():
    return TriageResponse(
        category="Account",
        priority="High",
        reply="Please reset your password."
    )
