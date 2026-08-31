from pydantic import BaseModel, Field
from typing import Literal, List
from app.schemas.ticket import TicketInput

class TriageResult(BaseModel):
    category: str
    sub_intent: str
    priority: Literal["P1", "P2", "P3", "P4"]
    assigned_queue: str
    suggested_macro_id: str | None
    internal_notes: str
    policy_citations: list[str]
    confidence: float
    escalate: bool
    
class BatchTicketInput(BaseModel):
    tickets: List[TicketInput] = Field(..., description="รายการตั๋วสนับสนุนลูกค้าที่ต้องการประมวลผลพร้อมกัน")

class BatchTriageResult(BaseModel):
    total_processed: int = Field(..., description="จำนวนตั๋วที่ประมวลผลทั้งหมด")
    results: List[TriageResult] = Field(..., description="รายการผลลัพธ์การคัดแยกตั๋ว")