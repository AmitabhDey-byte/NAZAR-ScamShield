from __future__ import annotations

import hmac
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database import get_session
from app.schemas import GmailWebhookRequest, TwilioWebhookRequest
from app.routers.analysis import persist
from app.services.pipeline import analyze_pipeline


router = APIRouter(prefix="/api/integrations", tags=["integrations"])


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
    result = await analyze_pipeline(evidence[:40000])
    persisted = await persist(result, "gmail", evidence[:40000], db)
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
    event = TwilioWebhookRequest.model_validate(raw)
    channel = event.channel.lower()
    source = "twilio_whatsapp" if "whatsapp" in channel or str(event.sender or "").startswith("whatsapp:") else "twilio_sms"
    evidence = "\n".join(filter(None, [
        f"Sender: {event.sender}" if event.sender else "",
        f"Profile: {event.profile_name}" if event.profile_name else "",
        event.body,
    ]))
    result = await analyze_pipeline(evidence[:20000])
    persisted = await persist(result, source, evidence[:20000], db)
    return {
        "status": "accepted", "source": source, "message_sid": event.message_sid,
        "sender": event.sender, "recipient": event.recipient, "analysis": persisted,
        "reply_mode": "analyst-approved-n8n-send",
    }
