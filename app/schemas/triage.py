from pydantic import BaseModel
from typing import Literal

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