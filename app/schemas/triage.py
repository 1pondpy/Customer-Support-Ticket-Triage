from typing import Literal, List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.ticket import TicketInput

# กำหนด 8 หมวดหมู่ตาม PRD ขอบเขต In-Scope
TicketCategory = Literal[
    "billing",
    "technical",
    "refund",
    "account",
    "shipping",
    "feedback",
    "security",
    "other"
]

TicketPriority = Literal["P1", "P2", "P3", "P4"]

class TriageResult(BaseModel):
    category: TicketCategory = Field(..., description="หมวดหมู่หลัก 1 ใน 8 หมวด")
    sub_intent: str = Field(..., description="เจตนาย่อยที่สกัดได้จากตั๋ว")
    priority: TicketPriority = Field(..., description="ระดับความสำคัญ P1-P4")
    assigned_queue: str = Field(..., description="ชื่อคิวงานเฉพาะทางที่ต้องส่งต่อ")
    industry: Optional[str] = Field(default=None, description="ประเภทอุตสาหกรรมของบริการ")
    suggested_macro_id: Optional[str] = Field(default=None, description="รหัสเทมเพลตสำหรับตอบกลับที่แนะนำ")
    internal_notes: str = Field(..., description="บันทึกและเหตุผลภายในสำหรับทีมซัพพอร์ต")
    policy_citations: List[str] = Field(..., description="รายชื่อไฟล์นโยบายที่ใช้อ้างอิงจริง")
    confidence: float = Field(..., ge=0.0, le=1.0, description="คะแนนความเชื่อมั่น (0.0 - 1.0)")
    escalate: bool = Field(..., description="แฟล็กแจ้งเตือนเคสด่วนฉุกเฉิน")

# รองรับ Batch Processing API (POST /tickets/triage/batch)
class BatchTicketInput(BaseModel):
    tickets: List[TicketInput] = Field(..., description="รายการตั๋วที่ส่งเข้ามาประมวลผลพร้อมกัน")

class BatchTriageResult(BaseModel):
    total_processed: int = Field(..., description="จำนวนตั๋วทั้งหมดที่ประมวลผล")
    results: List[TriageResult] = Field(..., description="รายการผลลัพธ์การคัดแยก")

# รองรับ Evaluation API (POST /evaluate) ตาม PRD API Contract
class EvaluateRequest(BaseModel):
    dataset_path: Optional[str] = Field(
        default="data/gold_dataset.json", 
        description="ที่อยู่ไฟล์ชุดทดสอบ Gold Dataset"
    )

class EvaluateMetrics(BaseModel):
    total_evaluated: int
    category_accuracy: float
    priority_accuracy_exact: float
    priority_accuracy_one_level: float
    escalation_recall: float
    average_latency_seconds: float
    pass_threshold_met: bool
    confusion_matrix: Optional[Dict[str, Dict[str, int]]] = None