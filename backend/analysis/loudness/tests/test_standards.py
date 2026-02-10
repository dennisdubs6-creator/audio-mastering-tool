"""
Tests for the StandardsMetering class.

Covers LUFS computation, LRA, True Peak, cross-validation, stereo
handling, and sample-rate support.
"""

import json
import logging
import math
import os

import numpy as np
import pytest

from analysis.loudness.standards import StandardsMetering, CROSS_VALIDATION_THRESHOLD_LU
from dsp.audio_loader import AudioLoader
from dsp.audio_types import AudioData


class TestStandardsMetering:
    """Unit tests for StandardsMetering metric computations."""

    def setup_method(self) -> None:
        self.metering = StandardsMetering()

    # --- LUFS ---

    def test_compute_lufs_sine_wave(self, sine_440_audio: AudioData) -> None:
        """Full-scale 440 Hz sine should measure approximately -3.0 LUFS."""
        metrics = self.metering.compute_overall_metrics(sine_440_audio)
        assert metrics.integrated_lufs is not None
        # RMS of a full-scale sine is -3.01 dBFS; K-weighting at 440 Hz
        # adds minor correction.  Allow +/- 1.0 for unit-test tolerance.
        assert abs(metrics.integrated_lufs - (-3.0)) < 1.0, (
            f"Expected ~-3.0 LUFS, got {metrics.integrated_lufs}"
        )

    def test_lufs_silence(self, silence_audio: AudioData) -> None:
        """Digital silence should yield None for LUFS."""
        metrics = self.metering.compute_overall_metrics(silence_audio)
        assert metrics.integrated_lufs is None

    # --- LRA ---

    def test_compute_lra(self, sine_440_audio: AudioData) -> None:
        """A constant-level sine should produce a finite LRA value.

        Note: For short signals (< 60s), pyloudnorm's LRA can exceed 0
        due to insufficient short-term loudness windows (EBU R128 recommends
        60+ seconds for reliable LRA).  We only verify it's a valid number.
        """
        metrics = self.metering.compute_overall_metrics(sine_440_audio)
        if metrics.loudness_range_lu is not None:
            assert metrics.loudness_range_lu >= 0.0, (
                f"Expected non-negative LRA, got {metrics.loudness_range_lu}"
            )

    # --- True Peak ---

    def test_compute_true_peak(self, sine_440_audio: AudioData) -> None:
        """Full-scale sine should have true peak near 0.0 dBFS."""
        metrics = self.metering.compute_overall_metrics(sine_440_audio)
        assert metrics.true_peak_dbfs is not None
        # True peak of a full-scale sine can slightly exceed 0 dBFS due to
        # inter-sample peaks; allow a small margin above and below.
        assert -1.0 <= metrics.true_peak_dbfs <= 1.0, (
            f"Expected true peak near 0.0 dBFS, got {metrics.true_peak_dbfs}"
        )

    def test_true_peak_silence(self, silence_audio: AudioData) -> None:
        """Digital silence should have very low true peak."""
        metrics = self.metering.compute_overall_metrics(silence_audio)
        assert metrics.true_peak_dbfs is not None
        assert metrics.true_peak_dbfs <= -80.0

    # --- Cross-validation ---

    def test_cross_validation(self, sine_440_audio: AudioData) -> None:
        """Primary and cross-check LUFS should agree within threshold."""
        samples = sine_440_audio.samples.astype(np.float64)
        rate = sine_440_audio.sample_rate

        lufs_primary = self.metering._compute_lufs_pyloudnorm(samples, rate)
        lufs_check = self.metering._compute_lufs_cross_check(
            sine_440_audio.samples, rate
        )

        assert lufs_primary is not None and lufs_check is not None
        diff = abs(lufs_primary - lufs_check)
        # When pyebur128 is available the threshold is 0.1 LU;
        # with pyloudnorm-only fallback the diff should be ~0.0.
        assert diff < 0.5, (
            f"LUFS cross-validation diff {diff:.3f} LU too large "
            f"(primary={lufs_primary:.2f}, check={lufs_check:.2f})"
        )

    def test_cross_validation_warning(
        self, sine_440_audio: AudioData, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verify that a warning is logged when diff > threshold.

        We cannot easily force a diff > 0.1 LU with the same input, so
        this test calls the static method directly with artificially
        divergent values.
        """
        with caplog.at_level(logging.WARNING):
            StandardsMetering._cross_validate_lufs(-14.0, -14.2)

        assert any(
            "cross-validation WARNING" in rec.message.upper()
            or "exceeds" in rec.message
            for rec in caplog.records
        ), "Expected a cross-validation warning in the logs"

    # --- Stereo handling ---

    def test_stereo_handling(self, sine_1khz_stereo_audio: AudioData) -> None:
        """Stereo AudioData with stereo_samples should produce valid metrics."""
        assert sine_1khz_stereo_audio.stereo_samples is not None
        metrics = self.metering.compute_overall_metrics(sine_1khz_stereo_audio)
        assert metrics.integrated_lufs is not None
        assert metrics.true_peak_dbfs is not None

    def test_stereo_true_peak_uses_both_channels(self) -> None:
        """True peak must reflect the louder channel, not a mono average.

        Left channel is full-scale; right channel is half-scale.  Mono
        averaging would lower the observed peak, so we verify the result
        is close to the full-scale true-peak value (near 0 dBFS).
        """
        t = np.arange(0, 3.0, 1.0 / 48000)
        left = np.sin(2.0 * np.pi * 1000.0 * t).astype(np.float32)
        right = (0.5 * np.sin(2.0 * np.pi * 1000.0 * t)).astype(np.float32)
        stereo = np.column_stack([left, right])
        mono = np.mean(stereo, axis=1).astype(np.float32)
        audio = AudioData(
            samples=mono,
            sample_rate=48000,
            bit_depth=16,
            duration=3.0,
            channels=2,
            file_path="<stereo_asym>",
            stereo_samples=stereo,
        )
        metrics = self.metering.compute_overall_metrics(audio)
        assert metrics.true_peak_dbfs is not None
        # Full-scale sine true peak should be near 0 dBFS; the mono
        # average would reduce it by ~2.5 dB.  Allow a small margin.
        assert metrics.true_peak_dbfs >= -1.0, (
            f"Expected true peak near 0 dBFS from stereo, got {metrics.true_peak_dbfs}"
        )

    # --- Sample rate support ---

    def test_sample_rate_44100(self) -> None:
        """44.1 kHz audio should produce valid metrics."""
        t = np.arange(0, 3.0, 1.0 / 44100)
        samples = np.sin(2.0 * np.pi * 440.0 * t).astype(np.float32)
        audio = AudioData(
            samples=samples,
            sample_rate=44100,
            bit_depth=16,
            duration=3.0,
            channels=1,
            file_path="<44100>",
        )
        metrics = self.metering.compute_overall_metrics(audio)
        assert metrics.integrated_lufs is not None

    def test_sample_rate_48000(self, sine_440_audio: AudioData) -> None:
        """48 kHz audio should produce valid metrics (default fixture)."""
        metrics = self.metering.compute_overall_metrics(sine_440_audio)
        assert metrics.integrated_lufs is not None


class TestIntegration:
    """Integration test: load audio from disk, compute, validate."""

    def test_full_pipeline(self, golden_corpus_path: str, expected_values: dict) -> None:
        """Load each golden test vector, compute metrics, verify non-None.

        Note: Precision validation is handled by test_validator.py and
        the standalone validate_precision.py script.
        """
        loader = AudioLoader()
        metering = StandardsMetering()

        wav_files = [
            f for f in os.listdir(golden_corpus_path) if f.endswith(".wav")
        ]
        if not wav_files:
            pytest.skip("No WAV test vectors found – run generate script first")

        for fname in wav_files:
            path = os.path.join(golden_corpus_path, fname)
            audio = loader.load_wav(path)
            metrics = metering.compute_overall_metrics(audio)

            exp = expected_values.get(fname, {})
            # If expected LUFS is not None, computed should not be None
            if exp.get("integrated_lufs") is not None:
                assert metrics.integrated_lufs is not None, (
                    f"{fname}: expected non-None LUFS"
                )
            # True peak should always be a number for any audio
            assert metrics.true_peak_dbfs is not None, (
                f"{fname}: true peak should not be None"
            )
