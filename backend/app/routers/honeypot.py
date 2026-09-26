from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import HoneypotMessage, HoneypotSession
from app.schemas import HoneypotMessageRequest, HoneypotStartRequest
from app.services.gemini import generate_honeypot_reply
from app.services.honeypot import merge_intelligence, next_response
from app.services.realtime import broker
from app.core.config import settings


router = APIRouter(prefix="/api/honeypot", tags=["honeypot"])


def configured_canary_url() -> str | None:
    """Return a configured Canarytokens URL without ever requesting it."""
    return settings.validated_canarytoken_url


def add_canary_lure(reply: str, intelligence: dict) -> tuple[str, dict, bool]:
    """Append the visible tripwire once when this session was explicitly armed."""
    canary = dict(intelligence.get("canary") or {})
    url = configured_canary_url()
    if not canary.get("armed") or canary.get("proposed") or not url:
        return reply, intelligence, False
    canary["proposed"] = True
    intelligence["canary"] = canary
    lure = "I cannot open the receipt page on my phone. Can you open this link on your side and tell me what it shows?"
    return f"{reply}\n\n{lure} {url}", intelligence, True


def serialize(session: HoneypotSession, messages: list[HoneypotMessage], engine: str | None = None) -> dict:
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
            "configured": configured_canary_url() is not None,
            "armed": bool(canary.get("armed")),
            "proposed": bool(canary.get("proposed")),
        },
        "messages": [
            {"id": msg.id, "role": msg.role, "content": msg.content, "created_at": msg.created_at}
            for msg in messages
        ],
    }


@router.post("/start")
async def start(payload: HoneypotStartRequest, db: AsyncSession = Depends(get_session)):
    canary_configured = configured_canary_url() is not None
    session = HoneypotSession(
        analysis_id=payload.analysis_id,
        intelligence={
            "canary": {
                "requested": payload.enable_canary,
                "armed": payload.enable_canary and canary_configured,
                "proposed": False,
            }
        },
    )
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
            "canary_armed": payload.enable_canary and canary_configured,
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
    reply, intelligence, canary_added = add_canary_lure(reply, intelligence)
    if canary_added:
        engine = f"{engine}+canary"
    assistant = HoneypotMessage(session_id=session.id, role="assistant", content=reply)
    session.state = next_state
    session.intelligence = intelligence
    session.active = next_state != "COMPLETE"
    db.add_all([scammer, assistant])
    await db.commit()
    messages = (await db.scalars(select(HoneypotMessage).where(HoneypotMessage.session_id == session.id).order_by(HoneypotMessage.created_at))).all()
    await broker.publish(
        "honeypot.turn",
        {
            "session_id": session.id,
            "state": session.state,
            "engine": engine,
            "canary_proposed": canary_added,
        },
    )
    return serialize(session, list(messages), engine)


@router.get("/{session_id}")
async def get_honeypot(session_id: str, db: AsyncSession = Depends(get_session)):
    session = await db.get(HoneypotSession, session_id)
    if not session:
        raise HTTPException(404, "Honeypot session not found")
    messages = (await db.scalars(select(HoneypotMessage).where(HoneypotMessage.session_id == session.id).order_by(HoneypotMessage.created_at))).all()
    return serialize(session, list(messages))
