from typing import Literal
from pydantic import BaseModel

class TicketInput(BaseModel):
    subject: str
    body: str
    customer_tier: Literal["free", "pro", "enterprise"] | None
    metadata: dict[str, str] | None