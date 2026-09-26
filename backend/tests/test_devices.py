import asyncio

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_session
from app.main import app


engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def prepare_database() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def override_session():
    async with Session() as session:
        yield session


def test_phone_pairing_and_event_sync():
    asyncio.run(prepare_database())
    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            pair_response = client.post(
                "/api/devices/pair-code",
                headers={"X-Forwarded-Host": "nazar.example", "X-Forwarded-Proto": "https"},
            ).json()
            assert pair_response["api_url"] == "https://nazar.example"
            pair_code = pair_response["code"]
            paired = client.post(
                "/api/devices/register",
                json={"pair_code": pair_code, "device_name": "Test phone", "platform": "android", "app_version": "1.0.0"},
            )
            assert paired.status_code == 200
            payload = paired.json()
            device_id = payload["device"]["id"]
            headers = {"X-Device-Token": payload["device_token"]}

            event = client.post(
                f"/api/devices/{device_id}/events",
                headers=headers,
                json={
                    "text": "Your electricity connection will be disconnected tonight. Pay ₹4980 immediately at ramesh123@oksbi using https://electric-bill-secure.xyz",
                    "source_package": "expo-go",
                    "source_label": "Clipboard scan",
                },
            )
            assert event.status_code == 200
            assert event.json()["analysis"]["classification"] == "DANGEROUS"

            timeline = client.get(f"/api/devices/{device_id}/events", headers=headers)
            assert timeline.status_code == 200
            assert timeline.json()[0]["source_label"] == "Clipboard scan"

            blocked = client.post(
                f"/api/devices/{device_id}/events",
                headers=headers,
                json={"text": "Your one time password is 123456", "source_label": "Notification"},
            )
            assert blocked.status_code == 422
    finally:
        app.dependency_overrides.clear()
