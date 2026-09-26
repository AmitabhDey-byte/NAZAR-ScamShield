from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import AnalysisRequest, Campaign, CampaignIndicator, Device, ScamReport, ThreatEdge, ThreatIndicator


router = APIRouter(prefix="/api", tags=["intelligence"])


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_session)):
    now = datetime.now(timezone.utc)
    analyzed = int(await db.scalar(select(func.count(AnalysisRequest.id))) or 0)
    dangerous = int(await db.scalar(select(func.count(AnalysisRequest.id)).where(AnalysisRequest.classification == "DANGEROUS")) or 0)
    campaigns = int(await db.scalar(select(func.count(Campaign.id)).where(Campaign.status != "closed")) or 0)
    indicators = int(await db.scalar(select(func.count(ThreatIndicator.id))) or 0)
    report_count = int(await db.scalar(select(func.count(ScamReport.id))) or 0)
    devices = (await db.scalars(select(Device))).all()
    online_cutoff = now - timedelta(minutes=2)
    online_devices = sum(1 for device in devices if (device.last_seen.replace(tzinfo=timezone.utc) if device.last_seen.tzinfo is None else device.last_seen) >= online_cutoff)
    recent = (await db.scalars(select(AnalysisRequest).order_by(AnalysisRequest.created_at.desc()).limit(6))).all()
    category_rows = (await db.execute(
        select(AnalysisRequest.category, func.count(AnalysisRequest.id))
        .group_by(AnalysisRequest.category)
        .order_by(func.count(AnalysisRequest.id).desc())
    )).all()
    seven_days_ago = now - timedelta(days=6)
    timeline_rows = (await db.scalars(
        select(AnalysisRequest).where(AnalysisRequest.created_at >= seven_days_ago).order_by(AnalysisRequest.created_at)
    )).all()
    by_day: dict[str, int] = {}
    for row in timeline_rows:
        timestamp = row.created_at.replace(tzinfo=timezone.utc) if row.created_at.tzinfo is None else row.created_at
        by_day[timestamp.date().isoformat()] = by_day.get(timestamp.date().isoformat(), 0) + 1
    timeline = []
    for offset in range(6, -1, -1):
        day = (now - timedelta(days=offset)).date()
        timeline.append({"day": day.strftime("%a"), "date": day.isoformat(), "signals": by_day.get(day.isoformat(), 0)})
    top_campaign = await db.scalar(select(Campaign).order_by(Campaign.report_count.desc(), Campaign.updated_at.desc()).limit(1))
    top_indicators: list[ThreatIndicator] = []
    if top_campaign:
        ids = (await db.scalars(select(CampaignIndicator.indicator_id).where(CampaignIndicator.campaign_id == top_campaign.id))).all()
        if ids:
            top_indicators = list((await db.scalars(
                select(ThreatIndicator).where(ThreatIndicator.id.in_(ids)).order_by(ThreatIndicator.report_count.desc()).limit(3)
            )).all())
    return {
        "metrics": {
            "threats_analyzed": analyzed,
            "dangerous_scams": dangerous,
            "active_campaigns": campaigns,
            "indicators_collected": indicators,
            "community_reports": report_count,
            "paired_devices": len(devices),
            "online_devices": online_devices,
        },
        "category_distribution": [{"name": category or "unknown", "value": int(count)} for category, count in category_rows],
        "reports_over_time": timeline,
        "recent": [
            {"id": row.id, "source_type": row.source_type, "category": row.category, "score": row.score,
             "classification": row.classification, "ai_provider": row.ai_provider, "created_at": row.created_at}
            for row in recent
        ],
        "top_campaign": None if not top_campaign else {
            "id": top_campaign.id, "name": top_campaign.name, "scam_type": top_campaign.scam_type,
            "status": top_campaign.status, "report_count": top_campaign.report_count,
            "summary": top_campaign.summary,
            "indicators": [
                {"id": item.id, "type": item.type, "value": item.value, "reports": item.report_count, "observations": item.observation_count}
                for item in top_indicators
            ],
        },
        "generated_at": now,
    }


@router.get("/campaigns")
async def campaigns(db: AsyncSession = Depends(get_session)):
    rows = (await db.scalars(select(Campaign).order_by(Campaign.report_count.desc()))).all()
    return [
        {"id": row.id, "name": row.name, "scam_type": row.scam_type, "status": row.status, "report_count": row.report_count,
         "fingerprint": row.fingerprint, "summary": row.summary, "updated_at": row.updated_at}
        for row in rows
    ]


@router.get("/campaigns/{campaign_id}")
async def campaign(campaign_id: str, db: AsyncSession = Depends(get_session)):
    row = await db.get(Campaign, campaign_id)
    if not row:
        raise HTTPException(404, "Campaign not found")
    ids = (await db.scalars(select(CampaignIndicator.indicator_id).where(CampaignIndicator.campaign_id == campaign_id))).all()
    indicators = (await db.scalars(select(ThreatIndicator).where(ThreatIndicator.id.in_(ids)))).all() if ids else []
    return {
        "id": row.id, "name": row.name, "scam_type": row.scam_type, "status": row.status,
        "report_count": row.report_count, "fingerprint": row.fingerprint, "summary": row.summary,
        "indicators": [{"id": item.id, "type": item.type, "value": item.value, "risk_score": item.risk_score, "report_count": item.report_count} for item in indicators],
    }


@router.get("/intelligence/graph")
async def graph(db: AsyncSession = Depends(get_session)):
    nodes = (await db.scalars(select(ThreatIndicator))).all()
    edges = (await db.scalars(select(ThreatEdge))).all()
    campaigns = (await db.scalars(select(Campaign))).all()
    campaign_links = (await db.scalars(select(CampaignIndicator))).all()
    graph_nodes = [{"id": n.id, "type": n.type, "label": n.value, "risk": n.risk_score, "reports": n.report_count} for n in nodes]
    graph_nodes += [{"id": c.id, "type": "CAMPAIGN", "label": c.name, "risk": 90, "reports": c.report_count} for c in campaigns]
    graph_edges = [{"source": e.source_id, "target": e.target_id, "type": e.edge_type, "confidence": e.confidence} for e in edges]
    graph_edges += [{"source": link.indicator_id, "target": link.campaign_id, "type": "BELONGS_TO_CAMPAIGN", "confidence": link.confidence} for link in campaign_links]
    return {"nodes": graph_nodes, "edges": graph_edges}
