from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import TransactionContext
from app.services.analyzer import classify, clamp, full_analysis, score_components
from app.services.gemini import assess_with_gemini
from app.services.intelligence import community_indicator_risk
from app.services.ml_classifier import get_classifier
from app.services.url_intelligence import inspect_url


async def analyze_pipeline(
    text: str,
    explicit_url: str | None = None,
    transaction: TransactionContext | None = None,
    db: AsyncSession | None = None,
) -> dict:
    result = full_analysis(text, explicit_url, transaction)
    if db:
        community_score, community_reasons, community_matches = await community_indicator_risk(db, result["entities"])
        result["component_scores"]["community_risk"] = community_score
        if community_matches:
            result["entities"]["community_matches"] = [
                f"{item['type']}: {item['value']} ({item['report_count']} report{'s' if item['report_count'] != 1 else ''})"
                for item in community_matches
            ]
        result["reasons"] = list(dict.fromkeys(result["reasons"] + community_reasons))

    url = explicit_url or next(iter(result["entities"].get("urls", [])), None)
    if url:
        external = await inspect_url(url)
        external_score = float(external.get("external_risk_score", 0))
        result["component_scores"]["external_url_risk"] = external_score
        result["component_scores"]["url_risk"] = max(result["component_scores"].get("url_risk", 0), external_score)
        for field in ("domain_age_days", "domain_registered_at", "reputation"):
            if external.get(field) is not None:
                result["entities"][field] = external[field]
        result["entities"]["reputation_sources"] = [
            f"{name.replace('_', ' ')}: {details['status']}"
            for name, details in external.get("reputation_sources", {}).items()
        ]
        result["reasons"] = list(dict.fromkeys(result["reasons"] + external.get("reasons", [])))

    result["score"] = score_components(result["component_scores"])
    result["classification"] = classify(result["score"])
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
