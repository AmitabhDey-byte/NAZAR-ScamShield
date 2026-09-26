import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import AnalysisRequest, HoneypotMessage, HoneypotSession, HoneypotTelemetryHit
from app.schemas import HoneypotMessageRequest, HoneypotStartRequest
from app.services.gemini import generate_honeypot_reply
from app.services.honeypot import merge_intelligence, next_response
from app.services.realtime import broker
from app.services.telemetry import client_type, enrich_telemetry_hit, request_ip
from app.core.config import settings


router = APIRouter(prefix="/api/honeypot", tags=["honeypot"])


def configured_canary_url() -> str | None:
    """Return a configured Canarytokens URL without ever requesting it."""
    return settings.validated_canarytoken_url


def telemetry_beacon_configured() -> bool:
    return configured_canary_url() is not None and bool(settings.public_api_url)


def add_canary_lure(reply: str, intelligence: dict, beacon_url: str | None = None) -> tuple[str, dict, bool]:
    """Append the visible tripwire once when this session was explicitly armed."""
    canary = dict(intelligence.get("canary") or {})
    url = beacon_url or configured_canary_url()
    if not canary.get("armed") or canary.get("proposed") or not url:
        return reply, intelligence, False
    canary["proposed"] = True
    intelligence["canary"] = canary
    lure = "I cannot open the receipt page on my phone. Can you open this link on your side and tell me what it shows?"
    return f"{reply}\n\n{lure} {url}", intelligence, True


def serialize(
    session: HoneypotSession,
    messages: list[HoneypotMessage],
    engine: str | None = None,
    telemetry: list[HoneypotTelemetryHit] | None = None,
) -> dict:
    canary = dict((session.intelligence or {}).get("canary") or {})
    return {
        "id": session.id,
        "analysis_id": session.analysis_id,
        "state": session.state,
        "active": session.active,
        "intelligence": session.intelligence,
        "reply_engine": engine,
        "gemini_available": bool(settings.gemini_api_key),
        "canary": {
            "configured": telemetry_beacon_configured(),
            "armed": bool(canary.get("armed")),
            "proposed": bool(canary.get("proposed")),
        },
        "telemetry": [
            {
                "id": hit.id,
                "ip_address": hit.ip_address,
                "user_agent": hit.user_agent,
                "accept_language": hit.accept_language,
                "referrer": hit.referrer,
                "client_type": hit.client_type,
                "country": hit.country,
                "region": hit.region,
                "city": hit.city,
                "latitude": hit.latitude,
                "longitude": hit.longitude,
                "postal": hit.postal,
                "timezone": hit.timezone,
                "asn": hit.asn,
                "organization": hit.organization,
                "hostname": hit.hostname,
                "privacy_flags": hit.privacy_flags,
                "geo_status": hit.geo_status,
                "created_at": hit.created_at,
            }
            for hit in (telemetry or [])
        ],
        "messages": [
            {"id": msg.id, "role": msg.role, "content": msg.content, "created_at": msg.created_at}
            for msg in messages
        ],
    }


@router.post("/start")
async def start(payload: HoneypotStartRequest, db: AsyncSession = Depends(get_session)):
    analysis = await db.get(AnalysisRequest, payload.analysis_id) if payload.analysis_id else None
    if payload.analysis_id and not analysis:
        raise HTTPException(404, "Analysis not found")
    risk_score = float(analysis.score) if analysis else None
    risk_eligible = risk_score is not None and risk_score >= settings.telemetry_risk_threshold
    canary_configured = telemetry_beacon_configured()
    session = HoneypotSession(
        analysis_id=payload.analysis_id,
        intelligence={
            "canary": {
                "requested": payload.enable_canary,
                "armed": payload.enable_canary and canary_configured,
                "proposed": False,
            },
            "telemetry_policy": {
                "risk_score": risk_score,
                "threshold": settings.telemetry_risk_threshold,
                "eligible": risk_eligible,
            },
        },
    )
    session.intelligence["canary"]["armed"] = payload.enable_canary and canary_configured and risk_eligible
    db.add(session)
    await db.flush()
    opening = HoneypotMessage(
        session_id=session.id,
        role="assistant",
        content="Hello, I saw your message. I am checking the bill now—can you explain what I need to do?",
    )
    db.add(opening)
    await db.commit()
    await db.refresh(opening)
    await broker.publish(
        "honeypot.started",
        {
            "session_id": session.id,
            "analysis_id": session.analysis_id,
            "canary_armed": payload.enable_canary and canary_configured and risk_eligible,
        },
    )
    return serialize(session, [opening], "safe-opening")


