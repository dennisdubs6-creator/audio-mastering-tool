"""
Shared pytest fixtures for the Audio Mastering Tool backend test suite.

Provides an in-memory SQLite database, a scoped session, and sample
data factories used across multiple test modules.
"""

import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from api.models import (
    Analysis,
    BandMetrics,
    Base,
    OverallMetrics,
    ReferenceTrack,
    ReferenceBandMetrics,
    Recommendation,
    UserSettings,
)


@pytest.fixture(scope="session")
def engine():
    """Create a shared in-memory SQLite engine for the entire test session."""
    eng = create_engine("sqlite:///:memory:", echo=False)

    def _set_sqlite_pragma(dbapi_conn, connection_record):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    event.listen(eng, "connect", _set_sqlite_pragma)
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def session(engine):
    """Provide a transactional session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    sess = sessionmaker(bind=connection, expire_on_commit=False)()

    yield sess

    sess.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def sample_analysis() -> dict:
    """Return a dictionary of valid Analysis column values."""
    return {
        "id": str(uuid.uuid4()),
        "file_path": "/tmp/test.wav",
        "file_name": "test.wav",
        "file_size": 1024000,
        "sample_rate": 44100,
        "bit_depth": 16,
        "duration_seconds": 180.5,
        "genre": "rock",
        "genre_confidence": 0.92,
        "recommendation_level": "suggestive",
        "analysis_engine_version": "0.1.0",
    }


@pytest.fixture()
def sample_band_metrics(sample_analysis) -> list[dict]:
    """Return a list of band metric dictionaries for each frequency band."""
    bands = [
        ("low", 20, 200),
        ("low_mid", 200, 500),
        ("mid", 500, 2000),
        ("high_mid", 2000, 6000),
        ("high", 6000, 20000),
    ]
    return [
        {
            "id": str(uuid.uuid4()),
            "analysis_id": sample_analysis["id"],
            "band_name": name,
            "freq_min": fmin,
            "freq_max": fmax,
            "band_rms_dbfs": -18.0,
            "dynamic_range_db": 12.0,
            "stereo_width_percent": 75.0,
        }
        for name, fmin, fmax in bands
    ]


@pytest.fixture()
def sample_reference_track() -> dict:
    """Return a dictionary of valid ReferenceTrack column values."""
    return {
        "id": str(uuid.uuid4()),
        "track_name": "Test Reference",
        "artist": "Test Artist",
        "genre": "rock",
        "year": 2023,
        "is_builtin": True,
    }
