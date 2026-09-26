from __future__ import annotations

import math
import re
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher
from urllib.parse import urlparse

from app.schemas import TransactionContext


URL_RE = re.compile(r"https?://[^\s<>\"']+|\b(?:[a-z0-9-]+\.)+(?:com|in|net|org|xyz|top|click|live|site|online)(?:/[^\s]*)?", re.I)
UPI_RE = re.compile(r"\b[a-zA-Z0-9._-]{2,}@[a-zA-Z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+91[-\s]?)?[6-9]\d{9}(?!\d)")
AMOUNT_RE = re.compile(r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d{1,2})?)", re.I)

KNOWN_BRANDS = {
    "sbi": ["sbi.co.in", "onlinesbi.sbi"],
    "hdfc": ["hdfcbank.com"],
    "icici": ["icicibank.com"],
    "axis": ["axisbank.com"],
    "amazon": ["amazon.in", "amazon.com"],
    "flipkart": ["flipkart.com"],
    "india post": ["indiapost.gov.in"],
}

CATEGORY_RULES = [
    ("utility_scam", ["electricity", "connection", "disconnected", "power bill", "bijli", "बिजली", "कनेक्शन काट"]),
    ("fake_kyc", ["kyc", "pan update", "account blocked", "verify account", "केवाईसी", "khata band", "खाता बंद"]),
    ("bank_impersonation", ["bank", "sbi", "hdfc", "icici", "fraud department"]),
    ("fake_reward", ["winner", "reward", "cashback", "prize", "lottery", "inaam", "इनाम"]),
    ("investment_scam", ["investment", "guaranteed return", "double your", "trading tip"]),
    ("delivery_scam", ["parcel", "delivery", "courier", "shipping fee"]),
    ("job_scam", ["job offer", "work from home", "registration fee", "hr manager"]),
    ("phishing", ["login", "verify", "click link", "credentials", "link kholo", "लिंक खोल"]),
]

TACTIC_RULES = {
    "urgency": ["immediately", "urgent", "today", "now", "within 24", "last chance", "tonight", "turant", "abhi", "तुरंत", "अभी", "आज"],
    "threat": ["blocked", "suspended", "disconnected", "legal action", "penalty", "arrest", "band ho jayega", "बंद", "कानूनी कार्रवाई"],
    "reward": ["winner", "cashback", "prize", "free gift", "bonus", "inaam", "इनाम", "मुफ्त"],
    "impersonation": ["sbi", "bank", "electricity board", "income tax", "police", "customs", "बैंक", "पुलिस", "बिजली विभाग"],
    "secrecy": ["do not tell", "confidential", "keep secret", "kisi ko mat batana", "किसी को मत बताना"],
}


def clamp(value: float) -> float:
    return round(max(0, min(100, value)), 1)


def classify(score: float) -> str:
    if score >= 70:
        return "DANGEROUS"
    if score >= 35:
        return "SUSPICIOUS"
    return "SAFE"


def extract_entities(text: str) -> dict:
    lowered = text.lower()
    urls = [match.rstrip(".,);]") for match in URL_RE.findall(text)]
    amounts = [float(value.replace(",", "")) for value in AMOUNT_RE.findall(text)]
    tactics = [name for name, words in TACTIC_RULES.items() if any(word in lowered for word in words)]
    claimed = []
    organization_aliases = {
        "SBI": [r"\bsbi\b", r"\bstate bank of india\b"],
        "HDFC Bank": [r"\bhdfc(?: bank)?\b"],
        "ICICI Bank": [r"\bicici(?: bank)?\b"],
        "Electricity Board": [r"\belectricity\b", r"\bpower (?:board|department)\b"],
        "India Post": [r"\bindia post\b"],
        "Amazon": [r"\bamazon\b"],
        "Flipkart": [r"\bflipkart\b"],
    }
    for name, patterns in organization_aliases.items():
        if any(re.search(pattern, lowered) for pattern in patterns):
            claimed.append(name)
    return {
        "amounts": amounts,
        "upi_ids": list(dict.fromkeys(UPI_RE.findall(text))),
        "urls": list(dict.fromkeys(urls)),
        "phone_numbers": list(dict.fromkeys(PHONE_RE.findall(text))),
        "claimed_organizations": claimed,
        "tactics": tactics,
    }


