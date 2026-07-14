from pydantic import BaseModel

class TriageResponse(BaseModel):
    category: str
    priority: str
    reply: str