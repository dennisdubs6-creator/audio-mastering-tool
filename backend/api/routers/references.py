"""
Reference Track API endpoints.

- ``GET /api/references`` – List all reference tracks, with optional genre filter.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.database import get_session_dependency
from api.repositories.reference_repo import ReferenceRepository
from api.schemas import ReferenceTrackResponse

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
