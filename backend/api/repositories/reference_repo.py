"""
Repository for Reference Track data access.

Extends ``BaseRepository`` with methods for querying built-in and
user-added reference tracks, including eager-loading of associated
band metrics and similarity search.
"""

import logging
from typing import List, Sequence, Tuple

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from api.models import ReferenceOverallMetrics, ReferenceTrack
from api.repositories.base import BaseRepository
from ml.similarity import SimilarityMatcher, deserialize_vector

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

    def get_with_all_metrics(self, reference_id: str) -> ReferenceTrack | None:
        """Fetch a reference track with both band and overall metrics eagerly loaded.

        Args:
            reference_id: UUID string of the reference track.

        Returns:
            The ``ReferenceTrack`` with ``reference_band_metrics`` and
            ``reference_overall_metrics`` populated, or ``None``.
        """
        stmt = (
            select(ReferenceTrack)
            .where(ReferenceTrack.id == reference_id)
            .options(
                joinedload(ReferenceTrack.reference_band_metrics),
                joinedload(ReferenceTrack.reference_overall_metrics),
            )
        )
        result = self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    def search_by_similarity(
        self,
        user_vector: np.ndarray,
        top_k: int = 10,
        genre_filter: str | None = None,
    ) -> List[Tuple[ReferenceTrack, float]]:
        """Find the most similar reference tracks to the given feature vector.

        Loads all reference tracks with stored similarity vectors, computes
        cosine similarity against the user vector, and returns the top-K
        matches sorted by similarity score.

        Args:
            user_vector: 128-dimensional feature vector from user analysis.
            top_k: Number of closest matches to return.
            genre_filter: Optional genre string to restrict search.

        Returns:
            List of (ReferenceTrack, similarity_score) tuples sorted by
            score descending.
        """
        stmt = select(ReferenceTrack).where(
            ReferenceTrack.similarity_vector.isnot(None)
        )
        if genre_filter:
            stmt = stmt.where(ReferenceTrack.genre == genre_filter)

        result = self._session.execute(stmt)
        tracks = result.scalars().all()

        # Build (id, vector) pairs for the matcher
        reference_vectors: List[Tuple[str, np.ndarray]] = []
        track_map = {}
        for track in tracks:
            try:
                vec = deserialize_vector(track.similarity_vector)
                reference_vectors.append((track.id, vec))
                track_map[track.id] = track
            except Exception:
                logger.warning(
                    "Failed to deserialize vector for reference %s", track.id
                )
                continue

        matcher = SimilarityMatcher()
        matches = matcher.find_similar_references(user_vector, reference_vectors, top_k)

        return [(track_map[ref_id], score) for ref_id, score in matches if ref_id in track_map]

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
