from __future__ import annotations

import asyncio
import hashlib
import time
from datetime import datetime, timezone
from urllib.parse import quote, urlparse

import httpx

from app.core.config import settings
from app.services.analyzer import normalize_url


IANA_RDAP_BOOTSTRAP = "https://data.iana.org/rdap/dns.json"
SAFE_BROWSING_SEARCH = "https://safebrowsing.googleapis.com/v5/urls:search"
URLHAUS_LOOKUP = "https://urlhaus-api.abuse.ch/v1/url/"

_bootstrap_cache: tuple[float, dict] | None = None
_result_cache: dict[str, tuple[float, dict]] = {}


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _registration_date(payload: dict) -> datetime | None:
    for event in payload.get("events", []):
        if str(event.get("eventAction", "")).lower() in {"registration", "registered"}:
            parsed = _parse_time(event.get("eventDate"))
            if parsed:
                return parsed
    return None


def score_url_intelligence(domain_age_days: int | None, reputation_hits: list[str]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if domain_age_days is not None:
        if domain_age_days <= 7:
            score = 48.0
            reasons.append(f"Domain was registered only {domain_age_days} day(s) ago")
        elif domain_age_days <= 30:
            score = 38.0
            reasons.append(f"Domain is only {domain_age_days} days old")
        elif domain_age_days <= 90:
            score = 24.0
            reasons.append(f"Domain is relatively new ({domain_age_days} days old)")
        elif domain_age_days <= 365:
            score = 10.0
            reasons.append("Domain is less than one year old")
    if reputation_hits:
        score = 100.0
        reasons.append(f"Known threat match from {', '.join(reputation_hits)}")
    return score, reasons


async def _rdap_bootstrap(client: httpx.AsyncClient) -> dict:
    global _bootstrap_cache
    now = time.monotonic()
    if _bootstrap_cache and _bootstrap_cache[0] > now:
        return _bootstrap_cache[1]
    response = await client.get(IANA_RDAP_BOOTSTRAP)
    response.raise_for_status()
    payload = response.json()
    _bootstrap_cache = (now + 86_400, payload)
    return payload


async def _domain_age(client: httpx.AsyncClient, domain: str) -> tuple[int | None, str | None, str]:
    try:
        bootstrap = await _rdap_bootstrap(client)
        tld = domain.rsplit(".", 1)[-1].lower()
        base_url = next(
            urls[0]
            for tlds, urls in bootstrap.get("services", [])
            if tld in {str(item).lower() for item in tlds} and urls
        )
        response = None
        labels = domain.split(".")
        for offset in range(max(1, len(labels) - 1)):
            candidate = ".".join(labels[offset:])
            current = await client.get(f"{base_url.rstrip('/')}/domain/{quote(candidate, safe='')}")
            if current.status_code == 404:
                continue
            current.raise_for_status()
            response = current
            break
        if response is None:
            return None, None, "not-found"
        registered = _registration_date(response.json())
        if not registered:
            return None, None, "no-registration-date"
        age = max(0, (datetime.now(timezone.utc) - registered.astimezone(timezone.utc)).days)
        return age, registered.isoformat(), "checked"
    except (httpx.HTTPError, StopIteration, TypeError, ValueError):
        return None, None, "unavailable"


async def _safe_browsing(client: httpx.AsyncClient, url: str) -> tuple[str, list[str]]:
    if not settings.google_safe_browsing_api_key:
        return "not-configured", []
    try:
        response = await client.get(
            SAFE_BROWSING_SEARCH,
            params={"urls": url},
            headers={"X-Goog-Api-Key": settings.google_safe_browsing_api_key},
        )
        response.raise_for_status()
        threats = response.json().get("threats", [])
        types = sorted({str(item) for threat in threats for item in threat.get("threatTypes", [])})
        return ("match", types) if threats else ("no-match", [])
    except (httpx.HTTPError, TypeError, ValueError):
        return "unavailable", []


async def _urlhaus(client: httpx.AsyncClient, url: str) -> tuple[str, list[str]]:
    if not settings.urlhaus_auth_key:
        return "not-configured", []
    try:
        response = await client.post(
            URLHAUS_LOOKUP,
            data={"url": url},
            headers={"Auth-Key": settings.urlhaus_auth_key},
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("query_status") == "ok":
            details = [str(payload.get("threat") or "malware URL")]
            details += [str(tag) for tag in payload.get("tags") or []]
            return "match", list(dict.fromkeys(details))
        return "no-match", []
    except (httpx.HTTPError, TypeError, ValueError):
        return "unavailable", []


async def inspect_url(raw_url: str) -> dict:
    """Check registration age and optional threat feeds without visiting the target URL."""
    normalized = normalize_url(raw_url.strip())
    parsed = urlparse(normalized)
    host = (parsed.hostname or "").strip(".").lower()
    try:
        domain = host.encode("idna").decode("ascii")
    except UnicodeError:
        domain = ""
    if not settings.url_intelligence_enabled or not domain or "." not in domain:
        return {"status": "not-checked", "external_risk_score": 0.0, "reasons": []}

    cache_key = hashlib.sha256(normalized.encode()).hexdigest()
    cached = _result_cache.get(cache_key)
    if cached and cached[0] > time.monotonic():
        return cached[1]

    timeout = httpx.Timeout(settings.url_intelligence_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        age_result, safe_result, urlhaus_result = await asyncio.gather(
            _domain_age(client, domain),
            _safe_browsing(client, normalized),
            _urlhaus(client, normalized),
        )

    age_days, registered_at, rdap_status = age_result
    safe_status, safe_details = safe_result
    urlhaus_status, urlhaus_details = urlhaus_result
    hits = []
    if safe_status == "match":
        hits.append("Google Safe Browsing")
    if urlhaus_status == "match":
        hits.append("URLhaus")
    score, reasons = score_url_intelligence(age_days, hits)
    configured_checks = [status for status in (safe_status, urlhaus_status) if status != "not-configured"]
    reputation = "known-malicious" if hits else "no-known-match" if any(status == "no-match" for status in configured_checks) else "not-checked"
    reputation_checked = any(status in {"match", "no-match"} for status in configured_checks)
    result = {
        "status": "checked" if rdap_status == "checked" or reputation_checked else "unavailable",
        "domain_age_days": age_days,
        "domain_registered_at": registered_at,
        "rdap_status": rdap_status,
        "reputation": reputation,
        "reputation_sources": {
            "google_safe_browsing": {"status": safe_status, "details": safe_details},
            "urlhaus": {"status": urlhaus_status, "details": urlhaus_details},
        },
        "external_risk_score": score,
        "reasons": reasons,
    }
    if len(_result_cache) >= 512:
        _result_cache.clear()
    _result_cache[cache_key] = (time.monotonic() + 21_600, result)
    return result
