from typing import Generic, TypeVar, Type, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession, model: Type[ModelT]) -> None:
        self._session = session
        self._model = model

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        return await self._session.get(self._model, entity_id)

    async def get_all(self) -> Sequence[ModelT]:
        result = await self._session.execute(select(self._model))
        return result.scalars().all()

    async def create(self, entity: ModelT) -> ModelT:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self._session.delete(entity)
        await self._session.flush()
