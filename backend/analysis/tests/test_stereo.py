"""Tests for analysis.metrics.stereo module."""

import math

import numpy as np
import pytest

from analysis.metrics.stereo import (
    compute_mid_energy_db,
    compute_phase_correlation,
    compute_side_energy_db,
    compute_stereo_width_percent,
)

NUM_SAMPLES = 48000 * 3


class TestStereoWidth:
    def test_mono_identical_channels(self):
        """Identical L/R should give 0 % width."""
        sig = np.sin(np.linspace(0, 100, NUM_SAMPLES)).astype(np.float32)
        width = compute_stereo_width_percent(sig, sig.copy())
        assert width is not None
        assert width == pytest.approx(0.0, abs=1.0)

    def test_opposite_phase_full_width(self):
        """L = signal, R = -signal should give 100 % width."""
        sig = np.sin(np.linspace(0, 100, NUM_SAMPLES)).astype(np.float32)
        width = compute_stereo_width_percent(sig, -sig)
        assert width is not None
        assert width == pytest.approx(100.0, abs=1.0)

    def test_hard_panned_stereo_full_width(self, hard_panned_stereo):
        """Hard-panned stereo (L=signal, R=-signal) → ~100% width."""
        left, right = hard_panned_stereo
        width = compute_stereo_width_percent(left, right)
        assert width is not None
        assert width == pytest.approx(100.0, abs=1.0)

    def test_stereo_content(self, stereo_test):
        left, right = stereo_test
        width = compute_stereo_width_percent(left, right)
        assert width is not None
        assert 0.0 < width < 100.0

    def test_none_inputs(self):
        assert compute_stereo_width_percent(None, None) is None

    def test_silence(self, silence):
        width = compute_stereo_width_percent(silence, silence)
        assert width == 0.0

    def test_clipping_no_nan_inf(self, clipping):
        """Clipped stereo signal must produce a finite result."""
        width = compute_stereo_width_percent(clipping, -clipping)
        assert width is not None
        assert math.isfinite(width)


class TestPhaseCorrelation:
    def test_identical_channels(self):
        sig = np.sin(np.linspace(0, 100, NUM_SAMPLES)).astype(np.float32)
        corr = compute_phase_correlation(sig, sig.copy())
        assert corr is not None
        assert corr == pytest.approx(1.0, abs=0.01)

    def test_opposite_phase(self):
        sig = np.sin(np.linspace(0, 100, NUM_SAMPLES)).astype(np.float32)
        corr = compute_phase_correlation(sig, -sig)
        assert corr is not None
        assert corr == pytest.approx(-1.0, abs=0.01)

    def test_hard_panned_stereo_correlation(self, hard_panned_stereo):
        """Hard-panned (L=signal, R=-signal) → correlation ≈ -1.0."""
        left, right = hard_panned_stereo
        corr = compute_phase_correlation(left, right)
        assert corr is not None
        assert corr == pytest.approx(-1.0, abs=0.01)

    def test_uncorrelated(self, stereo_test):
        left, right = stereo_test
        corr = compute_phase_correlation(left, right)
        assert corr is not None
        assert -1.0 <= corr <= 1.0

    def test_none_inputs(self):
        assert compute_phase_correlation(None, None) is None

    def test_silence(self, silence):
        assert compute_phase_correlation(silence, silence) is None

    def test_clipping_no_nan_inf(self, clipping):
        """Clipped signal must produce a finite correlation."""
        corr = compute_phase_correlation(clipping, -clipping)
        assert corr is not None
        assert math.isfinite(corr)


class TestMidEnergy:
    def test_identical_channels(self):
        sig = np.sin(np.linspace(0, 100, NUM_SAMPLES)).astype(np.float32)
        mid_e = compute_mid_energy_db(sig, sig.copy())
        assert mid_e is not None
        assert mid_e > -120.0

    def test_hard_panned_stereo_no_mid(self, hard_panned_stereo):
        """Hard-panned (L=-R) → mid cancels → floor energy."""
        left, right = hard_panned_stereo
        mid_e = compute_mid_energy_db(left, right)
        assert mid_e is not None
        assert mid_e == -120.0

    def test_none_inputs(self):
        assert compute_mid_energy_db(None, None) is None

    def test_silence(self, silence):
        mid_e = compute_mid_energy_db(silence, silence)
        assert mid_e == -120.0

    def test_clipping_no_nan_inf(self, clipping):
        """Clipped signal must produce a finite mid energy."""
        mid_e = compute_mid_energy_db(clipping, clipping)
        assert mid_e is not None
        assert math.isfinite(mid_e)


class TestSideEnergy:
    def test_identical_channels_no_side(self):
        """Identical L/R means zero side energy."""
        sig = np.sin(np.linspace(0, 100, NUM_SAMPLES)).astype(np.float32)
        side_e = compute_side_energy_db(sig, sig.copy())
        assert side_e is not None
        assert side_e == -120.0

    def test_opposite_phase_high_side(self):
        sig = np.sin(np.linspace(0, 100, NUM_SAMPLES)).astype(np.float32)
        side_e = compute_side_energy_db(sig, -sig)
        assert side_e is not None
        assert side_e > -120.0

    def test_hard_panned_stereo_high_side(self, hard_panned_stereo):
        """Hard-panned stereo has all energy in side channel."""
        left, right = hard_panned_stereo
        side_e = compute_side_energy_db(left, right)
        assert side_e is not None
        assert side_e > -120.0

    def test_none_inputs(self):
        assert compute_side_energy_db(None, None) is None

    def test_silence(self, silence):
        """Silence → floor side energy."""
        side_e = compute_side_energy_db(silence, silence)
        assert side_e is not None
        assert side_e == -120.0

    def test_clipping_no_nan_inf(self, clipping):
        """Clipped signal must produce a finite side energy."""
        side_e = compute_side_energy_db(clipping, -clipping)
        assert side_e is not None
        assert math.isfinite(side_e)
