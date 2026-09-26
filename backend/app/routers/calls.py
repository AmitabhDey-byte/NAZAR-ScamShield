from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.routers.analysis import persist
from app.schemas import AnalysisResponse, CallAnalyzeRequest
from app.services.pipeline import analyze_pipeline

router = APIRouter(prefix="/api/calls", tags=["calls"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_call(payload: CallAnalyzeRequest, db: AsyncSession = Depends(get_session)):
    text = f"Caller: {payload.caller_number or 'unknown'}\n{payload.transcript}"
    result = await analyze_pipeline(text, db=db)
    return await persist(result, "call", text, db)
