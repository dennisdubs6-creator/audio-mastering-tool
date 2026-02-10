"""Tests for analysis.metrics.spectral module."""

import math

import numpy as np
import pytest

from analysis.metrics.spectral import (
    compute_energy_db,
    compute_energy_db_from_energy,
    compute_spectral_centroid_hz,
    compute_spectral_flatness,
    compute_spectral_rolloff_hz,
)

SAMPLE_RATE = 48000


class TestSpectralCentroid:
    def test_sine_440_centroid(self, sine_wave_440hz, sample_rate):
        """Centroid of a pure 440 Hz tone should be ≈ 440 Hz."""
        centroid = compute_spectral_centroid_hz(sine_wave_440hz, sample_rate)
        assert centroid == pytest.approx(440.0, abs=60.0)

    def test_white_noise_centroid(self, white_noise, sample_rate):
        """White noise centroid is broadband → well above 1 kHz."""
        centroid = compute_spectral_centroid_hz(white_noise, sample_rate)
        assert centroid > 1000.0

    def test_impulse_centroid(self, impulse, sample_rate):
        """Impulse has flat spectrum → centroid roughly mid-band."""
        centroid = compute_spectral_centroid_hz(impulse, sample_rate)
        assert centroid > 0.0
        assert math.isfinite(centroid)

    def test_silence(self, silence, sample_rate):
        centroid = compute_spectral_centroid_hz(silence, sample_rate)
        assert centroid == 0.0

    def test_empty(self):
        centroid = compute_spectral_centroid_hz(
            np.array([], dtype=np.float32), SAMPLE_RATE
        )
        assert centroid == 0.0

    def test_clipping_no_nan_inf(self, clipping, sample_rate):
        """Clipped signal must produce a finite result."""
        centroid = compute_spectral_centroid_hz(clipping, sample_rate)
        assert math.isfinite(centroid)
        assert centroid > 0.0


class TestSpectralRolloff:
    def test_sine_wave_rolloff(self, sine_wave_440hz, sample_rate):
        """Roll-off for a pure tone should be near the tone frequency."""
        rolloff = compute_spectral_rolloff_hz(sine_wave_440hz, sample_rate)
        assert rolloff > 0.0

    def test_white_noise_rolloff(self, white_noise, sample_rate):
        """White noise rolloff should be high (energy spread across spectrum)."""
        rolloff = compute_spectral_rolloff_hz(white_noise, sample_rate)
        assert rolloff > 1000.0

    def test_impulse_rolloff(self, impulse, sample_rate):
        """Impulse has flat spectrum → high rolloff."""
        rolloff = compute_spectral_rolloff_hz(impulse, sample_rate)
        assert rolloff > 0.0
        assert math.isfinite(rolloff)

    def test_silence(self, silence, sample_rate):
        rolloff = compute_spectral_rolloff_hz(silence, sample_rate)
        assert rolloff == 0.0

    def test_clipping_no_nan_inf(self, clipping, sample_rate):
        """Clipped signal must produce a finite result."""
        rolloff = compute_spectral_rolloff_hz(clipping, sample_rate)
        assert math.isfinite(rolloff)
        assert rolloff > 0.0


class TestSpectralFlatness:
    def test_white_noise_high_flatness(self, white_noise):
        """White noise should have high spectral flatness (uniform distribution
        with STFT windowing yields ~0.56 via librosa, well above tonal signals)."""
        flatness = compute_spectral_flatness(white_noise)
        assert flatness > 0.5

    def test_sine_wave_low_flatness(self, sine_wave_440hz):
        """Pure tone should have very low spectral flatness."""
        flatness = compute_spectral_flatness(sine_wave_440hz)
        assert flatness < 0.1

    def test_impulse_flatness(self, impulse):
        """Impulse has flat spectrum → high flatness."""
        flatness = compute_spectral_flatness(impulse)
        assert math.isfinite(flatness)
        # Allow tiny floating-point overshoot above 1.0
        assert flatness >= 0.0
        assert flatness == pytest.approx(1.0, abs=0.1)

    def test_silence(self, silence):
        flatness = compute_spectral_flatness(silence)
        assert flatness == 0.0

    def test_clipping_no_nan_inf(self, clipping):
        """Clipped signal must produce a finite result."""
        flatness = compute_spectral_flatness(clipping)
        assert math.isfinite(flatness)
        assert 0.0 <= flatness <= 1.0


class TestEnergyDb:
    def test_nonzero_signal(self, sine_wave_440hz):
        magnitude = np.abs(sine_wave_440hz)
        e = compute_energy_db(magnitude)
        assert e > -120.0

    def test_white_noise_energy(self, white_noise):
        """White noise should have significant energy."""
        magnitude = np.abs(white_noise)
        e = compute_energy_db(magnitude)
        assert math.isfinite(e)
        assert e > -120.0

    def test_silence(self, silence):
        e = compute_energy_db(silence)
        assert e == -120.0

    def test_empty(self):
        e = compute_energy_db(np.array([], dtype=np.float32))
        assert e == -120.0

    def test_clipping_no_nan_inf(self, clipping):
        """Clipped signal must produce a finite result."""
        magnitude = np.abs(clipping)
        e = compute_energy_db(magnitude)
        assert math.isfinite(e)
        assert e > -120.0


class TestEnergyDbFromEnergy:
    def test_known_value(self):
        """10*log10(100/1) = 20 dB with 1 frame."""
        e = compute_energy_db_from_energy(100.0, num_frames=1)
        assert e == pytest.approx(20.0, abs=0.01)

    def test_normalization(self):
        """10*log10(100/10) = 10 dB with 10 frames."""
        e = compute_energy_db_from_energy(100.0, num_frames=10)
        assert e == pytest.approx(10.0, abs=0.01)

    def test_zero_energy(self):
        e = compute_energy_db_from_energy(0.0, num_frames=1)
        assert e == -120.0

    def test_near_zero_energy(self):
        e = compute_energy_db_from_energy(1e-12, num_frames=1)
        assert e == -120.0

    def test_positive_energy_finite(self):
        e = compute_energy_db_from_energy(42.0, num_frames=1)
        assert math.isfinite(e)
        assert e > -120.0
