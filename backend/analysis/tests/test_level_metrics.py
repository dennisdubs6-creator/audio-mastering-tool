"""Tests for analysis.metrics.level module."""

import math

import numpy as np
import pytest

from analysis.metrics.level import (
    compute_band_level_range_db,
    compute_band_rms_dbfs,
    compute_band_true_peak_dbfs,
)


class TestBandRmsDbfs:
    def test_sine_wave_rms(self, sine_wave_440hz):
        """Full-scale sine wave RMS should be ~-3.01 dBFS."""
        rms = compute_band_rms_dbfs(sine_wave_440hz)
        assert rms == pytest.approx(-3.01, abs=0.5)

    def test_white_noise_rms(self, white_noise):
        """Uniform [-1,1] white noise RMS ≈ -4.77 dBFS (sqrt(1/3))."""
        rms = compute_band_rms_dbfs(white_noise)
        assert rms == pytest.approx(-4.77, abs=1.0)

    def test_impulse_rms(self, impulse):
        """Single-sample impulse over 144k samples → very low RMS."""
        rms = compute_band_rms_dbfs(impulse)
        assert rms < -50.0

    def test_silence_returns_floor(self, silence):
        rms = compute_band_rms_dbfs(silence)
        assert rms == -120.0

    def test_empty_array(self):
        rms = compute_band_rms_dbfs(np.array([], dtype=np.float32))
        assert rms == -120.0

    def test_constant_value(self):
        samples = np.full(1000, 0.5, dtype=np.float32)
        rms = compute_band_rms_dbfs(samples)
        assert rms == pytest.approx(20.0 * np.log10(0.5), abs=0.1)

    def test_clipping_no_nan_inf(self, clipping):
        """Clipped signal must produce a finite result."""
        rms = compute_band_rms_dbfs(clipping)
        assert math.isfinite(rms)
        # Clipped sine has more energy than pure sine → higher RMS
        assert rms > -3.01


class TestBandTruePeakDbfs:
    def test_sine_wave_peak(self, sine_wave_440hz):
        """Full-scale sine peak should be ~0 dBFS."""
        peak = compute_band_true_peak_dbfs(sine_wave_440hz)
        assert peak == pytest.approx(0.0, abs=0.1)

    def test_white_noise_peak(self, white_noise):
        """White noise peak should be near 0 dBFS."""
        peak = compute_band_true_peak_dbfs(white_noise)
        assert peak == pytest.approx(0.0, abs=0.1)

    def test_impulse_peak(self, impulse):
        """Impulse peak is exactly 0 dBFS."""
        peak = compute_band_true_peak_dbfs(impulse)
        assert peak == pytest.approx(0.0, abs=0.01)

    def test_silence(self, silence):
        peak = compute_band_true_peak_dbfs(silence)
        assert peak == -120.0

    def test_half_scale(self):
        sig = np.full(100, 0.5, dtype=np.float32)
        peak = compute_band_true_peak_dbfs(sig)
        assert peak == pytest.approx(20.0 * np.log10(0.5), abs=0.1)

    def test_clipping_no_nan_inf(self, clipping):
        """Clipped signal must produce a finite result."""
        peak = compute_band_true_peak_dbfs(clipping)
        assert math.isfinite(peak)
        assert peak == pytest.approx(0.0, abs=0.01)


class TestBandLevelRangeDb:
    def test_constant_signal_zero_range(self, sample_rate):
        samples = np.full(sample_rate * 3, 0.5, dtype=np.float32)
        lr = compute_band_level_range_db(samples, sample_rate)
        assert lr == pytest.approx(0.0, abs=0.01)

    def test_dynamic_signal_positive_range(self, sample_rate):
        """Signal that alternates amplitude should have positive range."""
        half = sample_rate * 3 // 2
        samples = np.concatenate([
            np.full(half, 0.1, dtype=np.float32),
            np.full(half, 1.0, dtype=np.float32),
        ])
        lr = compute_band_level_range_db(samples, sample_rate)
        assert lr > 0.0

    def test_white_noise_low_range(self, white_noise, sample_rate):
        """White noise has consistent RMS across frames → low range."""
        lr = compute_band_level_range_db(white_noise, sample_rate)
        assert lr < 5.0

    def test_impulse_range(self, impulse, sample_rate):
        """Impulse: nearly all frames silent → range is 0 (percentiles both at floor)."""
        lr = compute_band_level_range_db(impulse, sample_rate)
        assert math.isfinite(lr)
        assert lr >= 0.0

    def test_silence(self, silence, sample_rate):
        lr = compute_band_level_range_db(silence, sample_rate)
        assert lr == 0.0

    def test_empty_array(self):
        lr = compute_band_level_range_db(np.array([], dtype=np.float32))
        assert lr == 0.0

    def test_clipping_no_nan_inf(self, clipping, sample_rate):
        """Clipped signal must produce a finite result."""
        lr = compute_band_level_range_db(clipping, sample_rate)
        assert math.isfinite(lr)
        assert lr >= 0.0
