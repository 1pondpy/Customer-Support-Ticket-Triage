"""
Security Guardrails Module:
- Untrusted Input Sanitization & Prompt Injection Mitigation
- PII Redaction for Secure Logging (No PII in logs beyond ticket ID)
"""

import re
import logging
from typing import Tuple, Dict, Any

# Logging Configuration strictly forbidding PII leakage
logger = logging.getLogger("triage_security")
logger.setLevel(logging.INFO)

# High-risk Prompt Injection Heuristic Patterns
INJECTION_SIGNATURES = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(all\s+)?prior\s+prompts",
    r"system\s*override",
    r"you\s+are\s+now\s+dan",
    r"assign\s+(me\s+)?p1",
    r"force\s+escalat(e|ion)",
    r"bypass\s+policy",
    r"override\s+sla"
]

# PII Regex Matchers
PII_PATTERNS = {
    "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b",
    "phone_th": r"\b(?:\+66|0)[689]\d{8}\b",
    "ssn_or_id": r"\b\d{3}-\d{2}-\d{4}\b"
}

def sanitize_untrusted_input(text: str) -> Tuple[str, bool, str]:
    """
    Scans untrusted ticket input for adversarial injection payloads.
    Returns: (cleaned_text, is_safe, detected_threat)
    """
    for pattern in INJECTION_SIGNATURES:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            threat = match.group(0)
            return text, False, f"Prompt injection pattern detected: '{threat}'"
            
    return text, True, "OK"

def redact_pii_for_logging(raw_text: str) -> str:
    """
    Redacts sensitive personal identifiable information before writing to logs.
    """
    redacted = raw_text
    redacted = re.sub(PII_PATTERNS["credit_card"], "[REDACTED_CARD]", redacted)
    redacted = re.sub(PII_PATTERNS["email"], "[REDACTED_EMAIL]", redacted)
    redacted = re.sub(PII_PATTERNS["phone_th"], "[REDACTED_PHONE]", redacted)
    redacted = re.sub(PII_PATTERNS["ssn_or_id"], "[REDACTED_ID]", redacted)
    return redacted

def secure_audit_log(ticket_id: str, action: str, details: Dict[str, Any]):
    """
    Safe audit logger strictly adhering to: 'No PII in logs beyond ticket ID'.
    """
    safe_details = {
        k: redact_pii_for_logging(str(v)) if isinstance(v, str) else v
        for k, v in details.items()
    }
    logger.info(f"[AUDIT] TicketID={ticket_id} | Action={action} | Context={safe_details}")