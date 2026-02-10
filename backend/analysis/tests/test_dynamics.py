"""Tests for analysis.metrics.dynamics module."""

import math

import numpy as np
import pytest

from analysis.metrics.dynamics import (
    compute_crest_factor_db,
    compute_dynamic_range_db,
    compute_rms_db,
)


class TestDynamicRange:
    def test_sine_wave_low_dr(self, sine_wave_440hz):
        """Pure sine wave has near-constant RMS across frames → low DR."""
        dr = compute_dynamic_range_db(sine_wave_440hz)
        assert dr < 3.0

    def test_silence(self, silence):
        dr = compute_dynamic_range_db(silence)
        assert dr == 0.0

    def test_impulse_high_range(self, impulse):
        """Impulse: most frames silent, one loud → very high DR."""
        dr = compute_dynamic_range_db(impulse)
        assert dr > 20.0

    def test_noise_low_dr(self, white_noise):
        """White noise has consistent RMS across frames → low DR."""
        dr = compute_dynamic_range_db(white_noise)
        assert dr < 3.0

    def test_empty(self):
        dr = compute_dynamic_range_db(np.array([], dtype=np.float32))
        assert dr == 0.0

    def test_differentiation_from_crest_factor(self, sine_wave_440hz):
        """DR and CF should yield meaningfully different values."""
        dr = compute_dynamic_range_db(sine_wave_440hz)
        cf = compute_crest_factor_db(sine_wave_440hz)
        assert abs(dr - cf) > 1.0

    def test_clipping_no_nan_inf(self, clipping):
        """Clipped signal must produce a finite result."""
        dr = compute_dynamic_range_db(clipping)
        assert math.isfinite(dr)
        assert dr >= 0.0


class TestCrestFactor:
    def test_sine_wave_approx_3db(self, sine_wave_440hz):
        cf = compute_crest_factor_db(sine_wave_440hz)
        assert cf == pytest.approx(3.01, abs=1.0)

    def test_white_noise_crest_factor(self, white_noise):
        """White noise crest factor is positive and finite."""
        cf = compute_crest_factor_db(white_noise)
        assert math.isfinite(cf)
        assert cf > 0.0

    def test_impulse_high_crest(self, impulse):
        """Impulse has enormous peak-to-RMS ratio."""
        cf = compute_crest_factor_db(impulse)
        assert cf > 20.0

    def test_constant_zero_crest(self):
        samples = np.full(1000, 0.5, dtype=np.float32)
        cf = compute_crest_factor_db(samples)
        assert cf == pytest.approx(0.0, abs=0.01)

    def test_silence(self, silence):
        cf = compute_crest_factor_db(silence)
        assert cf == 0.0

    def test_clipping_no_nan_inf(self, clipping):
        """Clipped signal must produce a finite result."""
        cf = compute_crest_factor_db(clipping)
        assert math.isfinite(cf)
        assert cf >= 0.0


class TestRmsDb:
    def test_full_scale_sine(self, sine_wave_440hz):
        """Full-scale sine RMS should be ~-3.01 dBFS."""
        rms = compute_rms_db(sine_wave_440hz)
        assert rms == pytest.approx(-3.01, abs=0.5)

    def test_white_noise_rms(self, white_noise):
        """Uniform [-1,1] white noise RMS ≈ -4.77 dBFS."""
        rms = compute_rms_db(white_noise)
        assert rms == pytest.approx(-4.77, abs=1.0)

    def test_impulse_rms(self, impulse):
        """Single-sample impulse → very low RMS."""
        rms = compute_rms_db(impulse)
        assert rms < -50.0

    def test_silence(self, silence):
        rms = compute_rms_db(silence)
        assert rms == -120.0

    def test_known_value(self):
        samples = np.full(1000, 0.5, dtype=np.float32)
        rms = compute_rms_db(samples)
        assert rms == pytest.approx(20.0 * np.log10(0.5), abs=0.1)

    def test_clipping_no_nan_inf(self, clipping):
        """Clipped signal must produce a finite result."""
        rms = compute_rms_db(clipping)
        assert math.isfinite(rms)
        assert rms > -3.01  # more energy than pure sine