@router.post("/{session_id}/message")
async def send_message(session_id: str, payload: HoneypotMessageRequest, db: AsyncSession = Depends(get_session)):
    session = await db.get(HoneypotSession, session_id)
    if not session:
        raise HTTPException(404, "Honeypot session not found")
    if not session.active:
        raise HTTPException(409, "Honeypot session is complete")
    scammer = HoneypotMessage(session_id=session.id, role="scammer", content=payload.content)
    intelligence = merge_intelligence(session.intelligence or {}, payload.content)
    previous = (await db.scalars(
        select(HoneypotMessage)
        .where(HoneypotMessage.session_id == session.id)
        .order_by(HoneypotMessage.created_at.desc())
        .limit(11)
    )).all()
    history = [{"role": msg.role, "content": msg.content} for msg in reversed(previous)]
    history.append({"role": "scammer", "content": payload.content})
    ai_turn = await generate_honeypot_reply(history, session.state, intelligence)
    if ai_turn:
        next_state, reply, engine = ai_turn["next_state"], ai_turn["reply"], "gemini"
    else:
        next_state, reply = next_response(session.state, payload.content, intelligence)
        engine = "rules"
    beacon_url = None
    if intelligence.get("canary", {}).get("armed") and not intelligence.get("canary", {}).get("proposed"):
        beacon_token = secrets.token_urlsafe(32)
        session.beacon_token_hash = hashlib.sha256(beacon_token.encode()).hexdigest()
        beacon_url = f"{settings.public_api_url.rstrip('/')}/api/honeypot/b/{beacon_token}"
    reply, intelligence, canary_added = add_canary_lure(reply, intelligence, beacon_url)
    if canary_added:
        engine = f"{engine}+canary"
    assistant = HoneypotMessage(session_id=session.id, role="assistant", content=reply)
    session.state = next_state
    session.intelligence = intelligence
    session.active = next_state != "COMPLETE"
    db.add_all([scammer, assistant])
    await db.commit()
    messages = (await db.scalars(select(HoneypotMessage).where(HoneypotMessage.session_id == session.id).order_by(HoneypotMessage.created_at))).all()
    telemetry = (await db.scalars(select(HoneypotTelemetryHit).where(HoneypotTelemetryHit.session_id == session.id).order_by(HoneypotTelemetryHit.created_at.desc()))).all()
    await broker.publish(
        "honeypot.turn",
        {
            "session_id": session.id,
            "state": session.state,
            "engine": engine,
            "canary_proposed": canary_added,
        },
    )
    return serialize(session, list(messages), engine, list(telemetry))


@router.get("/b/{beacon_token}", include_in_schema=False)
async def collect_telemetry(
    beacon_token: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    token_hash = hashlib.sha256(beacon_token.encode()).hexdigest()
    session = await db.scalar(select(HoneypotSession).where(HoneypotSession.beacon_token_hash == token_hash))
    if not session or not hmac.compare_digest(session.beacon_token_hash or "", token_hash):
        raise HTTPException(404, "Beacon not found")
    canary = (session.intelligence or {}).get("canary", {})
    policy = (session.intelligence or {}).get("telemetry_policy", {})
    if not canary.get("armed") or not policy.get("eligible"):
        raise HTTPException(404, "Beacon not found")

    user_agent = request.headers.get("user-agent", "")[:4000]
    hit = HoneypotTelemetryHit(
        session_id=session.id,
        ip_address=request_ip(request)[:64],
        user_agent=user_agent,
        accept_language=request.headers.get("accept-language", "")[:500],
        referrer=(request.headers.get("referer") or "")[:4000] or None,
        client_type=client_type(user_agent),
        geo_status="pending",
    )
    retention_cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, settings.telemetry_retention_days))
    await db.execute(delete(HoneypotTelemetryHit).where(HoneypotTelemetryHit.created_at < retention_cutoff))
    db.add(hit)
    await db.commit()
    await db.refresh(hit)
    await broker.publish(
        "honeypot.telemetry.captured",
        {"session_id": session.id, "hit_id": hit.id, "client_type": hit.client_type},
    )
    background_tasks.add_task(enrich_telemetry_hit, hit.id, hit.ip_address)
    destination = configured_canary_url()
    if not destination:
        raise HTTPException(410, "Canary destination is no longer configured")
    return RedirectResponse(
        destination,
        status_code=302,
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
        background=background_tasks,
    )


@router.get("/{session_id}")
async def get_honeypot(session_id: str, db: AsyncSession = Depends(get_session)):
    session = await db.get(HoneypotSession, session_id)
    if not session:
        raise HTTPException(404, "Honeypot session not found")
    messages = (await db.scalars(select(HoneypotMessage).where(HoneypotMessage.session_id == session.id).order_by(HoneypotMessage.created_at))).all()
    telemetry = (await db.scalars(select(HoneypotTelemetryHit).where(HoneypotTelemetryHit.session_id == session.id).order_by(HoneypotTelemetryHit.created_at.desc()))).all()
    return serialize(session, list(messages), telemetry=list(telemetry))
