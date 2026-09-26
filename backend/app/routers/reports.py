from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import ScamReport
from app.schemas import ReportCreate
from app.services.intelligence import record_confirmed_campaign, record_indicators
from app.services.pipeline import analyze_pipeline
from app.services.realtime import broker


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("")
async def create_report(payload: ReportCreate, session: AsyncSession = Depends(get_session)):
    row = ScamReport(**payload.model_dump())
    session.add(row)
    combined = " ".join(filter(None, [payload.message, payload.phone_number, payload.upi_id, payload.url]))
    result = await analyze_pipeline(combined, payload.url)
    indicators = await record_indicators(session, result["entities"], result["score"], confirmed_report=True)
    campaign = await record_confirmed_campaign(session, payload.scam_category or result["category"], result["entities"], indicators)
    await session.commit()
    await broker.publish("report.created", {"report_id": row.id, "campaign_id": campaign.id, "score": result["score"]})
    return {"id": row.id, "campaign_id": campaign.id, "status": "received", "message": "Report added to community intelligence"}


@router.get("")
async def list_reports(session: AsyncSession = Depends(get_session)):
    rows = (await session.scalars(select(ScamReport).order_by(ScamReport.created_at.desc()).limit(50))).all()
    return [{"id": row.id, "category": row.scam_category, "message": row.message, "created_at": row.created_at} for row in rows]
