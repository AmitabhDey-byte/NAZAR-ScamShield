from __future__ import annotations

import hmac
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database import get_session
from app.models import AnalysisRequest
from app.schemas import GmailWebhookRequest, TwilioWebhookRequest
from app.routers.analysis import persist
from app.services.pipeline import analyze_pipeline


router = APIRouter(prefix="/api/integrations", tags=["integrations"])


def _source_marker(label: str, external_id: str | None) -> str:
    return f"\n\n[NAZAR {label}: {external_id}]" if external_id else ""


async def _existing_delivery(
    db: AsyncSession,
    source_type: str,
    marker: str,
) -> AnalysisRequest | None:
    if not marker:
        return None
    return await db.scalar(
        select(AnalysisRequest)
        .where(AnalysisRequest.source_type == source_type)
        .where(AnalysisRequest.input_text.endswith(marker))
        .order_by(AnalysisRequest.created_at.desc())
        .limit(1)
    )


@router.get("/status")
async def integration_status(db: AsyncSession = Depends(get_session)):
    """Report actual persisted deliveries without exposing message contents."""
    supported = ("gmail", "twilio_whatsapp", "twilio_sms")
    rows = (await db.execute(
        select(
            AnalysisRequest.source_type,
            func.count(AnalysisRequest.id),
            func.max(AnalysisRequest.created_at),
        )
        .where(AnalysisRequest.source_type.in_(supported))
        .group_by(AnalysisRequest.source_type)
    )).all()
    observed = {
        source: {"count": int(count), "last_received_at": last_received}
        for source, count, last_received in rows
    }
    channels = {}
    for source in supported:
        delivery = observed.get(source, {"count": 0, "last_received_at": None})
        channels[source] = {
            **delivery,
            "status": "receiving" if delivery["count"] else "awaiting-first-event",
        }
    return {
        "n8n_secret": "configured" if settings.n8n_webhook_secret else "not-configured",
        "gemini": "configured" if settings.gemini_api_key else "not-configured",
        "canarytoken": "configured" if settings.validated_canarytoken_url else "not-configured",
        "honeypot_telemetry": "configured" if settings.validated_canarytoken_url and settings.public_api_url else "not-configured",
        "ipinfo": "configured" if settings.ipinfo_token else "not-configured",
        "honeypot_auto_reply": "enabled" if settings.honeypot_auto_reply_enabled else "human-approval",
        "channels": channels,
        "checked_at": datetime.now(timezone.utc),
    }


def _header_value(headers: list[dict], name: str) -> str:
    for item in headers:
        if str(item.get("name", "")).lower() == name.lower():
            return str(item.get("value", ""))
    return ""


def _extract_gmail_payload(payload: dict) -> GmailWebhookRequest:
    """Accept n8n's normalized fields and Gmail API-shaped payloads."""
    nested = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
    headers = nested.get("headers") if isinstance(nested.get("headers"), list) else []
    sender = payload.get("from") or payload.get("sender") or payload.get("From") or _header_value(headers, "From")
    subject = payload.get("subject") or payload.get("Subject") or _header_value(headers, "Subject")
    text = payload.get("text") or payload.get("Text") or payload.get("body") or payload.get("Body") or payload.get("snippet") or ""
    if isinstance(text, dict):
        text = text.get("data", "")
    html = payload.get("html") or payload.get("HTML") or ""
    received = payload.get("received_at") or payload.get("date") or _header_value(headers, "Date") or None
    parsed_received = None
    if isinstance(received, str):
        try:
            parsed_received = datetime.fromisoformat(received.replace("Z", "+00:00"))
        except ValueError:
            parsed_received = None
    return GmailWebhookRequest(
        **{"from": str(sender)[:320] if sender else None},
        subject=str(subject or "")[:500], text=str(text or "")[:40000], html=str(html or "")[:80000],
        snippet=str(payload.get("snippet") or "")[:2000], message_id=payload.get("id") or payload.get("messageId"),
        thread_id=payload.get("threadId") or nested.get("threadId"), received_at=parsed_received,
    )


