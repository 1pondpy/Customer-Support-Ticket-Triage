"""
Prompt Versioning Registry for Multi-Agent Mixture-of-Experts (MoE) Architecture.
Adheres to Iteration 3 v1.0.0 deliverable requirements.
"""

from typing import Dict, Any

PROMPT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "v0.1.0": {
        "release_date": "2026-02-10",
        "description": "Walking skeleton baseline mock prompts.",
        "prompts": {
            "router": "Mock router prompt"
        }
    },
    "v0.2.0": {
        "release_date": "2026-03-01",
        "description": "Single-agent delimiter-enforced prompt with RAG grounding.",
        "prompts": {
            "router": "You are a customer support triage agent. Categorize the ticket and ground using policy context."
        }
    },
    "v1.0.0": {
        "release_date": "2026-03-30",
        "description": "Production Multi-Agent MoE prompts with strict guardrails and deterministic grounding.",
        "prompts": {
            "router": (
                "You are an Intent Router Agent. Classify the customer support ticket into exactly "
                "one of the canonical categories: technical, billing, refund, account, shipping, "
                "security, feedback, other. Avoid hallucinating queues."
            ),
            "technical": (
                "You are a Technical Support Specialist. Analyze application bugs, crashes, 500 errors, "
                "and service outage alerts. Route to tech_support_queue."
            ),
            "billing": (
                "You are a Billing Specialist. Review subscription plans, double charges, and invoice errors. "
                "Route to billing_default_queue."
            ),
            "refund": (
                "You are a Refund Specialist. Inspect eligibility for money back and charge cancellations. "
                "Route to refund_expert_queue."
            ),
            "account": (
                "You are an Account Specialist. Handle 2FA/OTP failures, password resets, and account access locks. "
                "Route to account_security_queue."
            ),
            "shipping": (
                "You are a Shipping & Logistics Specialist. Analyze parcel tracking, courier delays, and shipment issues. "
                "Route to shipping_logistics_queue."
            ),
            "security": (
                "You are a Cybersecurity Incident Specialist. Analyze data compromises, unauthorized logins, and threat alerts. "
                "Route to security_incident_queue."
            ),
            "feedback": (
                "You are a Customer Experience Feedback Agent. Analyze UX improvements, feature requests, and compliments. "
                "Route to customer_feedback_queue."
            ),
            "other": (
                "You are a General Care Triage Agent. Handle standard queries that do not belong to specialized queues. "
                "Route to general_triage_queue."
            ),
            "judge": (
                "You are a Grounding Judge Agent. Verify that every citation in policy_citations corresponds "
                "strictly to retrieved policy documentation. Do not invent rules or SLAs."
            )
        }
    }
}

CURRENT_PROMPT_VERSION = "v1.0.0"

def get_system_prompt(role: str, version: str = CURRENT_PROMPT_VERSION) -> str:
    """Retrieve versioned system prompt by role and target semantic version."""
    ver_data = PROMPT_REGISTRY.get(version, PROMPT_REGISTRY[CURRENT_PROMPT_VERSION])
    return ver_data["prompts"].get(role, "You are a helpful customer support triage assistant.")

def list_prompt_versions() -> Dict[str, Any]:
    """Inspect all prompt versions, release notes, and supported roles."""
    return {
        "current_active_version": CURRENT_PROMPT_VERSION,
        "versions": {
            k: {
                "release_date": v["release_date"],
                "description": v["description"],
                "roles_registered": list(v["prompts"].keys())
            }
            for k, v in PROMPT_REGISTRY.items()
        }
    }