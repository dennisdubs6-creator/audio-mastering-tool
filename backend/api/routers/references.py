from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_session
from api.models import ReferenceTrack

router = APIRouter(prefix="/api", tags=["references"])


@router.get("/references")
async def list_references(
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """List all available reference tracks."""
    result = await session.execute(select(ReferenceTrack))
    tracks = result.scalars().all()
    return [
        {
            "id": t.id,
            "track_name": t.track_name,
            "genre": t.genre,
            "artist": t.artist,
        }
        for t in tracks
    ]
