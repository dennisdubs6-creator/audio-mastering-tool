"""Integration tests for the similarity search endpoint."""

import uuid
from unittest.mock import patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.database import get_session_dependency
from api.main import app
from api.models import (
    Analysis,
    BandMetrics,
    Base,
    OverallMetrics,
    ReferenceBandMetrics,
    ReferenceOverallMetrics,
    ReferenceTrack,
)
from api.repositories.analysis_repo import AnalysisRepository
from api.repositories.reference_repo import ReferenceRepository
from api.schemas import SimilaritySearchResponse
from ml.feature_extraction import FeatureExtractor
from ml.similarity import serialize_vector


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:", echo=False)

    def _set_pragma(dbapi_conn, connection_record):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    event.listen(eng, "connect", _set_pragma)
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def session(engine):
    conn = engine.connect()
    txn = conn.begin()
    sess = sessionmaker(bind=conn, expire_on_commit=False)()
    yield sess
    sess.close()
    txn.rollback()
    conn.close()


def _create_analysis_with_metrics(session) -> str:
    """Create a complete analysis with band metrics and overall metrics."""
    analysis_id = str(uuid.uuid4())
    analysis = Analysis(
        id=analysis_id,
        file_path="/tmp/test.wav",
        file_name="test.wav",
        status="completed",
        recommendation_level="suggestive",
    )
    session.add(analysis)
    session.flush()

    bands = [
        ("low", 20, 200),
        ("low_mid", 200, 500),
        ("mid", 500, 2000),
        ("high_mid", 2000, 6000),
        ("high", 6000, 20000),
    ]
    for name, fmin, fmax in bands:
        bm = BandMetrics(
            analysis_id=analysis_id,
            band_name=name,
            freq_min=fmin,
            freq_max=fmax,
            band_rms_dbfs=-18.0,
            dynamic_range_db=7.0,
            crest_factor_db=8.0,
            rms_db=-20.0,
            spectral_centroid_hz=1000.0,
            spectral_rolloff_hz=2000.0,
            spectral_flatness=0.25,
            energy_db=-20.0,
            stereo_width_percent=80.0,
            phase_correlation=0.8,
            thd_percent=1.5,
            harmonic_ratio=0.6,
            transient_preservation=0.7,
            attack_time_ms=10.0,
        )
        session.add(bm)

    overall = OverallMetrics(
        analysis_id=analysis_id,
        integrated_lufs=-7.0,
        loudness_range_lu=5.5,
        true_peak_dbfs=-0.5,
        dynamic_range_db=7.0,
        crest_factor_db=8.0,
        avg_stereo_width_percent=80.0,
        avg_phase_correlation=0.78,
        spectral_centroid_hz=3500.0,
        spectral_bandwidth_hz=4000.0,
    )
    session.add(overall)
    session.flush()
    return analysis_id


def _create_reference_track(session, genre: str, track_name: str, artist: str) -> str:
    """Create a reference track with metrics and feature vector."""
    track = ReferenceTrack(
        track_name=track_name,
        artist=artist,
        genre=genre,
        year=2020,
        is_builtin=True,
    )
    session.add(track)
    session.flush()

    bands = [
        ("low", 20, 200),
        ("low_mid", 200, 500),
        ("mid", 500, 2000),
        ("high_mid", 2000, 6000),
        ("high", 6000, 20000),
    ]
    band_metrics = []
    for name, fmin, fmax in bands:
        rbm = ReferenceBandMetrics(
            reference_track_id=track.id,
            band_name=name,
            freq_min=fmin,
            freq_max=fmax,
            band_rms_dbfs=-18.0,
            dynamic_range_db=7.0,
            crest_factor_db=8.0,
            rms_db=-20.0,
            spectral_centroid_hz=1000.0,
            spectral_rolloff_hz=2000.0,
            spectral_flatness=0.25,
            energy_db=-20.0,
            stereo_width_percent=80.0,
            phase_correlation=0.8,
            thd_percent=1.5,
            harmonic_ratio=0.6,
            transient_preservation=0.7,
            attack_time_ms=10.0,
        )
        session.add(rbm)
        band_metrics.append(rbm)

    ref_overall = ReferenceOverallMetrics(
        reference_track_id=track.id,
        integrated_lufs=-7.0,
        loudness_range_lu=5.5,
        true_peak_dbfs=-0.5,
        dynamic_range_db=7.0,
        crest_factor_db=8.0,
        avg_stereo_width_percent=80.0,
        avg_phase_correlation=0.78,
        spectral_centroid_hz=3500.0,
        spectral_bandwidth_hz=4000.0,
    )
    session.add(ref_overall)
    session.flush()

    extractor = FeatureExtractor()
    vec = extractor.extract_from_metrics(band_metrics, ref_overall)
    track.similarity_vector = serialize_vector(vec)
    session.flush()

    return track.id


