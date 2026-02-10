"""
Repository for Analysis-related data access.

Extends ``BaseRepository`` with methods that eagerly load associated
band metrics, overall metrics, and recommendations.
"""

import logging
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from api.models import Analysis, BandMetrics, OverallMetrics
from api.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class AnalysisRepository(BaseRepository[Analysis]):
    """Data-access layer for the ``analysis`` table and its children.

    Args:
        session: An active SQLAlchemy ``Session``.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(session, Analysis)

    def get_with_metrics(self, analysis_id: str) -> Analysis | None:
        """Fetch an analysis with its band_metrics and overall_metrics eagerly loaded.

        Args:
            analysis_id: UUID string of the analysis.

        Returns:
            The ``Analysis`` instance with relationships populated, or ``None``.
        """
        stmt = (
            select(Analysis)
            .where(Analysis.id == analysis_id)
            .options(
                joinedload(Analysis.band_metrics),
                joinedload(Analysis.overall_metrics),
            )
        )
        result = self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    def get_with_recommendations(self, analysis_id: str) -> Analysis | None:
        """Fetch an analysis with its recommendations eagerly loaded.

        Args:
            analysis_id: UUID string of the analysis.

        Returns:
            The ``Analysis`` instance with recommendations populated, or ``None``.
        """
        stmt = (
            select(Analysis)
            .where(Analysis.id == analysis_id)
            .options(joinedload(Analysis.recommendations))
        )
        result = self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    def save_complete_analysis(
        self,
        analysis: Analysis,
        band_metrics: list[BandMetrics],
        overall_metrics: OverallMetrics,
    ) -> Analysis:
        """Persist an analysis together with its metrics in a single transaction.

        Args:
            analysis: The parent ``Analysis`` instance.
            band_metrics: List of ``BandMetrics`` rows to associate.
            overall_metrics: The ``OverallMetrics`` row to associate.

        Returns:
            The saved ``Analysis`` with children attached.
        """
        self._session.add(analysis)
        self._session.flush()

        for bm in band_metrics:
            bm.analysis_id = analysis.id
            self._session.add(bm)

        overall_metrics.analysis_id = analysis.id
        self._session.add(overall_metrics)

        self._session.flush()
        self._session.refresh(analysis)
        logger.info("Saved complete analysis id=%s with %d band metrics", analysis.id, len(band_metrics))
        return analysis

    def update_status(self, analysis_id: str, status: str) -> None:
        """Update the status field of an analysis record.

        Args:
            analysis_id: UUID string of the analysis.
            status: New status value (pending, processing, completed, failed).
        """
        analysis = self._session.get(Analysis, analysis_id)
        if analysis is not None:
            analysis.status = status
            self._session.commit()

    def get_by_genre(self, genre: str) -> Sequence[Analysis]:
        """Return all analyses matching the given genre.

        Args:
            genre: Genre string to filter on.
        """
        stmt = select(Analysis).where(Analysis.genre == genre)
        result = self._session.execute(stmt)
        return result.scalars().all()

    def get_recent(self, limit: int = 10) -> Sequence[Analysis]:
        """Return the most recent analyses ordered by creation date.

        Args:
            limit: Maximum number of results (default 10).
        """
        stmt = select(Analysis).order_by(Analysis.created_at.desc()).limit(limit)
        result = self._session.execute(stmt)
        return result.scalars().all()
