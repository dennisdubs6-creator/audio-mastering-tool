"""
Tests for the comparison API endpoint.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


class MockBandMetrics:
    def __init__(self, band_name="low", **kwargs):
        self.id = "band-metric-id"
        self.band_name = band_name
        self.freq_min = 20
        self.freq_max = 200
        self.band_rms_dbfs = kwargs.get("band_rms_dbfs", -20.0)
        self.band_true_peak_dbfs = kwargs.get("band_true_peak_dbfs", -17.0)
        self.band_level_range_db = kwargs.get("band_level_range_db", 4.8)
        self.dynamic_range_db = kwargs.get("dynamic_range_db", 6.0)
        self.crest_factor_db = kwargs.get("crest_factor_db", 7.0)
        self.rms_db = kwargs.get("rms_db", -20.0)
        self.spectral_centroid_hz = kwargs.get("spectral_centroid_hz", 110.0)
        self.spectral_rolloff_hz = kwargs.get("spectral_rolloff_hz", 180.0)
        self.spectral_flatness = kwargs.get("spectral_flatness", 0.15)
        self.energy_db = kwargs.get("energy_db", -18.0)
        self.stereo_width_percent = kwargs.get("stereo_width_percent", 40.0)
        self.phase_correlation = kwargs.get("phase_correlation", 0.95)
        self.mid_energy_db = kwargs.get("mid_energy_db", -21.0)
        self.side_energy_db = kwargs.get("side_energy_db", -28.0)
        self.thd_percent = kwargs.get("thd_percent", 2.0)
        self.harmonic_ratio = kwargs.get("harmonic_ratio", 0.7)
        self.inharmonicity = kwargs.get("inharmonicity", 0.3)
        self.transient_preservation = kwargs.get("transient_preservation", 0.6)
        self.attack_time_ms = kwargs.get("attack_time_ms", 15.0)


class MockOverallMetrics:
    def __init__(self):
        self.id = "overall-metric-id"
        self.integrated_lufs = -7.0
        self.loudness_range_lu = 5.5
        self.true_peak_dbfs = -0.5
        self.dynamic_range_db = 7.0
        self.crest_factor_db = 8.0
        self.avg_stereo_width_percent = 80.0
        self.avg_phase_correlation = 0.75
        self.spectral_centroid_hz = 3500.0
        self.spectral_bandwidth_hz = 4000.0


class MockAnalysis:
    def __init__(self):
        self.id = "analysis-123"
        self.file_path = "/path/to/file.wav"
        self.file_name = "test.wav"
        self.file_size = 1000000
        self.sample_rate = 44100
        self.bit_depth = 24
        self.duration_seconds = 180.0
        self.genre = "Psytrance"
        self.genre_confidence = 0.85
        self.recommendation_level = "suggestive"
        self.analysis_engine_version = "1.0.0"
        self.created_at = "2025-01-01T00:00:00Z"
        self.updated_at = "2025-01-01T00:00:00Z"
        self.band_metrics = [MockBandMetrics("low"), MockBandMetrics("mid")]
        self.overall_metrics = MockOverallMetrics()
        self.recommendations = []


class MockReferenceTrack:
    def __init__(self):
        self.id = "ref-456"
        self.track_name = "Test Reference"
        self.artist = "Test Artist"
        self.genre = "Psytrance"
        self.year = 2023
        self.is_builtin = True
        self.created_at = "2025-01-01T00:00:00Z"
        self.reference_band_metrics = [MockBandMetrics("low"), MockBandMetrics("mid")]
        self.reference_overall_metrics = MockOverallMetrics()


@patch("api.routers.comparison.ReferenceRepository")
@patch("api.routers.comparison.AnalysisRepository")
def test_compare_valid_ids(mock_analysis_repo_cls, mock_ref_repo_cls):
    mock_analysis_repo = MagicMock()
    mock_analysis_repo.get_with_metrics.return_value = MockAnalysis()
    mock_analysis_repo_cls.return_value = mock_analysis_repo

    mock_ref_repo = MagicMock()
    mock_ref_repo.get_with_all_metrics.return_value = MockReferenceTrack()
    mock_ref_repo_cls.return_value = mock_ref_repo

    response = client.get("/api/compare/analysis-123/ref-456")
    assert response.status_code == 200

    data = response.json()
    assert "user_analysis" in data
    assert "reference_track" in data
    assert "reference_band_metrics" in data
    assert "recommendations" in data
    assert "comparison_mode" in data
    assert data["comparison_mode"] == "side-by-side"


@patch("api.routers.comparison.ReferenceRepository")
@patch("api.routers.comparison.AnalysisRepository")
def test_compare_analysis_not_found(mock_analysis_repo_cls, mock_ref_repo_cls):
    mock_analysis_repo = MagicMock()
    mock_analysis_repo.get_with_metrics.return_value = None
    mock_analysis_repo_cls.return_value = mock_analysis_repo

    response = client.get("/api/compare/nonexistent/ref-456")
    assert response.status_code == 404


@patch("api.routers.comparison.ReferenceRepository")
@patch("api.routers.comparison.AnalysisRepository")
def test_compare_reference_not_found(mock_analysis_repo_cls, mock_ref_repo_cls):
    mock_analysis_repo = MagicMock()
    mock_analysis_repo.get_with_metrics.return_value = MockAnalysis()
    mock_analysis_repo_cls.return_value = mock_analysis_repo

    mock_ref_repo = MagicMock()
    mock_ref_repo.get_with_all_metrics.return_value = None
    mock_ref_repo_cls.return_value = mock_ref_repo

    response = client.get("/api/compare/analysis-123/nonexistent")
    assert response.status_code == 404


@patch("api.routers.comparison.ReferenceRepository")
@patch("api.routers.comparison.AnalysisRepository")
def test_compare_incomplete_analysis(mock_analysis_repo_cls, mock_ref_repo_cls):
    mock_analysis = MockAnalysis()
    mock_analysis.band_metrics = []
    mock_analysis.overall_metrics = None

    mock_analysis_repo = MagicMock()
    mock_analysis_repo.get_with_metrics.return_value = mock_analysis
    mock_analysis_repo_cls.return_value = mock_analysis_repo

    response = client.get("/api/compare/analysis-123/ref-456")
    assert response.status_code == 400


@patch("api.routers.comparison.ReferenceRepository")
@patch("api.routers.comparison.AnalysisRepository")
def test_compare_with_recommendation_level(mock_analysis_repo_cls, mock_ref_repo_cls):
    mock_analysis_repo = MagicMock()
    mock_analysis_repo.get_with_metrics.return_value = MockAnalysis()
    mock_analysis_repo_cls.return_value = mock_analysis_repo

    mock_ref_repo = MagicMock()
    mock_ref_repo.get_with_all_metrics.return_value = MockReferenceTrack()
    mock_ref_repo_cls.return_value = mock_ref_repo

    response = client.get("/api/compare/analysis-123/ref-456?recommendation_level=prescriptive")
    assert response.status_code == 200

    data = response.json()
    assert "recommendations" in data


@patch("api.routers.comparison.ReferenceRepository")
@patch("api.routers.comparison.AnalysisRepository")
def test_compare_recommendation_levels_change_active_text(mock_analysis_repo_cls, mock_ref_repo_cls):
    analysis = MockAnalysis()
    reference = MockReferenceTrack()
    reference.reference_band_metrics[0].band_rms_dbfs = -24.0

    mock_analysis_repo = MagicMock()
    mock_analysis_repo.get_with_metrics.return_value = analysis
    mock_analysis_repo_cls.return_value = mock_analysis_repo

    mock_ref_repo = MagicMock()
    mock_ref_repo.get_with_all_metrics.return_value = reference
    mock_ref_repo_cls.return_value = mock_ref_repo

    analytical_response = client.get("/api/compare/analysis-123/ref-456?recommendation_level=analytical")
    suggestive_response = client.get("/api/compare/analysis-123/ref-456?recommendation_level=suggestive")
    prescriptive_response = client.get("/api/compare/analysis-123/ref-456?recommendation_level=prescriptive")

    assert analytical_response.status_code == 200
    assert suggestive_response.status_code == 200
    assert prescriptive_response.status_code == 200

    analytical_rec = analytical_response.json()["recommendations"][0]
    suggestive_rec = suggestive_response.json()["recommendations"][0]
    prescriptive_rec = prescriptive_response.json()["recommendations"][0]

    assert analytical_rec["recommendation_text"] == analytical_rec["analytical_text"]
    assert suggestive_rec["recommendation_text"] == suggestive_rec["suggestive_text"]
    assert prescriptive_rec["recommendation_text"] == prescriptive_rec["prescriptive_text"]

    assert analytical_rec["recommendation_text"] != suggestive_rec["recommendation_text"]
    assert suggestive_rec["recommendation_text"] != prescriptive_rec["recommendation_text"]


@patch("api.routers.comparison.ReferenceRepository")
@patch("api.routers.comparison.AnalysisRepository")
def test_compare_response_schema(mock_analysis_repo_cls, mock_ref_repo_cls):
    mock_analysis_repo = MagicMock()
    mock_analysis_repo.get_with_metrics.return_value = MockAnalysis()
    mock_analysis_repo_cls.return_value = mock_analysis_repo

    mock_ref_repo = MagicMock()
    mock_ref_repo.get_with_all_metrics.return_value = MockReferenceTrack()
    mock_ref_repo_cls.return_value = mock_ref_repo

    response = client.get("/api/compare/analysis-123/ref-456")
    assert response.status_code == 200

    data = response.json()
    # Validate reference band metrics structure
    assert isinstance(data["reference_band_metrics"], list)
    if len(data["reference_band_metrics"]) > 0:
        rbm = data["reference_band_metrics"][0]
        assert "band_name" in rbm
        assert "band_rms_dbfs" in rbm
        assert "energy_db" in rbm

    # Validate recommendations structure
    assert isinstance(data["recommendations"], list)
    for rec in data["recommendations"]:
        assert "id" in rec
        assert "severity" in rec
        assert "analytical_text" in rec
        assert "suggestive_text" in rec
        assert "prescriptive_text" in rec
