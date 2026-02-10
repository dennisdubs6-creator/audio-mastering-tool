"""Tests for the FeatureExtractor class."""

import numpy as np
import pytest

from ml.feature_extraction import FeatureExtractor


class _MockBandMetrics:
    """Minimal mock of a BandMetrics / ReferenceBandMetrics ORM instance."""

    def __init__(self, band_name, **kwargs):
        self.band_name = band_name
        self.spectral_centroid_hz = kwargs.get("spectral_centroid_hz", 1000.0)
        self.spectral_rolloff_hz = kwargs.get("spectral_rolloff_hz", 2000.0)
        self.spectral_flatness = kwargs.get("spectral_flatness", 0.3)
        self.energy_db = kwargs.get("energy_db", -20.0)
        self.dynamic_range_db = kwargs.get("dynamic_range_db", 8.0)
        self.crest_factor_db = kwargs.get("crest_factor_db", 7.0)
        self.rms_db = kwargs.get("rms_db", -18.0)
        self.stereo_width_percent = kwargs.get("stereo_width_percent", 75.0)
        self.phase_correlation = kwargs.get("phase_correlation", 0.8)
        self.thd_percent = kwargs.get("thd_percent", 1.5)
        self.harmonic_ratio = kwargs.get("harmonic_ratio", 0.6)
        self.transient_preservation = kwargs.get("transient_preservation", 0.7)
        self.attack_time_ms = kwargs.get("attack_time_ms", 10.0)


class _MockOverallMetrics:
    """Minimal mock of an OverallMetrics / ReferenceOverallMetrics instance."""

    def __init__(self, **kwargs):
        self.integrated_lufs = kwargs.get("integrated_lufs", -7.0)
        self.loudness_range_lu = kwargs.get("loudness_range_lu", 6.0)
        self.true_peak_dbfs = kwargs.get("true_peak_dbfs", -0.5)
        self.dynamic_range_db = kwargs.get("dynamic_range_db", 8.0)
        self.crest_factor_db = kwargs.get("crest_factor_db", 8.5)
        self.avg_stereo_width_percent = kwargs.get("avg_stereo_width_percent", 80.0)
        self.avg_phase_correlation = kwargs.get("avg_phase_correlation", 0.75)
        self.spectral_centroid_hz = kwargs.get("spectral_centroid_hz", 3500.0)
        self.spectral_bandwidth_hz = kwargs.get("spectral_bandwidth_hz", 4000.0)


def _make_band_metrics():
    bands = ["low", "low_mid", "mid", "high_mid", "high"]
    return [_MockBandMetrics(name) for name in bands]


def _make_overall_metrics():
    return _MockOverallMetrics()


class TestFeatureExtractor:
    def test_vector_dimensionality(self):
        extractor = FeatureExtractor()
        vec = extractor.extract_from_metrics(_make_band_metrics(), _make_overall_metrics())
        assert vec.shape == (128,)
        assert vec.dtype == np.float32

    def test_l2_normalization(self):
        extractor = FeatureExtractor()
        vec = extractor.extract_from_metrics(_make_band_metrics(), _make_overall_metrics())
        norm = np.linalg.norm(vec)
        assert abs(norm - 1.0) < 1e-5, f"L2 norm should be ~1.0, got {norm}"

    def test_none_values_handled(self):
        """Feature extraction should handle None attribute values gracefully."""
        bands = ["low", "low_mid", "mid", "high_mid", "high"]
        band_metrics = []
        for name in bands:
            bm = _MockBandMetrics(name)
            bm.spectral_centroid_hz = None
            bm.energy_db = None
            bm.thd_percent = None
            band_metrics.append(bm)

        overall = _MockOverallMetrics()
        overall.integrated_lufs = None
        overall.dynamic_range_db = None

        extractor = FeatureExtractor()
        vec = extractor.extract_from_metrics(band_metrics, overall)

        assert vec.shape == (128,)
        assert not np.any(np.isnan(vec))
        assert not np.any(np.isinf(vec))

    def test_identical_inputs_produce_identical_vectors(self):
        extractor = FeatureExtractor()
        vec1 = extractor.extract_from_metrics(_make_band_metrics(), _make_overall_metrics())
        vec2 = extractor.extract_from_metrics(_make_band_metrics(), _make_overall_metrics())
        np.testing.assert_array_almost_equal(vec1, vec2)

    def test_different_inputs_produce_different_vectors(self):
        extractor = FeatureExtractor()
        vec1 = extractor.extract_from_metrics(_make_band_metrics(), _make_overall_metrics())

        loud_overall = _MockOverallMetrics(integrated_lufs=-3.0, dynamic_range_db=4.0)
        vec2 = extractor.extract_from_metrics(_make_band_metrics(), loud_overall)

        assert not np.allclose(vec1, vec2)

    def test_missing_bands_handled(self):
        """Should handle case where some bands are missing."""
        extractor = FeatureExtractor()
        partial_bands = [_MockBandMetrics("low"), _MockBandMetrics("mid")]
        vec = extractor.extract_from_metrics(partial_bands, _make_overall_metrics())
        assert vec.shape == (128,)
        assert not np.any(np.isnan(vec))