def message_analysis(text: str) -> tuple[float, str, list[str], dict]:
    lowered = text.lower()
    entities = extract_entities(text)
    score = 5.0
    reasons: list[str] = []
    for tactic in entities["tactics"]:
        weights = {"urgency": 19, "threat": 21, "reward": 15, "impersonation": 16, "secrecy": 18}
        score += weights[tactic]
        reasons.append(f"Uses {tactic.replace('_', ' ')} language")
    if entities["upi_ids"]:
        score += 12
        reasons.append("Requests payment through a UPI identifier")
    if entities["urls"]:
        score += 8
        reasons.append("Contains a link that should be independently verified")
    if any(word in lowered for word in ["otp", "password", "pin", "cvv"]):
        score += 22
        reasons.append("Requests sensitive authentication information")
    category = "payment_request_scam" if entities["upi_ids"] or entities["amounts"] else "phishing"
    best_hits = 0
    for candidate, words in CATEGORY_RULES:
        hits = sum(word in lowered for word in words)
        if hits > best_hits:
            category, best_hits = candidate, hits
    if not reasons:
        reasons.append("No common scam-pressure patterns detected")
    return clamp(score), category, reasons, entities


def normalize_url(raw: str) -> str:
    return raw if raw.startswith(("http://", "https://")) else f"http://{raw}"


def url_analysis(raw: str) -> tuple[float, list[str], dict]:
    url = normalize_url(raw.strip())
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    score = 0.0
    reasons: list[str] = []
    if parsed.scheme != "https":
        score += 15
        reasons.append("Does not use HTTPS")
    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host):
        score += 32
        reasons.append("Uses an IP address instead of a named domain")
    parts = host.split(".")
    if len(parts) > 4:
        score += 16
        reasons.append("Uses an unusually deep subdomain structure")
    if len(url) > 110:
        score += 14
        reasons.append("URL is unusually long")
    if "xn--" in host:
        score += 28
        reasons.append("Contains a punycode/lookalike domain")
    if parts and parts[-1] in {"xyz", "top", "click", "live", "site", "online", "buzz"}:
        score += 24
        reasons.append(f"Uses the high-risk .{parts[-1]} domain ending")
    if host.count("-") >= 2:
        score += 12
        reasons.append("Domain uses multiple deceptive separators")
    for brand, official in KNOWN_BRANDS.items():
        if brand.replace(" ", "") in host.replace("-", "") and not any(host == domain or host.endswith(f".{domain}") for domain in official):
            score += 32
            reasons.append(f"Looks like {brand.upper()} but is not an official domain")
            break
    if not reasons:
        reasons.append("No high-risk URL structure detected")
    return clamp(score), reasons, {"url": raw, "domain": host, "scheme": parsed.scheme}


def transaction_analysis(context: TransactionContext) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if context.is_new_recipient:
        score += 35
        reasons.append("Recipient has not been paid before")
    if context.amount >= 10_000:
        score += 22
        reasons.append("Amount is high for an unverified payment")
    elif context.amount >= 3_000:
        score += 12
        reasons.append("Payment amount warrants verification")
    if context.transaction_hour <= 5 or context.transaction_hour >= 23:
        score += 18
        reasons.append("Transaction occurs at an unusual hour")
    if context.recent_frequency >= 5:
        score += min(25, 8 + context.recent_frequency * 2)
        reasons.append("Unusual burst of recent transactions")
    if "@" in context.payee and any(token in context.payee.lower() for token in ["help", "refund", "secure", "verify"]):
        score += 15
        reasons.append("Payee identifier uses a social-engineering keyword")
    if not reasons:
        reasons.append("Transaction pattern is consistent with normal activity")
    return clamp(score), reasons


