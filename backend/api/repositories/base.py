"""
Generic base repository providing synchronous CRUD operations.

All concrete repositories extend ``BaseRepository[ModelT]`` to inherit
``get_by_id``, ``get_all``, ``create``, ``update``, and ``delete``.
"""

import logging
from typing import Generic, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models import Base

ModelT = TypeVar("ModelT", bound=Base)
logger = logging.getLogger(__name__)


class BaseRepository(Generic[ModelT]):
    """Synchronous generic repository for SQLAlchemy models.

    Args:
        session: An active SQLAlchemy ``Session``.
        model: The ORM model class this repository manages.
    """

    def __init__(self, session: Session, model: Type[ModelT]) -> None:
        self._session = session
        self._model = model

    def get_by_id(self, entity_id: str) -> ModelT | None:
        """Return a single entity by its primary key, or ``None``.

        Args:
            entity_id: UUID string primary key.
        """
        return self._session.get(self._model, entity_id)

    def get_all(self) -> Sequence[ModelT]:
        """Return every row for the managed model."""
        result = self._session.execute(select(self._model))
        return result.scalars().all()

    def create(self, entity: ModelT) -> ModelT:
        """Add a new entity to the session and flush to obtain defaults.

        Args:
            entity: A model instance (unsaved).

        Returns:
            The same instance after flush, with server-side defaults populated.
        """
        self._session.add(entity)
        self._session.flush()
        self._session.refresh(entity)
        logger.debug("Created %s id=%s", self._model.__tablename__, getattr(entity, "id", "?"))
        return entity

    def update(self, entity: ModelT) -> ModelT:
        """Merge changes for an existing entity and flush.

        Args:
            entity: A model instance with updated attributes.

        Returns:
            The merged instance.
        """
        merged = self._session.merge(entity)
        self._session.flush()
        logger.debug("Updated %s id=%s", self._model.__tablename__, getattr(merged, "id", "?"))
        return merged

    def delete(self, entity: ModelT) -> None:
        """Remove an entity from the database.

        Args:
            entity: The model instance to delete.
        """
        self._session.delete(entity)
        self._session.flush()
        logger.debug("Deleted %s id=%s", self._model.__tablename__, getattr(entity, "id", "?"))
