from app.schemas.triage import TriageResult

def get_mock_triage() -> TriageResult:
    return TriageResult(
        category="billing",
        sub_intent="double_charge",
        priority="P2",
        assigned_queue="billing_default_queue",
        suggested_macro_id="macro_billing_refund_check",
        internal_notes="Mocked: Processed via Triage Service layer.",
        policy_citations=["SLA-BILLING-V1", "REFUND-POLICY-SEC3"],
        confidence=0.95,
        escalate=False
    )