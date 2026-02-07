from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.models import Analysis
from api.repositories.base import BaseRepository


class AnalysisRepository(BaseRepository[Analysis]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Analysis)

    async def get_with_relations(self, analysis_id: int) -> Analysis | None:
        stmt = (
            select(Analysis)
            .where(Analysis.id == analysis_id)
            .options(
                selectinload(Analysis.per_band_metrics),
                selectinload(Analysis.detailed_metrics),
                selectinload(Analysis.reference_matches),
                selectinload(Analysis.recommendations),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_genre(self, genre: str) -> Sequence[Analysis]:
        stmt = select(Analysis).where(Analysis.genre == genre)
        result = await self._session.execute(stmt)
        return result.scalars().all()
