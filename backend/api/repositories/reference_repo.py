"""
Repository for Reference Track data access.

Extends ``BaseRepository`` with methods for querying built-in and
user-added reference tracks, including eager-loading of associated
band metrics.
"""

import logging
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from api.models import ReferenceTrack
from api.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ReferenceRepository(BaseRepository[ReferenceTrack]):
    """Data-access layer for the ``reference_tracks`` table and its children.

    Args:
        session: An active SQLAlchemy ``Session``.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(session, ReferenceTrack)

    def get_all_builtin(self) -> Sequence[ReferenceTrack]:
        """Return all pre-shipped (built-in) reference tracks."""
        stmt = select(ReferenceTrack).where(ReferenceTrack.is_builtin.is_(True))
        result = self._session.execute(stmt)
        return result.scalars().all()

    def get_by_genre(self, genre: str) -> Sequence[ReferenceTrack]:
        """Return reference tracks matching the given genre.

        Args:
            genre: Genre string to filter on.
        """
        stmt = select(ReferenceTrack).where(ReferenceTrack.genre == genre)
        result = self._session.execute(stmt)
        return result.scalars().all()

    def get_with_band_metrics(self, reference_id: str) -> ReferenceTrack | None:
        """Fetch a reference track with its band metrics eagerly loaded.

        Args:
            reference_id: UUID string of the reference track.

        Returns:
            The ``ReferenceTrack`` with ``reference_band_metrics`` populated,
            or ``None``.
        """
        stmt = (
            select(ReferenceTrack)
            .where(ReferenceTrack.id == reference_id)
            .options(joinedload(ReferenceTrack.reference_band_metrics))
        )
        result = self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    def search_by_similarity(self, vector: bytes, top_k: int = 5) -> Sequence[ReferenceTrack]:
        """Stub for future ML-based similarity search.

        Will compare the provided feature vector against stored
        ``similarity_vector`` blobs. Currently returns an empty list.

        Args:
            vector: Feature vector bytes to compare.
            top_k: Number of closest matches to return.

        Returns:
            An empty sequence (not yet implemented).
        """
        logger.warning("search_by_similarity is not yet implemented; returning empty results")
        return []

    def add_user_reference(self, track_data: dict) -> ReferenceTrack:
        """Create a new user-added reference track.

        Args:
            track_data: Dictionary of column values for the new track.
                        Must include at least ``track_name``.

        Returns:
            The persisted ``ReferenceTrack`` instance.
        """
        track = ReferenceTrack(**track_data, is_builtin=False)
        self._session.add(track)
        self._session.flush()
        self._session.refresh(track)
        logger.info("Added user reference track id=%s name=%s", track.id, track.track_name)
        return track
