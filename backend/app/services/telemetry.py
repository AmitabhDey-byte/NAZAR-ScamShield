from __future__ import annotations

import ipaddress

import httpx
from fastapi import Request

from app.core.config import settings
from app.database import SessionLocal
from app.models import HoneypotTelemetryHit
from app.services.realtime import broker


def request_ip(request: Request) -> str:
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            candidate = forwarded.split(",", 1)[0].strip()
            try:
                return str(ipaddress.ip_address(candidate))
            except ValueError:
                pass
    return request.client.host if request.client else "unknown"


def client_type(user_agent: str) -> str:
    lowered = user_agent.lower()
    preview_markers = (
        "facebookexternalhit", "whatsapp", "twitterbot", "telegrambot",
        "slackbot", "discordbot", "googlebot", "bingbot",
    )
    if any(marker in lowered for marker in preview_markers):
        return "link-preview-or-bot"
    if "android" in lowered:
        return "android-browser"
    if any(marker in lowered for marker in ("iphone", "ipad", "ios")):
        return "ios-browser"
    return "browser"


async def lookup_ip(ip: str) -> tuple[dict, str]:
    if not settings.telemetry_geoip_enabled:
        return {}, "disabled"
    if not settings.ipinfo_token:
        return {}, "token-not-configured"
    try:
        parsed = ipaddress.ip_address(ip)
    except ValueError:
        return {}, "invalid-ip"
    if not parsed.is_global:
        return {}, "private-or-reserved-ip"
    tier = settings.ipinfo_tier.strip().lower()
    endpoint = "lookup" if tier in {"core", "plus", "max"} else "lite"
    try:
        async with httpx.AsyncClient(timeout=settings.telemetry_timeout_seconds) as client:
            response = await client.get(
                f"https://api.ipinfo.io/{endpoint}/{parsed}",
                params={"token": settings.ipinfo_token},
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError):
        return {}, "lookup-failed"
    if not isinstance(data, dict):
        return {}, "lookup-failed"

    geo = data.get("geo") if isinstance(data.get("geo"), dict) else data
    asn_data = data.get("as") if isinstance(data.get("as"), dict) else data.get("asn") if isinstance(data.get("asn"), dict) else {}
    latitude = longitude = None
    if isinstance(geo.get("loc"), str) and "," in geo["loc"]:
        try:
            latitude, longitude = (float(value) for value in geo["loc"].split(",", 1))
        except ValueError:
            latitude = longitude = None
    elif geo.get("latitude") is not None and geo.get("longitude") is not None:
        try:
            latitude, longitude = float(geo["latitude"]), float(geo["longitude"])
        except (TypeError, ValueError):
            latitude = longitude = None
    privacy = data.get("privacy") if isinstance(data.get("privacy"), dict) else data.get("anonymous") if isinstance(data.get("anonymous"), dict) else {}
    organization = str(data.get("org") or data.get("as_name") or asn_data.get("name") or "") or None
    asn = organization.split(" ", 1)[0] if organization and organization.startswith("AS") else asn_data.get("asn") or data.get("asn")
    if isinstance(asn, dict):
        asn = asn.get("asn")
    privacy_flags = {}
    for label in ("vpn", "proxy", "tor", "relay", "hosting"):
        value = privacy.get(label)
        if value is None:
            value = privacy.get(f"is_{label}")
        if value is None:
            value = data.get(f"is_{label}")
        if value is not None:
            privacy_flags[label] = bool(value)
    return {
        "country": geo.get("country") or data.get("country_code"),
        "region": geo.get("region"),
        "city": geo.get("city"),
        "latitude": latitude,
        "longitude": longitude,
        "postal": geo.get("postal") or geo.get("postal_code"),
        "timezone": geo.get("timezone"),
        "asn": str(asn)[:64] if asn else None,
        "organization": organization[:240] if organization else None,
        "hostname": str(data.get("hostname"))[:255] if data.get("hostname") else None,
        "privacy_flags": privacy_flags,
    }, "complete"


async def enrich_telemetry_hit(hit_id: str, ip: str) -> None:
    enrichment, status = await lookup_ip(ip)
    async with SessionLocal() as db:
        hit = await db.get(HoneypotTelemetryHit, hit_id)
        if not hit:
            return
        for key, value in enrichment.items():
            setattr(hit, key, value)
        hit.geo_status = status
        await db.commit()
        await broker.publish(
            "honeypot.telemetry.enriched",
            {"session_id": hit.session_id, "hit_id": hit.id, "geo_status": status},
        )
