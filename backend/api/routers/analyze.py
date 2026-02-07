"""
Analysis API endpoints.

- ``POST /api/analyze`` – Submit a WAV file for mastering analysis (stub).
- ``GET /api/analysis/{analysis_id}`` – Retrieve analysis results by UUID.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from api.database import get_session_dependency
from api.repositories.analysis_repo import AnalysisRepository
from api.schemas import AnalysisResponse

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze")
def create_analysis(
    file: UploadFile = File(...),
    genre: str | None = Form(None),
    recommendation_level: str = Form("suggestive"),
    session: Session = Depends(get_session_dependency),
) -> dict:
    """Submit a WAV file for audio mastering analysis.

    Currently returns a stub response with a generated UUID. The full
    DSP analysis pipeline will be connected in a future ticket.
    """
    _ = AnalysisRepository(session)
    analysis_id = str(uuid.uuid4())
    return {
        "id": analysis_id,
        "message": "Analysis endpoint stub – DSP pipeline not yet implemented",
        "file_name": file.filename,
        "genre": genre,
        "recommendation_level": recommendation_level,
    }


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: str,
    session: Session = Depends(get_session_dependency),
) -> AnalysisResponse:
    """Retrieve analysis results by UUID.

    Returns the analysis record with band metrics, overall metrics,
    and recommendations eagerly loaded.

    Raises:
        HTTPException: 404 if no analysis exists with the given ID.
    """
    repo = AnalysisRepository(session)
    analysis = repo.get_with_metrics(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return AnalysisResponse.model_validate(analysis)
