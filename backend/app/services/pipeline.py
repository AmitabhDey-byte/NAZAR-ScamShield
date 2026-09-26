from __future__ import annotations

from app.schemas import TransactionContext
from app.services.analyzer import classify, clamp, full_analysis
from app.services.gemini import assess_with_gemini
from app.services.ml_classifier import get_classifier


async def analyze_pipeline(
    text: str,
    explicit_url: str | None = None,
    transaction: TransactionContext | None = None,
) -> dict:
    result = full_analysis(text, explicit_url, transaction)
    ml = get_classifier().predict(text)
    ml_score = round(ml["scam_probability"] * 100, 1)
    result["component_scores"]["ml_probability"] = ml_score

    ai = await assess_with_gemini(text)
    signals = [result["score"], ml_score]
    weights = [0.78, 0.22]
    if ai and ai["confidence"] >= 0.35:
        result["component_scores"]["gemini_risk"] = round(float(ai["risk_score"]), 1)
        signals = [result["score"], ml_score, float(ai["risk_score"])]
        weights = [0.62, 0.18, 0.20]
        if result["category"] in {"phishing", "payment_request_scam"} and ai["confidence"] >= 0.7:
            result["category"] = ai["category"]
        result["reasons"] = list(dict.fromkeys(result["reasons"] + ai["reasons"]))[:10]
        result["recommended_action"] = ai["recommended_action"] or result["recommended_action"]
        for key in ("claimed_organizations", "tactics"):
            result["entities"][key] = list(dict.fromkeys(result["entities"].get(key, []) + ai.get(key, [])))
        result["ai_provider"] = ai["provider"]
        result["ai_model"] = ai["model"]
        result["ai_summary"] = ai["summary"]
        result["ai_confidence"] = round(float(ai["confidence"]), 3)
    else:
        result["ai_provider"] = None
        result["ai_model"] = None
        result["ai_summary"] = None
        result["ai_confidence"] = None

    combined = clamp(sum(score * weight for score, weight in zip(signals, weights, strict=True)))
    result["score"] = max(result["score"], combined) if result["score"] >= 70 else combined
    result["classification"] = classify(result["score"])
    return result
