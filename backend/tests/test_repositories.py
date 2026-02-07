"""
Tests for AnalysisRepository and ReferenceRepository CRUD operations.
"""

import uuid

from api.models import Analysis, BandMetrics, OverallMetrics, ReferenceTrack
from api.repositories.analysis_repo import AnalysisRepository
from api.repositories.reference_repo import ReferenceRepository


# ---------------------------------------------------------------------------
# AnalysisRepository
# ---------------------------------------------------------------------------

class TestAnalysisRepository:

    def test_create_and_get_by_id(self, session, sample_analysis):
        repo = AnalysisRepository(session)
        analysis = Analysis(**sample_analysis)
        repo.create(analysis)

        fetched = repo.get_by_id(sample_analysis["id"])
        assert fetched is not None
        assert fetched.file_name == "test.wav"

    def test_get_all(self, session, sample_analysis):
        repo = AnalysisRepository(session)
        repo.create(Analysis(**sample_analysis))

        all_analyses = repo.get_all()
        assert len(all_analyses) >= 1

    def test_get_with_metrics(self, session, sample_analysis, sample_band_metrics):
        repo = AnalysisRepository(session)
        analysis = Analysis(**sample_analysis)
        repo.create(analysis)

        for bm_data in sample_band_metrics:
            session.add(BandMetrics(**bm_data))
        session.flush()

        overall = OverallMetrics(
            id=str(uuid.uuid4()),
            analysis_id=sample_analysis["id"],
            integrated_lufs=-14.0,
            dynamic_range_db=10.0,
        )
        session.add(overall)
        session.flush()

        result = repo.get_with_metrics(sample_analysis["id"])
        assert result is not None
        assert len(result.band_metrics) == 5
        assert result.overall_metrics is not None
        assert result.overall_metrics.integrated_lufs == -14.0

    def test_get_by_genre(self, session, sample_analysis):
        repo = AnalysisRepository(session)
        repo.create(Analysis(**sample_analysis))

        results = repo.get_by_genre("rock")
        assert len(results) >= 1
        assert all(a.genre == "rock" for a in results)

    def test_get_recent(self, session, sample_analysis):
        repo = AnalysisRepository(session)
        repo.create(Analysis(**sample_analysis))

        results = repo.get_recent(limit=5)
        assert len(results) >= 1

    def test_delete(self, session, sample_analysis):
        repo = AnalysisRepository(session)
        analysis = Analysis(**sample_analysis)
        repo.create(analysis)

        repo.delete(analysis)
        assert repo.get_by_id(sample_analysis["id"]) is None

    def test_save_complete_analysis(self, session):
        repo = AnalysisRepository(session)
        analysis = Analysis(
            file_path="/tmp/complete.wav",
            file_name="complete.wav",
        )
        band_metrics = [
            BandMetrics(band_name="low", freq_min=20, freq_max=200),
            BandMetrics(band_name="mid", freq_min=500, freq_max=2000),
        ]
        overall = OverallMetrics(integrated_lufs=-14.0)

        saved = repo.save_complete_analysis(analysis, band_metrics, overall)
        assert saved.id is not None
        assert len(saved.band_metrics) == 2


# ---------------------------------------------------------------------------
# ReferenceRepository
# ---------------------------------------------------------------------------

class TestReferenceRepository:

    def test_create_and_get_by_id(self, session, sample_reference_track):
        repo = ReferenceRepository(session)
        track = ReferenceTrack(**sample_reference_track)
        repo.create(track)

        fetched = repo.get_by_id(sample_reference_track["id"])
        assert fetched is not None
        assert fetched.track_name == "Test Reference"

    def test_get_all_builtin(self, session, sample_reference_track):
        repo = ReferenceRepository(session)
        repo.create(ReferenceTrack(**sample_reference_track))

        builtins = repo.get_all_builtin()
        assert len(builtins) >= 1
        assert all(t.is_builtin for t in builtins)

    def test_get_by_genre(self, session, sample_reference_track):
        repo = ReferenceRepository(session)
        repo.create(ReferenceTrack(**sample_reference_track))

        results = repo.get_by_genre("rock")
        assert len(results) >= 1

    def test_get_with_band_metrics(self, session, sample_reference_track):
        repo = ReferenceRepository(session)
        repo.create(ReferenceTrack(**sample_reference_track))

        result = repo.get_with_band_metrics(sample_reference_track["id"])
        assert result is not None
        assert result.reference_band_metrics == []

    def test_add_user_reference(self, session):
        repo = ReferenceRepository(session)
        track = repo.add_user_reference({
            "track_name": "User Track",
            "artist": "User Artist",
            "genre": "pop",
        })
        assert track.id is not None
        assert track.is_builtin is False
        assert track.track_name == "User Track"

    def test_search_by_similarity_stub(self, session):
        repo = ReferenceRepository(session)
        results = repo.search_by_similarity(b"\x00\x01\x02")
        assert results == []
