from typing import Literal
from pydantic import BaseModel

class TicketInput(BaseModel):
    subject: str
    body: str
    customer_tier: Literal["free", "pro", "enterprise"] | None  ## Literal คือการล็อกค่าตายตัวตามที่กำหนดเท่านั้น
    metadata: dict[str, str] | None                             ## dict คือโครงสร้างคู่คีย์-ค่า (Key-Value Pairs) เช่น {"device": "iPhone 15"}
                                                                ## | None คือการระบุว่า "ฟิลด์นี้อนุญาตให้มีค่าว่าง (Null) ได้