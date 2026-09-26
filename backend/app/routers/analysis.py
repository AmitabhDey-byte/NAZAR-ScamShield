from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import AnalysisRequest, Transaction
from app.schemas import AnalysisResponse, FullAnalyzeRequest, MessageAnalyzeRequest, TransactionContext, UrlAnalyzeRequest
from app.services.analyzer import transaction_analysis
from app.services.intelligence import record_indicators
from app.services.pipeline import analyze_pipeline
from app.services.realtime import broker


router = APIRouter(prefix="/api/analyze", tags=["analysis"])


async def persist(result: dict, source_type: str, text: str, session: AsyncSession) -> AnalysisResponse:
    row = AnalysisRequest(
        id=result["id"], source_type=source_type, input_text=text, score=result["score"],
        classification=result["classification"], category=result["category"], reasons=result["reasons"],
        entities=result["entities"], component_scores=result["component_scores"],
        recommended_action=result["recommended_action"], ai_provider=result.get("ai_provider"),
        ai_model=result.get("ai_model"), ai_summary=result.get("ai_summary"),
        ai_confidence=result.get("ai_confidence"), created_at=result["created_at"],
    )
    session.add(row)
    await record_indicators(session, result["entities"], result["score"])
    await session.commit()
    response = AnalysisResponse.model_validate(row)
    await broker.publish("analysis.created", {"id": row.id, "source": source_type, "score": row.score, "classification": row.classification, "category": row.category})
    return response


@router.post("/message")
async def analyze_message(payload: MessageAnalyzeRequest, session: AsyncSession = Depends(get_session)):
    return await analyze_pipeline(payload.text, db=session)


@router.post("/url")
async def analyze_url(payload: UrlAnalyzeRequest, session: AsyncSession = Depends(get_session)):
    return await analyze_pipeline(payload.url, explicit_url=payload.url, db=session)


@router.post("/transaction")
async def analyze_transaction(payload: TransactionContext, session: AsyncSession = Depends(get_session)):
    score, reasons = transaction_analysis(payload)
    session.add(Transaction(**payload.model_dump(), anomaly_score=score))
    await session.commit()
    return {"score": score, "classification": "DANGEROUS" if score >= 70 else "SUSPICIOUS" if score >= 35 else "SAFE", "reasons": reasons}


@router.post("/full", response_model=AnalysisResponse)
async def analyze_full(payload: FullAnalyzeRequest, session: AsyncSession = Depends(get_session)):
    result = await analyze_pipeline(payload.text, payload.url, payload.transaction, session)
    return await persist(result, "full", payload.text, session)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str, session: AsyncSession = Depends(get_session)):
    row = await session.get(AnalysisRequest, analysis_id)
    if not row:
        raise HTTPException(404, "Analysis not found")
    return AnalysisResponse.model_validate(row)
