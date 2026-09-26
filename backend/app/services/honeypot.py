from __future__ import annotations

from app.services.analyzer import extract_entities


STATES = [
    "INITIAL_CONTACT",
    "BUILD_TRUST",
    "DELAY_PAYMENT",
    "COLLECT_PAYMENT_IDENTIFIER",
    "COLLECT_URL",
    "COLLECT_ALTERNATIVE_CONTACT",
    "IDENTIFY_SCAM_SCRIPT",
    "COMPLETE",
]


def merge_intelligence(current: dict, message: str) -> dict:
    extracted = extract_entities(message)
    merged = {key: list(value) if isinstance(value, list) else value for key, value in current.items()}
    for key in ["upi_ids", "urls", "phone_numbers", "amounts", "claimed_organizations", "tactics"]:
        merged[key] = list(dict.fromkeys([*merged.get(key, []), *extracted.get(key, [])]))
    return merged


def next_response(state: str, message: str, intelligence: dict) -> tuple[str, str]:
    idx = min(STATES.index(state) if state in STATES else 0, len(STATES) - 1)
    if intelligence.get("upi_ids") and state in STATES[:4]:
        idx = 4
    elif intelligence.get("urls") and idx < 5:
        idx = 5
    else:
        idx = min(idx + 1, len(STATES) - 1)
    next_state = STATES[idx]
    prompts = {
        "BUILD_TRUST": "I understand. I am trying to arrange the payment now—what is this charge for exactly?",
        "DELAY_PAYMENT": "My banking app is taking a while to load. Please give me a minute.",
        "COLLECT_PAYMENT_IDENTIFIER": "The QR is not opening on my phone. Can you send the UPI ID in text?",
        "COLLECT_URL": "I still cannot see the bill. Can you send the exact payment or verification link?",
        "COLLECT_ALTERNATIVE_CONTACT": "If the link fails again, what number should I call you back on?",
        "IDENTIFY_SCAM_SCRIPT": "Which organization and department are you calling from, and what reference number should I quote?",
        "COMPLETE": "Thank you. I have enough details and will verify them through the organization’s official channel.",
    }
    return next_state, prompts.get(next_state, prompts["BUILD_TRUST"])

