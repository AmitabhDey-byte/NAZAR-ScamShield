from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import init_db
from app.routers import analysis, calls, devices, honeypot, intelligence, integrations, model, realtime, reports


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Explainable scam-risk analysis and defensive threat intelligence.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
for api_router in [analysis.router, reports.router, honeypot.router, intelligence.router, model.router, calls.router, devices.router, realtime.router, integrations.router]:
    app.include_router(api_router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "database": settings.database_label,
        "gemini": "connected" if settings.gemini_api_key else "not-configured",
        "gemini_model": settings.gemini_model if settings.gemini_api_key else None,
        "realtime": "sse",
        "integrations": {
            "n8n_gmail": "configured" if settings.n8n_webhook_secret else "not-configured",
            "n8n_twilio": "configured" if settings.n8n_webhook_secret else "not-configured",
        },
    }
