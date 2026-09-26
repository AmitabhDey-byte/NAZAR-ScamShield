import asyncio
import re

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.database import Base, get_session
from app.main import app
from app.models import AnalysisRequest
from app.routers.honeypot import add_canary_lure, configured_canary_url
from app.services.telemetry import client_type


engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def prepare_database(score: float = 80) -> str:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with Session() as db:
        analysis = AnalysisRequest(
            source_type="test", input_text="controlled test", score=score,
            classification="DANGEROUS" if score >= 70 else "SAFE", category="phishing", reasons=[], entities={},
            component_scores={}, recommended_action="Do not engage.",
        )
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        return analysis.id


async def override_session():
    async with Session() as session:
        yield session


def test_canary_url_accepts_only_official_hosts(monkeypatch):
    monkeypatch.setattr(settings, "canarytoken_url", "https://example.com/tracker")
    assert configured_canary_url() is None

    monkeypatch.setattr(settings, "canarytoken_url", "https://canarytokens.com/example/token")
    assert configured_canary_url() == "https://canarytokens.com/example/token"


def test_canary_lure_is_opt_in_and_added_only_once(monkeypatch):
    monkeypatch.setattr(settings, "canarytoken_url", "https://canarytokens.com/example/token")
    intelligence = {"canary": {"armed": True, "proposed": False}}

    reply, intelligence, added = add_canary_lure("Please wait.", intelligence)
    assert added is True
    assert "https://canarytokens.com/example/token" in reply
    assert intelligence["canary"]["proposed"] is True

    second_reply, _, added_again = add_canary_lure("Still checking.", intelligence)
    assert added_again is False
    assert "canarytokens.com" not in second_reply


def test_canary_lure_stays_off_when_session_is_not_armed(monkeypatch):
    monkeypatch.setattr(settings, "canarytoken_url", "https://canarytokens.com/example/token")
    reply, _, added = add_canary_lure("Please wait.", {"canary": {"armed": False}})
    assert added is False
    assert reply == "Please wait."


def test_client_type_separates_preview_bots_from_phone_browsers():
    assert client_type("facebookexternalhit/1.1") == "link-preview-or-bot"
    assert client_type("Mozilla/5.0 (Linux; Android 15)") == "android-browser"


def test_beacon_captures_request_telemetry_and_redirects(monkeypatch):
    async def no_gemini(*_):
        return None

    async def no_enrichment(*_):
        return None

    analysis_id = asyncio.run(prepare_database())
    monkeypatch.setattr(settings, "canarytoken_url", "https://canarytokens.com/example/token")
    monkeypatch.setattr(settings, "public_api_url", "https://api.nazar.test")
    monkeypatch.setattr(settings, "honeypot_auto_reply_enabled", True)
    monkeypatch.setattr(settings, "honeypot_auto_reply_threshold", 70.0)
    monkeypatch.setattr("app.routers.honeypot.generate_honeypot_reply", no_gemini)
    monkeypatch.setattr("app.routers.honeypot.enrich_telemetry_hit", no_enrichment)
    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            started = client.post(
                "/api/honeypot/start",
                json={"analysis_id": analysis_id, "enable_canary": True},
            )
            assert started.status_code == 200
            session_id = started.json()["id"]
            assert started.json()["canary"]["armed"] is True

            turn = client.post(
                f"/api/honeypot/{session_id}/message",
                json={"content": "Pay now to test@upi"},
            )
            assert turn.status_code == 200
            assert turn.json()["auto_reply"]["allowed"] is True
            reply = turn.json()["messages"][-1]["content"]
            beacon = re.search(r"https://api\.nazar\.test(/api/honeypot/b/[A-Za-z0-9_-]+)", reply)
            assert beacon

            captured = client.get(
                beacon.group(1),
                headers={
                    "X-Forwarded-For": "8.8.8.8",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 15)",
                    "Accept-Language": "en-IN,en;q=0.9",
                    "Referer": "https://web.whatsapp.com/",
                },
                follow_redirects=False,
            )
            assert captured.status_code == 302
            assert captured.headers["location"] == "https://canarytokens.com/example/token"

            session = client.get(f"/api/honeypot/{session_id}").json()
            assert session["telemetry"][0]["ip_address"] == "8.8.8.8"
            assert session["telemetry"][0]["client_type"] == "android-browser"
            assert session["telemetry"][0]["accept_language"].startswith("en-IN")
    finally:
        app.dependency_overrides.clear()


def test_risk_below_30_cannot_arm_telemetry(monkeypatch):
    analysis_id = asyncio.run(prepare_database(29.9))
    monkeypatch.setattr(settings, "canarytoken_url", "https://canarytokens.com/example/token")
    monkeypatch.setattr(settings, "public_api_url", "https://api.nazar.test")
    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/honeypot/start",
                json={"analysis_id": analysis_id, "enable_canary": True},
            )
            assert response.status_code == 200
            assert response.json()["canary"]["armed"] is False
            assert response.json()["intelligence"]["telemetry_policy"]["eligible"] is False
    finally:
        app.dependency_overrides.clear()
