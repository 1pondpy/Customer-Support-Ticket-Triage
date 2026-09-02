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
    policy_citations: list[str] ## รายการของข้อความที่ใช้เก็บชื่อไฟล์นโยบาย ที่โมเดลใช้อ้างอิงจริงในการตัดสินใจคัดแยกตั๋วใบนั้น , เป็น Grounding Check บังคับให้ LLM ดึงข้อเท็จจริงมาจากไฟล์
    confidence: float 
    escalate: bool ## เคสด่วน/วิกฤต , True False
    
class BatchTicketInput(BaseModel): ## ## เรียกฟังก์ชั่น BaseModel ให้ควบคุม Formatม ส่งตั๋วหลายใบใน Request เดียวได้ โดยส่งก้อน JSON ที่มีคีย์ tickets ครอบ Array ของอ็อบเจกต์ตั๋ว { "tickets": [ {...} , {...}  ] }
    tickets: List[TicketInput] = Field(..., description="รายการตั๋วสนับสนุนลูกค้าที่ต้องการประมวลผลพร้อมกัน")

class BatchTriageResult(BaseModel): ## ควบคุมรูปแบบ JSON ขากลับหลังจากระบบประมวลผลตั๋วทุกใบเสร็จสิ้น
    total_processed: int = Field(..., description="จำนวนตั๋วที่ประมวลผลทั้งหมด")
    results: List[TriageResult] = Field(..., description="รายการผลลัพธ์การคัดแยกตั๋ว")