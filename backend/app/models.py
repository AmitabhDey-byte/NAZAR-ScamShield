from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def uid() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    display_name: Mapped[str] = mapped_column(String(120), default="Analyst")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AnalysisRequest(Base):
    __tablename__ = "analysis_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_type: Mapped[str] = mapped_column(String(32), default="message")
    input_text: Mapped[str] = mapped_column(Text, default="")
    score: Mapped[float] = mapped_column(Float)
    classification: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(64))
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    entities: Mapped[dict] = mapped_column(JSON, default=dict)
    component_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    recommended_action: Mapped[str] = mapped_column(Text)
    ai_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ScamReport(Base):
    __tablename__ = "scam_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    phone_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    upi_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    message: Mapped[str] = mapped_column(Text, default="")
    scam_category: Mapped[str] = mapped_column(String(64), default="payment_request_scam")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ThreatIndicator(Base):
    __tablename__ = "threat_indicators"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    type: Mapped[str] = mapped_column(String(40), index=True)
    value: Mapped[str] = mapped_column(Text, index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=50)
    report_count: Mapped[int] = mapped_column(Integer, default=1)
    observation_count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ThreatEdge(Base):
    __tablename__ = "threat_edges"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey("threat_indicators.id"))
    target_id: Mapped[str] = mapped_column(ForeignKey("threat_indicators.id"))
    edge_type: Mapped[str] = mapped_column(String(48))
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(160))
    scam_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="active")
    report_count: Mapped[int] = mapped_column(Integer, default=1)
    fingerprint: Mapped[dict] = mapped_column(JSON, default=dict)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class CampaignIndicator(Base):
    __tablename__ = "campaign_indicators"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"))
    indicator_id: Mapped[str] = mapped_column(ForeignKey("threat_indicators.id"))
    confidence: Mapped[float] = mapped_column(Float, default=0.8)


class HoneypotSession(Base):
    __tablename__ = "honeypot_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    analysis_id: Mapped[str | None] = mapped_column(ForeignKey("analysis_requests.id"), nullable=True)
    state: Mapped[str] = mapped_column(String(64), default="INITIAL_CONTACT")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    intelligence: Mapped[dict] = mapped_column(JSON, default=dict)
    beacon_token_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class HoneypotMessage(Base):
    __tablename__ = "honeypot_messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    session_id: Mapped[str] = mapped_column(ForeignKey("honeypot_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(24))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class HoneypotTelemetryHit(Base):
    __tablename__ = "honeypot_telemetry_hits"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    session_id: Mapped[str] = mapped_column(ForeignKey("honeypot_sessions.id"), index=True)
    ip_address: Mapped[str] = mapped_column(String(64))
    user_agent: Mapped[str] = mapped_column(Text, default="")
    accept_language: Mapped[str] = mapped_column(String(500), default="")
    referrer: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_type: Mapped[str] = mapped_column(String(64), default="browser")
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    region: Mapped[str | None] = mapped_column(String(160), nullable=True)
    city: Mapped[str | None] = mapped_column(String(160), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    postal: Mapped[str | None] = mapped_column(String(40), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    asn: Mapped[str | None] = mapped_column(String(64), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(240), nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    privacy_flags: Mapped[dict] = mapped_column(JSON, default=dict)
    geo_status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    amount: Mapped[float] = mapped_column(Float)
    payee: Mapped[str] = mapped_column(String(180))
    is_new_recipient: Mapped[bool] = mapped_column(Boolean, default=False)
    transaction_hour: Mapped[int] = mapped_column(Integer, default=12)
    recent_frequency: Mapped[int] = mapped_column(Integer, default=0)
    anomaly_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ModelMetric(Base):
    __tablename__ = "model_metrics"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    model_name: Mapped[str] = mapped_column(String(100))
    accuracy: Mapped[float] = mapped_column(Float)
    precision: Mapped[float] = mapped_column(Float)
    recall: Mapped[float] = mapped_column(Float)
    f1: Mapped[float] = mapped_column(Float)
    sample_count: Mapped[int] = mapped_column(Integer)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(120))
    platform: Mapped[str] = mapped_column(String(24), default="android")
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    protection_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    app_version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class MobileEvent(Base):
    __tablename__ = "mobile_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"), index=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analysis_requests.id"), index=True)
    source_package: Mapped[str] = mapped_column(String(180), default="manual")
    source_label: Mapped[str] = mapped_column(String(100), default="Shared text")
    preview: Mapped[str] = mapped_column(Text, default="")
    classification: Mapped[str] = mapped_column(String(20))
    score: Mapped[float] = mapped_column(Float)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
