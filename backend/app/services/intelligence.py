from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Campaign, CampaignIndicator, ThreatIndicator


def _normalize(kind: str, value: str) -> str:
    value = value.strip()
    if kind == "PHONE":
        return re.sub(r"[^+\d]", "", value)
    if kind == "DOMAIN":
        parsed = urlparse(value if "://" in value else f"https://{value}")
        return (parsed.hostname or value).lower()
    return value.lower() if kind == "UPI" else value


def entity_candidates(entities: dict) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    candidates += [("PHONE", str(value)) for value in entities.get("phone_numbers", [])]
    candidates += [("UPI", str(value)) for value in entities.get("upi_ids", [])]
    candidates += [("DOMAIN", str(value)) for value in entities.get("urls", [])]
    candidates += [("CLAIMED_ORGANIZATION", str(value)) for value in entities.get("claimed_organizations", [])]
    unique: dict[tuple[str, str], tuple[str, str]] = {}
    for kind, value in candidates:
        normalized = _normalize(kind, value)
        if normalized:
            unique[(kind, normalized)] = (kind, normalized)
    return list(unique.values())


async def record_indicators(
    db: AsyncSession,
    entities: dict,
    risk_score: float,
    *,
    confirmed_report: bool = False,
) -> list[ThreatIndicator]:
    now = datetime.now(timezone.utc)
    rows: list[ThreatIndicator] = []
    for kind, value in entity_candidates(entities):
        row = await db.scalar(select(ThreatIndicator).where(ThreatIndicator.type == kind, ThreatIndicator.value == value))
        if row:
            row.last_seen = now
            row.observation_count += 1
            row.risk_score = round(max(row.risk_score, risk_score), 1)
            if confirmed_report:
                row.report_count += 1
        else:
            row = ThreatIndicator(
                type=kind,
                value=value,
                risk_score=round(risk_score, 1),
                report_count=1 if confirmed_report else 0,
                observation_count=1,
                first_seen=now,
                last_seen=now,
            )
            db.add(row)
            await db.flush()
        rows.append(row)
    return rows


def campaign_name(category: str) -> str:
    return f"{category.replace('_', ' ').title()} cluster"


async def record_confirmed_campaign(
    db: AsyncSession,
    category: str,
    entities: dict,
    indicators: list[ThreatIndicator],
) -> Campaign:
    campaign_id = f"cluster-{re.sub(r'[^a-z0-9]+', '-', category.lower()).strip('-')}"
    campaign = await db.get(Campaign, campaign_id)
    if campaign:
        campaign.report_count += 1
        campaign.updated_at = datetime.now(timezone.utc)
    else:
        campaign = Campaign(
            id=campaign_id,
            name=campaign_name(category),
            scam_type=category,
            status="emerging",
            report_count=1,
            summary="Built from real community submissions. Review indicators before escalation.",
            fingerprint={
                "tactics": entities.get("tactics", []),
                "claimed_organizations": entities.get("claimed_organizations", []),
                "source": "community_reports",
            },
        )
        db.add(campaign)
        await db.flush()
    for indicator in indicators:
        linked = await db.scalar(
            select(CampaignIndicator).where(
                CampaignIndicator.campaign_id == campaign.id,
                CampaignIndicator.indicator_id == indicator.id,
            )
        )
        if not linked:
            db.add(CampaignIndicator(campaign_id=campaign.id, indicator_id=indicator.id, confidence=0.75))
    return campaign
