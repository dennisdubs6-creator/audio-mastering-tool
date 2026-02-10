"""Tests for analysis.metrics.harmonics module."""

import math

import numpy as np
import pytest

from analysis.metrics.harmonics import (
    compute_harmonic_ratio,
    compute_hpss,
    compute_inharmonicity,
    compute_thd_percent,
)

SAMPLE_RATE = 48000
DURATION = 3.0
NUM_SAMPLES = int(SAMPLE_RATE * DURATION)


class TestHpss:
    def test_returns_two_components(self, sine_wave_440hz):
        """HPSS returns harmonic and percussive arrays of correct length."""
        harmonic, percussive = compute_hpss(sine_wave_440hz)
        assert harmonic.size > 0
        assert percussive.size > 0
        assert harmonic.dtype == np.float32
        assert percussive.dtype == np.float32

    def test_silence_returns_empty(self, silence):
        harmonic, percussive = compute_hpss(silence)
        assert harmonic.size == 0
        assert percussive.size == 0

    def test_empty_returns_empty(self):
        harmonic, percussive = compute_hpss(np.array([], dtype=np.float32))
        assert harmonic.size == 0
        assert percussive.size == 0

    def test_white_noise_no_nan_inf(self, white_noise):
        """HPSS on white noise should produce finite values."""
        harmonic, percussive = compute_hpss(white_noise)
        assert np.all(np.isfinite(harmonic))
        assert np.all(np.isfinite(percussive))


class TestThdPercent:
    def test_pure_sine_low_thd(self, sine_wave_440hz, sample_rate):
        """A pure sine wave should have near-zero THD."""
        thd = compute_thd_percent(sine_wave_440hz, sample_rate)
        assert 0.0 <= thd < 30.0

    def test_white_noise_thd(self, white_noise, sample_rate):
        """White noise THD should be a finite value."""
        thd = compute_thd_percent(white_noise, sample_rate)
        assert math.isfinite(thd)
        assert thd >= 0.0

    def test_impulse_thd(self, impulse, sample_rate):
        """Impulse THD should be a finite value."""
        thd = compute_thd_percent(impulse, sample_rate)
        assert math.isfinite(thd)
        assert thd >= 0.0

    def test_silence(self, silence, sample_rate):
        thd = compute_thd_percent(silence, sample_rate)
        assert thd == 0.0

    def test_empty(self):
        thd = compute_thd_percent(np.array([], dtype=np.float32), SAMPLE_RATE)
        assert thd == 0.0

    def test_clipping_no_nan_inf(self, clipping, sample_rate):
        """Clipped signal must produce a finite THD."""
        thd = compute_thd_percent(clipping, sample_rate)
        assert math.isfinite(thd)
        assert thd >= 0.0

    def test_with_precomputed_harmonic(self, sine_wave_440hz, sample_rate):
        """THD with pre-computed harmonic should match standalone call."""
        harmonic, _ = compute_hpss(sine_wave_440hz)
        thd = compute_thd_percent(
            sine_wave_440hz, sample_rate, harmonic=harmonic
        )
        assert 0.0 <= thd < 30.0


class TestHarmonicRatio:
    def test_sine_wave_high_ratio(self, sine_wave_440hz):
        """A pure sine wave should be mostly harmonic."""
        ratio = compute_harmonic_ratio(sine_wave_440hz)
        assert 0.0 <= ratio <= 1.0

    def test_noise_lower_ratio(self, white_noise):
        """White noise has less harmonic structure than a sine."""
        ratio = compute_harmonic_ratio(white_noise)
        assert 0.0 <= ratio <= 1.0

    def test_impulse_ratio(self, impulse):
        """Impulse harmonic ratio should be finite and in [0, 1]."""
        ratio = compute_harmonic_ratio(impulse)
        assert math.isfinite(ratio)
        assert 0.0 <= ratio <= 1.0

    def test_silence(self, silence):
        ratio = compute_harmonic_ratio(silence)
        assert ratio == 0.0

    def test_empty(self):
        ratio = compute_harmonic_ratio(np.array([], dtype=np.float32))
        assert ratio == 0.0

    def test_clipping_no_nan_inf(self, clipping):
        """Clipped signal must produce a finite harmonic ratio."""
        ratio = compute_harmonic_ratio(clipping)
        assert math.isfinite(ratio)
        assert 0.0 <= ratio <= 1.0

    def test_sine_more_harmonic_than_noise(self, sine_wave_440hz, white_noise):
        """Sine should have a higher harmonic ratio than white noise."""
        sine_ratio = compute_harmonic_ratio(sine_wave_440hz)
        noise_ratio = compute_harmonic_ratio(white_noise)
        assert sine_ratio > noise_ratio


class TestInharmonicity:
    def test_sine_wave_low_inharmonicity(self, sine_wave_440hz, sample_rate):
        """Pure sine should have very low inharmonicity."""
        inh = compute_inharmonicity(sine_wave_440hz, sample_rate)
        assert 0.0 <= inh <= 1.0

    def test_white_noise_inharmonicity(self, white_noise, sample_rate):
        """White noise inharmonicity should be finite."""
        inh = compute_inharmonicity(white_noise, sample_rate)
        assert math.isfinite(inh)
        assert 0.0 <= inh <= 1.0

    def test_silence(self, silence, sample_rate):
        inh = compute_inharmonicity(silence, sample_rate)
        assert inh == 0.0

    def test_empty(self):
        inh = compute_inharmonicity(
            np.array([], dtype=np.float32), SAMPLE_RATE
        )
        assert inh == 0.0

    def test_clipping_no_nan_inf(self, clipping, sample_rate):
        """Clipped signal must produce a finite inharmonicity."""
        inh = compute_inharmonicity(clipping, sample_rate)
        assert math.isfinite(inh)
        assert 0.0 <= inh <= 1.0
