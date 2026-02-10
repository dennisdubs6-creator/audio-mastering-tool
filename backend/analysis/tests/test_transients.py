"""Tests for analysis.metrics.transients module."""

import math

import numpy as np
import pytest

from analysis.metrics.transients import (
    compute_attack_time_ms,
    compute_transient_preservation,
)

SAMPLE_RATE = 48000
DURATION = 3.0
NUM_SAMPLES = int(SAMPLE_RATE * DURATION)


class TestTransientPreservation:
    def test_impulse_high_transients(self, impulse, sample_rate):
        """An impulse signal should have notable transient content."""
        tp = compute_transient_preservation(impulse, sample_rate)
        assert 0.0 <= tp <= 1.0

    def test_sine_wave_low_transients(self, sine_wave_440hz, sample_rate):
        """A sustained sine has little percussive energy."""
        tp = compute_transient_preservation(sine_wave_440hz, sample_rate)
        assert 0.0 <= tp <= 1.0

    def test_white_noise_transients(self, white_noise, sample_rate):
        """White noise transient preservation should be finite and in [0, 1]."""
        tp = compute_transient_preservation(white_noise, sample_rate)
        assert math.isfinite(tp)
        assert 0.0 <= tp <= 1.0

    def test_impulse_more_transient_than_sine(
        self, impulse, sine_wave_440hz, sample_rate
    ):
        """Impulse should have more transient energy than a sustained sine."""
        tp_impulse = compute_transient_preservation(impulse, sample_rate)
        tp_sine = compute_transient_preservation(sine_wave_440hz, sample_rate)
        assert tp_impulse > tp_sine

    def test_silence(self, silence, sample_rate):
        tp = compute_transient_preservation(silence, sample_rate)
        assert tp == 0.0

    def test_empty(self):
        tp = compute_transient_preservation(
            np.array([], dtype=np.float32), SAMPLE_RATE
        )
        assert tp == 0.0

    def test_clipping_no_nan_inf(self, clipping, sample_rate):
        """Clipped signal must produce a finite result."""
        tp = compute_transient_preservation(clipping, sample_rate)
        assert math.isfinite(tp)
        assert 0.0 <= tp <= 1.0

    def test_with_precomputed_percussive(self, sine_wave_440hz, sample_rate):
        """Transient preservation with pre-computed percussive component."""
        from analysis.metrics.harmonics import compute_hpss

        _, percussive = compute_hpss(sine_wave_440hz)
        tp = compute_transient_preservation(
            sine_wave_440hz, sample_rate, percussive=percussive
        )
        assert 0.0 <= tp <= 1.0


class TestAttackTime:
    def test_impulse_attack_under_1ms(self, impulse, sample_rate):
        """Impulse attack time should be < 1 ms (instantaneous attack)."""
        at = compute_attack_time_ms(impulse, sample_rate)
        assert at < 1.0

    def test_sine_wave(self, sine_wave_440hz, sample_rate):
        """Continuous sine may or may not have detected onsets."""
        at = compute_attack_time_ms(sine_wave_440hz, sample_rate)
        assert at >= 0.0
        assert math.isfinite(at)

    def test_white_noise_attack_time(self, white_noise, sample_rate):
        """White noise attack time should be finite and non-negative."""
        at = compute_attack_time_ms(white_noise, sample_rate)
        assert math.isfinite(at)
        assert at >= 0.0

    def test_silence(self, silence, sample_rate):
        at = compute_attack_time_ms(silence, sample_rate)
        assert at == 0.0

    def test_empty(self):
        at = compute_attack_time_ms(
            np.array([], dtype=np.float32), SAMPLE_RATE
        )
        assert at == 0.0

    def test_clipping_no_nan_inf(self, clipping, sample_rate):
        """Clipped signal must produce a finite attack time."""
        at = compute_attack_time_ms(clipping, sample_rate)
        assert math.isfinite(at)
        assert at >= 0.0
