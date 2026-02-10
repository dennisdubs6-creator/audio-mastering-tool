"""
Tests for the recommendation engine.
"""

import pytest

from recommendations.engine import RecommendationEngine


class MockBandMetrics:
    """Minimal mock for band metrics objects."""

    def __init__(self, band_name, band_rms_dbfs=None, energy_db=None,
                 dynamic_range_db=None, stereo_width_percent=None):
        self.band_name = band_name
        self.band_rms_dbfs = band_rms_dbfs
        self.energy_db = energy_db
        self.dynamic_range_db = dynamic_range_db
        self.stereo_width_percent = stereo_width_percent


class MockOverallMetrics:
    """Minimal mock for overall metrics objects."""

    def __init__(self, integrated_lufs=None, dynamic_range_db=None,
                 true_peak_dbfs=None, avg_stereo_width_percent=None,
                 loudness_range_lu=None, crest_factor_db=None,
                 avg_phase_correlation=None):
        self.integrated_lufs = integrated_lufs
        self.dynamic_range_db = dynamic_range_db
        self.true_peak_dbfs = true_peak_dbfs
        self.avg_stereo_width_percent = avg_stereo_width_percent
        self.loudness_range_lu = loudness_range_lu
        self.crest_factor_db = crest_factor_db
        self.avg_phase_correlation = avg_phase_correlation


def make_user_bands():
    return [
        MockBandMetrics("low", band_rms_dbfs=-18.0, energy_db=-16.0, dynamic_range_db=6.0, stereo_width_percent=40.0),
        MockBandMetrics("low_mid", band_rms_dbfs=-22.0, energy_db=-20.0, dynamic_range_db=7.0, stereo_width_percent=60.0),
        MockBandMetrics("mid", band_rms_dbfs=-20.0, energy_db=-18.0, dynamic_range_db=8.0, stereo_width_percent=80.0),
        MockBandMetrics("high_mid", band_rms_dbfs=-24.0, energy_db=-22.0, dynamic_range_db=7.5, stereo_width_percent=90.0),
        MockBandMetrics("high", band_rms_dbfs=-30.0, energy_db=-28.0, dynamic_range_db=6.5, stereo_width_percent=85.0),
    ]


def make_ref_bands():
    return [
        MockBandMetrics("low", band_rms_dbfs=-20.0, energy_db=-18.0, dynamic_range_db=6.0, stereo_width_percent=40.0),
        MockBandMetrics("low_mid", band_rms_dbfs=-24.0, energy_db=-22.0, dynamic_range_db=7.0, stereo_width_percent=60.0),
        MockBandMetrics("mid", band_rms_dbfs=-22.0, energy_db=-20.0, dynamic_range_db=8.0, stereo_width_percent=80.0),
        MockBandMetrics("high_mid", band_rms_dbfs=-26.0, energy_db=-24.0, dynamic_range_db=7.5, stereo_width_percent=90.0),
        MockBandMetrics("high", band_rms_dbfs=-36.0, energy_db=-34.0, dynamic_range_db=6.5, stereo_width_percent=85.0),
    ]


class TestRecommendationEngine:
    def test_generate_with_reference_returns_recommendations(self):
        engine = RecommendationEngine()
        user_bands = make_user_bands()
        ref_bands = make_ref_bands()
        user_overall = MockOverallMetrics(integrated_lufs=-7.0, dynamic_range_db=7.0)
        ref_overall = MockOverallMetrics(integrated_lufs=-7.0, dynamic_range_db=7.0)

        recs = engine.generate(user_bands, user_overall, ref_bands, ref_overall)
        assert isinstance(recs, list)

    def test_delta_computation(self):
        engine = RecommendationEngine()
        # User low band is 2dB louder than reference (at attention threshold)
        user_bands = [MockBandMetrics("low", band_rms_dbfs=-18.0)]
        ref_bands = [MockBandMetrics("low", band_rms_dbfs=-20.0)]

        recs = engine.generate(user_bands, None, ref_bands, None)
        assert len(recs) >= 1

        low_rec = [r for r in recs if r["band_name"] == "low"]
        assert len(low_rec) >= 1
        assert low_rec[0]["metric_category"] == "loudness"

    def test_severity_classification(self):
        engine = RecommendationEngine()

        assert engine._classify_severity(5.0) == "issue"
        assert engine._classify_severity(-4.5) == "issue"
        assert engine._classify_severity(3.0) == "attention"
        assert engine._classify_severity(-2.5) == "attention"
        assert engine._classify_severity(1.0) == "info"
        assert engine._classify_severity(0.0) == "info"

    def test_three_text_levels_populated(self):
        engine = RecommendationEngine()
        # 6dB delta -> should generate recommendation
        user_bands = [MockBandMetrics("high", band_rms_dbfs=-24.0)]
        ref_bands = [MockBandMetrics("high", band_rms_dbfs=-30.0)]

        recs = engine.generate(user_bands, None, ref_bands, None)
        assert len(recs) >= 1

        rec = recs[0]
        assert rec["analytical_text"] is not None
        assert rec["suggestive_text"] is not None
        assert rec["prescriptive_text"] is not None
        assert rec["severity"] == "issue"  # 6dB delta

    def test_genre_rules_with_psytrance(self):
        engine = RecommendationEngine()
        # User far from Psytrance targets
        user_bands = [
            MockBandMetrics("low", band_rms_dbfs=-10.0, energy_db=-8.0),
        ]
        user_overall = MockOverallMetrics(integrated_lufs=-2.0)

        recs = engine.generate(user_bands, user_overall, genre="Psytrance")
        assert isinstance(recs, list)
        assert len(recs) >= 1

    def test_genre_rules_no_recs_when_on_target(self):
        engine = RecommendationEngine()
        # User exactly on Psytrance targets for low band
        user_bands = [
            MockBandMetrics("low", band_rms_dbfs=-20.0, energy_db=-18.0,
                            dynamic_range_db=6.0, stereo_width_percent=40.0),
        ]

        recs = engine.generate(user_bands, None, genre="Psytrance")
        # Should have no band-level recs since values match targets
        band_recs = [r for r in recs if r["band_name"] == "low"]
        assert len(band_recs) == 0

    def test_no_genre_returns_empty(self):
        engine = RecommendationEngine()
        user_bands = make_user_bands()
        recs = engine.generate(user_bands, None, genre=None)
        assert recs == []

    def test_unknown_genre_returns_empty(self):
        engine = RecommendationEngine()
        user_bands = make_user_bands()
        recs = engine.generate(user_bands, None, genre="Unknown Genre")
        assert recs == []

    def test_overall_metric_comparison(self):
        engine = RecommendationEngine()
        user_overall = MockOverallMetrics(integrated_lufs=-2.0, dynamic_range_db=3.0)
        ref_overall = MockOverallMetrics(integrated_lufs=-7.0, dynamic_range_db=7.0)

        recs = engine.generate([], user_overall, [], ref_overall)
        overall_recs = [r for r in recs if r["band_name"] is None]
        assert len(overall_recs) >= 2  # LUFS and DR both have large deltas

    def test_different_genres(self):
        engine = RecommendationEngine()
        user_bands = make_user_bands()
        user_overall = MockOverallMetrics(integrated_lufs=-2.0)

        for genre in ["Psytrance", "Trance", "Techno", "House", "Drum & Bass", "Dubstep"]:
            recs = engine.generate(user_bands, user_overall, genre=genre)
            assert isinstance(recs, list)
