"""
Synchronous SQLAlchemy database engine and session management.

Provides ``init_db()`` to create all tables and ``get_session()`` as a
context-manager that yields a scoped session with automatic commit /
rollback semantics.
"""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from api.core.config import settings
from api.models import Base, UserSettings

logger = logging.getLogger(__name__)

_SQLITE_PREFIX = "sqlite:///"


def _ensure_db_directory() -> None:
    """Create the database directory under ~/.audio-mastering-tool/ if needed."""
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        if url.startswith(_SQLITE_PREFIX):
            db_path = Path(url[len(_SQLITE_PREFIX):]).expanduser()
            db_path.parent.mkdir(parents=True, exist_ok=True)


engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False},
)


def _set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key enforcement for SQLite connections."""
    dbapi_conn.execute("PRAGMA foreign_keys=ON")


event.listen(engine, "connect", _set_sqlite_pragma)

SessionFactory = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


def _insert_default_settings(session: Session) -> None:
    """Seed the user_settings table with default values if empty."""
    existing = session.query(UserSettings).first()
    if existing is not None:
        return

    defaults = [
        UserSettings(key="recommendation_level", value="suggestive"),
        UserSettings(key="default_genre", value=""),
        UserSettings(key="theme", value="dark"),
    ]
    session.add_all(defaults)
    session.commit()
    logger.info("Inserted default user settings")


def init_db() -> None:
    """Create all tables and seed default data.

    Call this once at application startup. Safe to call multiple times -
    ``create_all`` is a no-op when tables already exist.
    """
    _ensure_db_directory()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified")

    with SessionFactory() as session:
        _insert_default_settings(session)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional session scope.

    Usage::

        with get_session() as session:
            session.add(entity)
            # auto-committed on clean exit, rolled back on exception

    Yields:
        A SQLAlchemy ``Session`` instance.
    """
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session_dependency() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    Used with ``Depends(get_session_dependency)`` in route handlers.
    """
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