def consistency_analysis(entities: dict, url: str | None, payee: str) -> tuple[float, list[str]]:
    claimed = " ".join(entities.get("claimed_organizations", [])).lower()
    score = 0.0
    reasons: list[str] = []
    if claimed and payee and "@" in payee:
        payee_prefix = payee.split("@", 1)[0].lower()
        org_tokens = [token for token in re.findall(r"[a-z]+", claimed) if len(token) > 3]
        if org_tokens and not any(token in payee_prefix for token in org_tokens):
            score += 72
            reasons.append("Claimed organization does not match the payment recipient")
    if claimed and url:
        host = urlparse(normalize_url(url)).hostname or ""
        normalized_host = host.replace("-", "")
        org_tokens = [token for token in re.findall(r"[a-z]+", claimed) if len(token) > 3]
        if org_tokens and not any(SequenceMatcher(None, token, normalized_host).ratio() > 0.6 for token in org_tokens):
            score += 22
            reasons.append("Website domain does not clearly belong to the claimed organization")
    return clamp(score), reasons


def community_risk(entities: dict) -> tuple[float, list[str]]:
    # Real community matches are applied asynchronously from ThreatIndicator
    # records in the analysis pipeline. No identifiers are hard-coded here.
    return 0.0, []


def score_components(scores: dict[str, float]) -> float:
    final_score = clamp(
        0.25 * scores.get("message_risk", 0)
        + 0.20 * scores.get("url_risk", 0)
        + 0.20 * scores.get("transaction_risk", 0)
        + 0.15 * scores.get("community_risk", 0)
        + 0.20 * scores.get("consistency_risk", 0)
    )
    if scores.get("message_risk", 0) >= 75 and max(
        scores.get("url_risk", 0),
        scores.get("consistency_risk", 0),
        scores.get("community_risk", 0),
    ) >= 60:
        return max(final_score, 82.0)
    return final_score


def full_analysis(text: str, explicit_url: str | None = None, transaction: TransactionContext | None = None) -> dict:
    message_score, category, message_reasons, entities = message_analysis(text)
    url = explicit_url or (entities["urls"][0] if entities["urls"] else None)
    url_score, url_reasons, url_entities = url_analysis(url) if url else (0.0, [], {})
    tx = transaction or TransactionContext(
        amount=entities["amounts"][0] if entities["amounts"] else 0,
        payee=entities["upi_ids"][0] if entities["upi_ids"] else "",
        is_new_recipient=bool(entities["upi_ids"]),
        transaction_hour=datetime.now().hour,
        recent_frequency=0,
    )
    tx_score, tx_reasons = transaction_analysis(tx)
    community_score, community_reasons = community_risk(entities)
    consistency_score, consistency_reasons = consistency_analysis(entities, url, tx.payee)
    scores = {
        "message_risk": message_score,
        "url_risk": url_score,
        "transaction_risk": tx_score,
        "community_risk": community_score,
        "consistency_risk": consistency_score,
    }
    final_score = score_components(scores)
    classification = classify(final_score)
    recommendations = {
        "SAFE": "Confirm the recipient and purpose, then proceed only if you recognize the request.",
        "SUSPICIOUS": "Pause the payment and verify the request through an official channel you find independently.",
        "DANGEROUS": "Do not pay or open the link. Block the sender, preserve the evidence, and report the indicators.",
    }
    all_entities = {**entities, **url_entities, "payee": tx.payee or None}
    reasons = list(dict.fromkeys(message_reasons + url_reasons + tx_reasons + community_reasons + consistency_reasons))
    return {
        "id": str(uuid.uuid4()),
        "score": final_score,
        "classification": classification,
        "category": category,
        "reasons": reasons[:8],
        "entities": all_entities,
        "component_scores": scores,
        "recommended_action": recommendations[classification],
        "created_at": datetime.now(timezone.utc),
    }