def _extract_twilio_payload(payload: dict) -> TwilioWebhookRequest:
    """Accept the flat n8n mapping or Twilio's original form field names."""
    event = payload.get("body") if isinstance(payload.get("body"), dict) else payload
    return TwilioWebhookRequest.model_validate({
        "from": event.get("from") or event.get("From"),
        "to": event.get("to") or event.get("To"),
        "body": event.get("body") or event.get("Body") or "",
        "MessageSid": event.get("MessageSid") or event.get("SmsMessageSid"),
        "channel": event.get("channel") or "sms",
        "ProfileName": event.get("ProfileName") or event.get("profile_name"),
    })


@router.post("/n8n/gmail")
async def ingest_gmail(
    request: Request,
    x_nazar_webhook_secret: str | None = Header(default=None),
    db: AsyncSession = Depends(get_session),
):
    if not settings.n8n_webhook_secret:
        raise HTTPException(503, "N8N_WEBHOOK_SECRET is not configured")
    if not x_nazar_webhook_secret or not hmac.compare_digest(x_nazar_webhook_secret, settings.n8n_webhook_secret):
        raise HTTPException(401, "Invalid n8n webhook secret")
    raw = await request.json()
    if not isinstance(raw, dict):
        raise HTTPException(422, "Expected a Gmail event object")
    email = _extract_gmail_payload(raw)
    body = re.sub(r"<[^>]+>", " ", email.html) if not email.text else email.text
    evidence = "\n".join(filter(None, [f"From: {email.sender}" if email.sender else "", f"Subject: {email.subject}" if email.subject else "", body, email.snippet]))
    if len(evidence.strip()) < 3:
        raise HTTPException(422, "Gmail event has no readable subject or body")
    marker = _source_marker("Gmail message ID", email.message_id)
    existing = await _existing_delivery(db, "gmail", marker)
    if existing:
        return {
            "status": "duplicate", "source": "gmail", "message_id": email.message_id,
            "thread_id": email.thread_id, "analysis": existing,
        }
    result = await analyze_pipeline(evidence[:40000], db=db)
    persisted = await persist(result, "gmail", evidence[:40000] + marker, db)
    return {"status": "accepted", "source": "gmail", "message_id": email.message_id, "thread_id": email.thread_id, "analysis": persisted}


@router.post("/n8n/twilio")
async def ingest_twilio(
    request: Request,
    x_nazar_webhook_secret: str | None = Header(default=None),
    db: AsyncSession = Depends(get_session),
):
    """Ingest a Twilio SMS/WhatsApp event normalized by an n8n Webhook node."""
    if not settings.n8n_webhook_secret:
        raise HTTPException(503, "N8N_WEBHOOK_SECRET is not configured")
    if not x_nazar_webhook_secret or not hmac.compare_digest(x_nazar_webhook_secret, settings.n8n_webhook_secret):
        raise HTTPException(401, "Invalid n8n webhook secret")
    raw = await request.json()
    if not isinstance(raw, dict):
        raise HTTPException(422, "Expected a Twilio event object")
    event = _extract_twilio_payload(raw)
    channel = event.channel.lower()
    source = "twilio_whatsapp" if "whatsapp" in channel or str(event.sender or "").startswith("whatsapp:") else "twilio_sms"
    evidence = "\n".join(filter(None, [
        f"Sender: {event.sender}" if event.sender else "",
        f"Profile: {event.profile_name}" if event.profile_name else "",
        event.body,
    ]))
    marker = _source_marker("Twilio message SID", event.message_sid)
    existing = await _existing_delivery(db, source, marker)
    if existing:
        return {
            "status": "duplicate", "source": source, "message_sid": event.message_sid,
            "sender": event.sender, "recipient": event.recipient, "analysis": existing,
            "reply_mode": "analyst-approved-n8n-send",
        }
    result = await analyze_pipeline(evidence[:20000], db=db)
    persisted = await persist(result, source, evidence[:20000] + marker, db)
    return {
        "status": "accepted", "source": source, "message_sid": event.message_sid,
        "sender": event.sender, "recipient": event.recipient, "analysis": persisted,
        "reply_mode": "analyst-approved-n8n-send",
    }
