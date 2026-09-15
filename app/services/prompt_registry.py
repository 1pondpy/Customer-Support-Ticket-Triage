"""
Prompt Versioning Registry for Multi-Agent MoE Triage System.
Complies with Iteration 3 v1.0.0 requirements.
"""

from typing import Dict, Any

PROMPT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "v1.0.0": {
        "release_date": "2026-03-30",
        "description": "Multi-Agent Mixture-of-Experts System Prompts with Deterministic Grounding",
        "prompts": {
            "router": (
                "You are an Intent Router Agent. Classify the customer support ticket into exactly "
                "one of the 8 canonical domains: technical, billing, refund, account, shipping, "
                "security, feedback, other. Avoid hallucinating queues."
            ),
            "technical": (
                "You are a Technical Support Specialist. Analyze application bugs, crashes, 500 error codes, "
                "and service outage alerts. Route to tech_support_queue."
            ),
            "billing": (
                "You are a Billing Specialist. Review subscription plans, double charges, and invoice errors. "
                "Route to billing_default_queue."
            ),
            "refund": (
                "You are a Refund Specialist. Inspect eligibility for money back and subscription charge cancellations. "
                "Route to refund_expert_queue."
            ),
            "account": (
                "You are an Account Specialist. Handle 2FA/OTP failures, password resets, and account access locks. "
                "Route to account_security_queue."
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
    """
    Retrieve versioned system prompt by agent role.
    """
    ver_data = PROMPT_REGISTRY.get(version)
    if not ver_data:
        ver_data = PROMPT_REGISTRY[CURRENT_PROMPT_VERSION]
    
    return ver_data["prompts"].get(
        role, 
        "You are a helpful customer support triage assistant."
    )

def list_prompt_versions() -> Dict[str, Any]:
    """
    Return all registered prompt versions and their metadata.
    """
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