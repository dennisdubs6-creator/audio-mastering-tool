from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_session
from api.repositories.analysis_repo import AnalysisRepository

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze")
async def create_analysis(
    file: UploadFile = File(...),
    genre: str | None = Form(None),
    recommendation_level: str = Form("suggestive"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Submit a WAV file for audio mastering analysis."""
    # TODO: Implement DSP analysis pipeline (T2/T4)
    _ = AnalysisRepository(session)
    return {
        "message": "Analysis endpoint stub",
        "file_name": file.filename,
        "genre": genre,
        "recommendation_level": recommendation_level,
    }


@router.get("/analysis/{analysis_id}")
async def get_analysis(
    analysis_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Retrieve analysis results by ID."""
    repo = AnalysisRepository(session)
    analysis = await repo.get_with_relations(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {
        "id": analysis.id,
        "file_name": analysis.file_name,
        "genre": analysis.genre,
        "recommendation_level": analysis.recommendation_level,
        "upload_timestamp": analysis.upload_timestamp.isoformat(),
    }
