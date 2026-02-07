"""
Tests for the FastAPI HTTP endpoints.

Uses the FastAPI TestClient for synchronous request testing.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.database import get_session_dependency
from api.main import app
from api.models import Base


@pytest.fixture(scope="module")
def test_engine():
    """Create a module-scoped in-memory SQLite engine."""
    eng = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture(scope="module")
def test_session_factory(test_engine):
    """Create a session factory bound to the test engine."""
    return sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest.fixture(scope="module")
def client(test_session_factory):
    """FastAPI TestClient with overridden database dependency."""

    def _override_session():
        session = test_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_session_dependency] = _override_session
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.json() == {"status": "ok"}


class TestAnalyzeEndpoint:

    def test_analyze_accepts_file(self, client):
        response = client.post(
            "/api/analyze",
            files={"file": ("test.wav", b"fake wav content", "audio/wav")},
            data={"genre": "rock", "recommendation_level": "suggestive"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["file_name"] == "test.wav"
        assert data["genre"] == "rock"

    def test_analyze_default_recommendation_level(self, client):
        response = client.post(
            "/api/analyze",
            files={"file": ("test.wav", b"content", "audio/wav")},
        )
        assert response.status_code == 200
        assert response.json()["recommendation_level"] == "suggestive"


class TestAnalysisRetrievalEndpoint:

    def test_get_analysis_not_found(self, client):
        response = client.get("/api/analysis/nonexistent-uuid")
        assert response.status_code == 404

    def test_get_analysis_returns_404_detail(self, client):
        response = client.get("/api/analysis/00000000-0000-0000-0000-000000000000")
        assert response.json()["detail"] == "Analysis not found"


class TestReferencesEndpoint:

    def test_list_references_returns_200(self, client):
        response = client.get("/api/references")
        assert response.status_code == 200

    def test_list_references_returns_list(self, client):
        response = client.get("/api/references")
        assert isinstance(response.json(), list)

    def test_list_references_genre_filter(self, client):
        response = client.get("/api/references", params={"genre": "rock"})
        assert response.status_code == 200
        assert isinstance(response.json(), list)