class TestSimilaritySearch:
    def test_full_flow(self, session):
        """Test: create analysis -> extract features -> find similar references."""
        analysis_id = _create_analysis_with_metrics(session)
        ref_id = _create_reference_track(session, "Psytrance", "Test Track", "Test Artist")

        analysis_repo = AnalysisRepository(session)
        analysis = analysis_repo.get_with_metrics(analysis_id)
        assert analysis is not None

        extractor = FeatureExtractor()
        user_vector = extractor.extract_from_metrics(
            analysis.band_metrics, analysis.overall_metrics
        )

        ref_repo = ReferenceRepository(session)
        matches = ref_repo.search_by_similarity(user_vector, top_k=10)

        assert len(matches) >= 1
        track, score = matches[0]
        assert track.id == ref_id
        assert 0.0 <= score <= 1.0

    def test_identical_metrics_high_similarity(self, session):
        """Tracks with identical metrics should have very high similarity."""
        analysis_id = _create_analysis_with_metrics(session)
        ref_id = _create_reference_track(session, "Trance", "Similar Track", "Similar Artist")

        analysis_repo = AnalysisRepository(session)
        analysis = analysis_repo.get_with_metrics(analysis_id)

        extractor = FeatureExtractor()
        user_vector = extractor.extract_from_metrics(
            analysis.band_metrics, analysis.overall_metrics
        )

        ref_repo = ReferenceRepository(session)
        matches = ref_repo.search_by_similarity(user_vector)

        # Find our reference in results
        found = [s for t, s in matches if t.id == ref_id]
        assert len(found) == 1
        assert found[0] > 0.95  # Nearly identical

    def test_genre_filter(self, session):
        """Genre filter should only return matching references."""
        _create_analysis_with_metrics(session)
        _create_reference_track(session, "Techno", "Techno Track", "Techno DJ")
        _create_reference_track(session, "House", "House Track", "House DJ")

        extractor = FeatureExtractor()
        user_vector = np.random.randn(128).astype(np.float32)
        user_vector = user_vector / np.linalg.norm(user_vector)

        ref_repo = ReferenceRepository(session)
        matches = ref_repo.search_by_similarity(user_vector, genre_filter="Techno")

        for track, _ in matches:
            assert track.genre == "Techno"

    def test_top_k_limit(self, session):
        """Results should respect the top_k limit."""
        for i in range(5):
            _create_reference_track(session, "Trance", f"Track {i}", f"Artist {i}")

        extractor = FeatureExtractor()
        user_vector = np.ones(128, dtype=np.float32)
        user_vector = user_vector / np.linalg.norm(user_vector)

        ref_repo = ReferenceRepository(session)
        matches = ref_repo.search_by_similarity(user_vector, top_k=3)

        assert len(matches) <= 3

    def test_no_references_returns_empty(self, session):
        """Empty reference database should return empty results."""
        extractor = FeatureExtractor()
        user_vector = np.ones(128, dtype=np.float32)
        user_vector = user_vector / np.linalg.norm(user_vector)

        ref_repo = ReferenceRepository(session)
        # Filter to a genre with no tracks
        matches = ref_repo.search_by_similarity(
            user_vector, genre_filter="NonExistentGenre"
        )
        assert matches == []


# ---------------------------------------------------------------------------
# HTTP-level tests using FastAPI TestClient
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def http_engine():
    """In-memory SQLite engine with StaticPool for HTTP tests."""
    eng = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    def _set_pragma(dbapi_conn, connection_record):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    event.listen(eng, "connect", _set_pragma)
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture(scope="module")
def http_session_factory(http_engine):
    return sessionmaker(bind=http_engine, expire_on_commit=False)


@pytest.fixture(scope="module")
def client(http_session_factory):
    """FastAPI TestClient with overridden DB dependency."""

    def _override_session():
        session = http_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_session_dependency] = _override_session

    with patch("api.routers.analyze.SessionFactory", http_session_factory), \
         TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


