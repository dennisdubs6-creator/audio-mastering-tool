"""
Reference Track API endpoints.

- ``GET /api/references`` – List all reference tracks, with optional genre filter.
- ``POST /api/similarity/{analysis_id}`` – Find similar reference tracks for an analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_session_dependency
from api.repositories.analysis_repo import AnalysisRepository
from api.repositories.reference_repo import ReferenceRepository
from api.schemas import (
    ReferenceTrackResponse,
    SimilarityMatchResponse,
    SimilaritySearchResponse,
)
from ml.feature_extraction import FeatureExtractor

router = APIRouter(prefix="/api", tags=["references"])


@router.get("/references", response_model=list[ReferenceTrackResponse])
def list_references(
    genre: str | None = Query(None, description="Filter reference tracks by genre"),
    session: Session = Depends(get_session_dependency),
) -> list[ReferenceTrackResponse]:
    """List all available reference tracks.

    Optionally filter by genre via the ``genre`` query parameter.
    """
    repo = ReferenceRepository(session)
    if genre:
        tracks = repo.get_by_genre(genre)
    else:
        tracks = repo.get_all()
    return [ReferenceTrackResponse.model_validate(t) for t in tracks]


@router.post(
    "/similarity/{analysis_id}",
    response_model=SimilaritySearchResponse,
    tags=["similarity"],
)
def search_similar_references(
    analysis_id: str,
    genre: str | None = Query(None, description="Filter references by genre"),
    top_k: int = Query(10, ge=1, le=50, description="Number of matches to return"),
    session: Session = Depends(get_session_dependency),
) -> SimilaritySearchResponse:
    """Find reference tracks most similar to the given analysis.

    Extracts a feature vector from the analysis metrics and compares
    it against all stored reference track vectors using cosine similarity.

    Args:
        analysis_id: UUID of the analysis to compare against.
        genre: Optional genre filter for reference tracks.
        top_k: Number of top matches to return (default 10, max 50).

    Returns:
        Top matches sorted by similarity score (descending).

    Raises:
        404: Analysis not found.
        400: Analysis is incomplete (missing metrics).
    """
    analysis_repo = AnalysisRepository(session)
    analysis = analysis_repo.get_with_metrics(analysis_id)

    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if not analysis.band_metrics or analysis.overall_metrics is None:
        raise HTTPException(
            status_code=400,
            detail="Analysis is incomplete: missing band metrics or overall metrics",
        )

    extractor = FeatureExtractor()
    user_vector = extractor.extract_from_metrics(
        analysis.band_metrics, analysis.overall_metrics
    )

    ref_repo = ReferenceRepository(session)
    matches = ref_repo.search_by_similarity(
        user_vector=user_vector,
        top_k=top_k,
        genre_filter=genre,
    )

    match_responses = [
        SimilarityMatchResponse(
            reference_id=track.id,
            track_name=track.track_name,
            artist=track.artist,
            genre=track.genre,
            year=track.year,
            similarity_score=round(max(0.0, min(1.0, score)), 4),
        )
        for track, score in matches
    ]

    return SimilaritySearchResponse(matches=match_responses)
