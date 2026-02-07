from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.core.config import settings
from api.models import Base


def _ensure_db_directory() -> None:
    """Create the database directory under ~/.audio-mastering-tool/ if needed."""
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        # Extract the file path after 'sqlite+aiosqlite:///'
        prefix = "sqlite+aiosqlite:///"
        if url.startswith(prefix):
            db_path = Path(url[len(prefix):]).expanduser()
            db_path.parent.mkdir(parents=True, exist_ok=True)


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    _ensure_db_directory()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        async with session.begin():
            yield session