def _seed_analysis_with_metrics(session_factory) -> str:
    """Seed a complete analysis with band and overall metrics. Returns the analysis ID."""
    session = session_factory()
    try:
        analysis_id = str(uuid.uuid4())
        analysis = Analysis(
            id=analysis_id,
            file_path="/tmp/test.wav",
            file_name="test.wav",
            status="completed",
            recommendation_level="suggestive",
        )
        session.add(analysis)
        session.flush()

        bands = [
            ("low", 20, 200),
            ("low_mid", 200, 500),
            ("mid", 500, 2000),
            ("high_mid", 2000, 6000),
            ("high", 6000, 20000),
        ]
        for name, fmin, fmax in bands:
            bm = BandMetrics(
                analysis_id=analysis_id,
                band_name=name,
                freq_min=fmin,
                freq_max=fmax,
                band_rms_dbfs=-18.0,
                dynamic_range_db=7.0,
                crest_factor_db=8.0,
                rms_db=-20.0,
                spectral_centroid_hz=1000.0,
                spectral_rolloff_hz=2000.0,
                spectral_flatness=0.25,
                energy_db=-20.0,
                stereo_width_percent=80.0,
                phase_correlation=0.8,
                thd_percent=1.5,
                harmonic_ratio=0.6,
                transient_preservation=0.7,
                attack_time_ms=10.0,
            )
            session.add(bm)

        overall = OverallMetrics(
            analysis_id=analysis_id,
            integrated_lufs=-7.0,
            loudness_range_lu=5.5,
            true_peak_dbfs=-0.5,
            dynamic_range_db=7.0,
            crest_factor_db=8.0,
            avg_stereo_width_percent=80.0,
            avg_phase_correlation=0.78,
            spectral_centroid_hz=3500.0,
            spectral_bandwidth_hz=4000.0,
        )
        session.add(overall)
        session.commit()
        return analysis_id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _seed_analysis_without_metrics(session_factory) -> str:
    """Seed an analysis with NO band or overall metrics. Returns the analysis ID."""
    session = session_factory()
    try:
        analysis_id = str(uuid.uuid4())
        analysis = Analysis(
            id=analysis_id,
            file_path="/tmp/incomplete.wav",
            file_name="incomplete.wav",
            status="pending",
            recommendation_level="suggestive",
        )
        session.add(analysis)
        session.commit()
        return analysis_id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _seed_reference_track(session_factory, genre: str, track_name: str, artist: str) -> str:
    """Seed a reference track with metrics and a similarity vector. Returns the track ID."""
    session = session_factory()
    try:
        track = ReferenceTrack(
            track_name=track_name,
            artist=artist,
            genre=genre,
            year=2020,
            is_builtin=True,
        )
        session.add(track)
        session.flush()

        bands = [
            ("low", 20, 200),
            ("low_mid", 200, 500),
            ("mid", 500, 2000),
            ("high_mid", 2000, 6000),
            ("high", 6000, 20000),
        ]
        band_metrics = []
        for name, fmin, fmax in bands:
            rbm = ReferenceBandMetrics(
                reference_track_id=track.id,
                band_name=name,
                freq_min=fmin,
                freq_max=fmax,
                band_rms_dbfs=-18.0,
                dynamic_range_db=7.0,
                crest_factor_db=8.0,
                rms_db=-20.0,
                spectral_centroid_hz=1000.0,
                spectral_rolloff_hz=2000.0,
                spectral_flatness=0.25,
                energy_db=-20.0,
                stereo_width_percent=80.0,
                phase_correlation=0.8,
                thd_percent=1.5,
                harmonic_ratio=0.6,
                transient_preservation=0.7,
                attack_time_ms=10.0,
            )
            session.add(rbm)
            band_metrics.append(rbm)

        ref_overall = ReferenceOverallMetrics(
            reference_track_id=track.id,
            integrated_lufs=-7.0,
            loudness_range_lu=5.5,
            true_peak_dbfs=-0.5,
            dynamic_range_db=7.0,
            crest_factor_db=8.0,
            avg_stereo_width_percent=80.0,
            avg_phase_correlation=0.78,
            spectral_centroid_hz=3500.0,
            spectral_bandwidth_hz=4000.0,
        )
        session.add(ref_overall)
        session.flush()

        extractor = FeatureExtractor()
        vec = extractor.extract_from_metrics(band_metrics, ref_overall)
        track.similarity_vector = serialize_vector(vec)
        session.commit()
        return track.id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class TestSimilarityEndpointHTTP:
    """HTTP-level tests for POST /api/similarity/{analysis_id}."""

    def test_similarity_200_top_k_and_genre_filter(self, client, http_session_factory):
        """POST returns 200, honors top_k, and applies genre filter."""
        analysis_id = _seed_analysis_with_metrics(http_session_factory)
        for i in range(4):
            _seed_reference_track(
                http_session_factory, "Trance", f"HTTP Trance {i}", f"HTTP Artist {i}"
            )
        _seed_reference_track(http_session_factory, "House", "HTTP House", "HTTP House Artist")

        response = client.post(f"/api/similarity/{analysis_id}?top_k=2&genre=Trance")

        assert response.status_code == 200
        payload = SimilaritySearchResponse.model_validate(response.json())
        assert len(payload.matches) >= 1
        assert len(payload.matches) <= 2
        assert all(match.genre == "Trance" for match in payload.matches)

    def test_similarity_404_nonexistent_analysis(self, client):
        """POST with a nonexistent analysis_id returns 404."""
        fake_id = str(uuid.uuid4())
        response = client.post(f"/api/similarity/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Analysis not found"

    def test_similarity_400_missing_metrics(self, client, http_session_factory):
        """POST with an analysis that has no metrics returns 400."""
        analysis_id = _seed_analysis_without_metrics(http_session_factory)

        response = client.post(f"/api/similarity/{analysis_id}")

        assert response.status_code == 400
        assert "missing" in response.json()["detail"].lower()

    def test_similarity_response_schema(self, client, http_session_factory):
        """Response body conforms to the SimilaritySearchResponse schema."""
        analysis_id = _seed_analysis_with_metrics(http_session_factory)
        _seed_reference_track(http_session_factory, "Pop", "Schema Track", "Schema Artist")

        response = client.post(f"/api/similarity/{analysis_id}")

        assert response.status_code == 200
        payload = SimilaritySearchResponse.model_validate(response.json())
        assert isinstance(payload.matches, list)
