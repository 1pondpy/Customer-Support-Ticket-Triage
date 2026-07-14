from pydantic import BaseModel

class TicketRequest(BaseModel):
    subject: str
    description: str