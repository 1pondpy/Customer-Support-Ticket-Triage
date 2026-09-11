from typing import Literal, Dict, Any, Optional
from pydantic import BaseModel, Field

CustomerTier = Literal["free", "pro", "enterprise"]

class TicketInput(BaseModel):
    subject: str = Field(..., description="หัวข้อหรือสรุปปัญหาของตั๋ว")
    body: str = Field(..., description="เนื้อหารายละเอียดของตั๋วจากลูกค้า")
    customer_tier: Optional[CustomerTier] = Field(
        default=None, 
        description="ระดับสิทธิ์ลูกค้า: free, pro, หรือ enterprise"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="ข้อมูลบริบทเสริม เช่น device, browser, tweet_id"
    )