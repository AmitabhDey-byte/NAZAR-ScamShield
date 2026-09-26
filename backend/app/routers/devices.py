from __future__ import annotations

import hashlib
import re
import secrets
import socket
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database import get_session
from app.models import AnalysisRequest, Device, MobileEvent
from app.schemas import DeviceRegisterRequest, MobileEventCreate
from app.services.intelligence import record_indicators
from app.services.pipeline import analyze_pipeline
from app.services.realtime import broker


router = APIRouter(prefix="/api/devices", tags=["devices"])
_pair_codes: dict[str, datetime] = {}


def local_api_url() -> str:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        address = probe.getsockname()[0]
    except OSError:
        address = socket.gethostbyname(socket.gethostname())
    finally:
        probe.close()
    return f"http://{address}:8000"


def public_api_url(request: Request) -> str:
    """Return an address the phone can actually reach.

    Hosted platforms expose an internal machine address to Python, so local
    socket discovery is only suitable for local development. Prefer an
    explicit public URL and otherwise honor the proxy host Render forwards.
    """
    if settings.public_api_url:
        return settings.public_api_url.rstrip("/")

    forwarded_host = request.headers.get("x-forwarded-host", "").split(",", 1)[0].strip()
    host = forwarded_host or request.headers.get("host", "").strip()
    if host and not host.startswith(("localhost", "127.0.0.1", "0.0.0.0")):
        forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",", 1)[0].strip()
        scheme = forwarded_proto or request.url.scheme or "https"
        return f"{scheme}://{host}".rstrip("/")

    return local_api_url()


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def serialize_device(device: Device) -> dict:
    return {
        "id": device.id,
        "name": device.name,
        "platform": device.platform,
        "protection_enabled": device.protection_enabled,
        "app_version": device.app_version,
        "last_seen": device.last_seen,
        "created_at": device.created_at,
    }


async def authenticate(device_id: str, token: str | None, db: AsyncSession) -> Device:
    device = await db.get(Device, device_id)
    if not device or not token or not secrets.compare_digest(device.token_hash, token_hash(token)):
        raise HTTPException(401, "Invalid device credentials")
    return device


@router.post("/pair-code")
async def create_pair_code(request: Request):
    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    _pair_codes[code] = expires_at
    return {"code": code, "expires_at": expires_at, "api_url": public_api_url(request)}


@router.post("/register")
async def register(payload: DeviceRegisterRequest, db: AsyncSession = Depends(get_session)):
    expires_at = _pair_codes.pop(payload.pair_code, None)
    if not expires_at or expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, "Pairing code is invalid or expired")
    raw_token = secrets.token_urlsafe(32)
    device = Device(
        name=payload.device_name,
        platform=payload.platform,
        app_version=payload.app_version,
        token_hash=token_hash(raw_token),
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    await broker.publish("device.registered", {"device_id": device.id, "name": device.name, "platform": device.platform})
    return {"device": serialize_device(device), "device_token": raw_token}


@router.get("")
async def list_devices(db: AsyncSession = Depends(get_session)):
    rows = (await db.scalars(select(Device).order_by(Device.last_seen.desc()))).all()
    return [serialize_device(row) for row in rows]


@router.post("/{device_id}/heartbeat")
async def heartbeat(
    device_id: str,
    protection_enabled: bool,
    x_device_token: str | None = Header(default=None),
    db: AsyncSession = Depends(get_session),
):
    device = await authenticate(device_id, x_device_token, db)
    device.last_seen = datetime.now(timezone.utc)
    device.protection_enabled = protection_enabled
    await db.commit()
    return {"status": "online", "last_seen": device.last_seen}


@router.post("/{device_id}/events")
async def ingest_event(
    device_id: str,
    payload: MobileEventCreate,
    x_device_token: str | None = Header(default=None),
    db: AsyncSession = Depends(get_session),
):
    device = await authenticate(device_id, x_device_token, db)
    if re.search(r"\b(?:otp|one[- ]time password|verification code|authentication code|auth code|cvv|pin)\b", payload.text, re.I) and re.search(r"\b\d{4,8}\b", payload.text):
        raise HTTPException(422, "Authentication-code notifications are not collected")
    result = await analyze_pipeline(payload.text)
    analysis = AnalysisRequest(
        id=result["id"], source_type="mobile", input_text=payload.text, score=result["score"],
        classification=result["classification"], category=result["category"], reasons=result["reasons"],
        entities=result["entities"], component_scores=result["component_scores"],
        recommended_action=result["recommended_action"], created_at=result["created_at"],
        ai_provider=result["ai_provider"], ai_model=result["ai_model"], ai_summary=result["ai_summary"],
        ai_confidence=result["ai_confidence"],
    )
    event = MobileEvent(
        device_id=device.id,
        analysis_id=analysis.id,
        source_package=payload.source_package,
        source_label=payload.source_label,
        preview=payload.text[:220],
        classification=result["classification"],
        score=result["score"],
    )
    device.last_seen = datetime.now(timezone.utc)
    db.add_all([analysis, event])
    await db.flush()
    await record_indicators(db, result["entities"], result["score"])
    await db.commit()
    await broker.publish("device.event", {
        "device_id": device.id, "event_id": event.id, "analysis_id": analysis.id,
        "classification": result["classification"], "score": result["score"],
    })
    return {"event_id": event.id, "analysis": result}


@router.get("/{device_id}/events")
async def device_events(
    device_id: str,
    x_device_token: str | None = Header(default=None),
    db: AsyncSession = Depends(get_session),
):
    await authenticate(device_id, x_device_token, db)
    rows = (await db.scalars(select(MobileEvent).where(MobileEvent.device_id == device_id).order_by(MobileEvent.created_at.desc()).limit(50))).all()
    return [
        {"id": row.id, "analysis_id": row.analysis_id, "source_label": row.source_label, "preview": row.preview,
         "classification": row.classification, "score": row.score, "acknowledged": row.acknowledged, "created_at": row.created_at}
        for row in rows
    ]


@router.get("/{device_id}/feed")
async def device_feed(
    device_id: str,
    x_device_token: str | None = Header(default=None),
    db: AsyncSession = Depends(get_session),
):
    """Scoped phone feed: local scans plus live Gmail/Twilio signals."""
    await authenticate(device_id, x_device_token, db)
    local_rows = (await db.scalars(
        select(MobileEvent).where(MobileEvent.device_id == device_id)
        .order_by(MobileEvent.created_at.desc()).limit(50)
    )).all()
    external_rows = (await db.scalars(
        select(AnalysisRequest).where(AnalysisRequest.source_type.in_(["gmail", "twilio_sms", "twilio_whatsapp"]))
        .order_by(AnalysisRequest.created_at.desc()).limit(50)
    )).all()
    feed = [
        {"id": row.id, "analysis_id": row.analysis_id, "source_label": row.source_label, "preview": row.preview,
         "classification": row.classification, "score": row.score, "acknowledged": row.acknowledged, "created_at": row.created_at}
        for row in local_rows
    ]
    feed += [
        {"id": f"external-{row.id}", "analysis_id": row.id, "source_label": row.source_type.replace("_", " ").title(),
         "preview": row.input_text[:220], "classification": row.classification, "score": row.score,
         "acknowledged": False, "created_at": row.created_at}
        for row in external_rows
    ]
    return sorted(feed, key=lambda item: item["created_at"], reverse=True)[:50]
