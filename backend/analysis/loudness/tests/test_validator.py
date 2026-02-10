"""
Tests for the PrecisionValidator class.

Covers tolerance checks, edge cases, report generation, and golden
corpus validation.
"""

import json
import os

import pytest

from analysis.loudness.standards import StandardsMetering
from analysis.loudness.validator import (
    LUFS_TOLERANCE,
    LRA_TOLERANCE,
    TRUE_PEAK_TOLERANCE,
    PrecisionValidator,
    ValidationResult,
)
from api.models import OverallMetrics
from dsp.audio_loader import AudioLoader


class TestPrecisionValidator:
    """Unit tests for PrecisionValidator tolerance checks."""

    def setup_method(self) -> None:
        self.validator = PrecisionValidator()

    def _make_metrics(
        self,
        lufs: float | None = -14.0,
        tp: float | None = -1.0,
        lra: float | None = 7.0,
    ) -> OverallMetrics:
        return OverallMetrics(
            integrated_lufs=lufs,
            true_peak_dbfs=tp,
            loudness_range_lu=lra,
        )

    # --- Pass cases ---

    def test_validation_pass(self) -> None:
        """Metrics exactly matching expected values should pass."""
        computed = self._make_metrics(lufs=-14.0, tp=-1.0, lra=7.0)
        expected = {
            "integrated_lufs": -14.0,
            "true_peak_dbfs": -1.0,
            "loudness_range_lu": 7.0,
        }
        result = self.validator.validate_against_expected(computed, expected)
        assert result.overall_pass
        assert result.lufs_diff == 0.0
        assert result.true_peak_diff == 0.0
        assert result.lra_diff == 0.0

    def test_validation_pass_within_tolerance(self) -> None:
        """Metrics within tolerance should pass."""
        computed = self._make_metrics(lufs=-14.05, tp=-1.1, lra=7.15)
        expected = {
            "integrated_lufs": -14.0,
            "true_peak_dbfs": -1.0,
            "loudness_range_lu": 7.0,
        }
        result = self.validator.validate_against_expected(computed, expected)
        assert result.overall_pass

    def test_validation_pass_both_none(self) -> None:
        """Both computed and expected None should pass (silence LUFS)."""
        computed = self._make_metrics(lufs=None, tp=-120.0, lra=None)
        expected = {
            "integrated_lufs": None,
            "true_peak_dbfs": -120.0,
            "loudness_range_lu": None,
        }
        result = self.validator.validate_against_expected(computed, expected)
        assert result.overall_pass

    # --- Fail cases ---

    def test_validation_fail_lufs(self) -> None:
        """LUFS outside tolerance should fail."""
        computed = self._make_metrics(lufs=-14.2, tp=-1.0, lra=7.0)
        expected = {
            "integrated_lufs": -14.0,
            "true_peak_dbfs": -1.0,
            "loudness_range_lu": 7.0,
        }
        result = self.validator.validate_against_expected(computed, expected)
        assert not result.lufs_pass
        assert not result.overall_pass
        assert result.lufs_diff == pytest.approx(0.2, abs=0.001)

    def test_validation_fail_true_peak(self) -> None:
        """True Peak outside tolerance should fail."""
        computed = self._make_metrics(lufs=-14.0, tp=-1.3, lra=7.0)
        expected = {
            "integrated_lufs": -14.0,
            "true_peak_dbfs": -1.0,
            "loudness_range_lu": 7.0,
        }
        result = self.validator.validate_against_expected(computed, expected)
        assert not result.true_peak_pass
        assert not result.overall_pass

    def test_validation_fail_lra(self) -> None:
        """LRA outside tolerance should fail."""
        computed = self._make_metrics(lufs=-14.0, tp=-1.0, lra=7.3)
        expected = {
            "integrated_lufs": -14.0,
            "true_peak_dbfs": -1.0,
            "loudness_range_lu": 7.0,
        }
        result = self.validator.validate_against_expected(computed, expected)
        assert not result.lra_pass
        assert not result.overall_pass

    def test_validation_fail_none_mismatch(self) -> None:
        """Computed None but expected non-None should fail."""
        computed = self._make_metrics(lufs=None, tp=-1.0, lra=7.0)
        expected = {
            "integrated_lufs": -14.0,
            "true_peak_dbfs": -1.0,
            "loudness_range_lu": 7.0,
        }
        result = self.validator.validate_against_expected(computed, expected)
        assert not result.lufs_pass
        assert not result.overall_pass

    # --- Report generation ---

    def test_validation_report_generation(self) -> None:
        """Report should contain Markdown table headers and verdict."""
        computed = self._make_metrics()
        expected = {
            "integrated_lufs": -14.0,
            "true_peak_dbfs": -1.0,
            "loudness_range_lu": 7.0,
            "description": "Test signal",
        }
        result = self.validator.validate_against_expected(computed, expected)
        report = self.validator.generate_validation_report(
            {"test.wav": result},
            {"test.wav": expected},
        )
        assert "# Loudness Metering Precision Validation Report" in report
        assert "| Test File" in report
        assert "PASS" in report or "FAIL" in report
        assert "Overall Verdict" in report


class TestGoldenCorpus:
    """Validate computed metrics against golden corpus expected values."""

    def test_all_vectors_pass(
        self, golden_corpus_path: str, expected_values: dict
    ) -> None:
        """All golden test vectors should pass precision validation."""
        loader = AudioLoader()
        metering = StandardsMetering()
        validator = PrecisionValidator()

        wav_files = [
            f for f in os.listdir(golden_corpus_path) if f.endswith(".wav")
        ]
        if not wav_files:
            pytest.skip("No WAV test vectors found – run generate script first")

        failures: list[str] = []
        for fname in sorted(wav_files):
            if fname not in expected_values:
                continue
            path = os.path.join(golden_corpus_path, fname)
            audio = loader.load_wav(path)
            metrics = metering.compute_overall_metrics(audio)
            result = validator.validate_against_expected(
                metrics, expected_values[fname]
            )
            if not result.overall_pass:
                failures.append(
                    f"{fname}: LUFS diff={result.lufs_diff:.3f} "
                    f"TP diff={result.true_peak_diff:.3f} "
                    f"LRA diff={result.lra_diff:.3f}"
                )

        assert not failures, (
            "Golden corpus validation failures:\n" + "\n".join(failures)
        )

    @pytest.mark.parametrize(
        "filename",
        [
            "sine_440hz.wav",
            "sine_1khz_stereo.wav",
            "white_noise.wav",
            "silence.wav",
            "pink_noise.wav",
            # EBU R128 / ITU-R BS.1770-4 compliance vectors (1 kHz)
            "ebu_r128_tone_stereo_23lufs.wav",
            "ebu_r128_tone_stereo_33lufs.wav",
            "ebu_r128_tone_mono_23lufs.wav",
            "ebu_r128_tone_with_silence.wav",
            "ebu_r128_two_tones.wav",
            # EBU R128 / ITU-R BS.1770-4 compliance vectors (997 Hz)
            "ebu_r128_stereo_997hz_23lufs.wav",
            "ebu_r128_stereo_997hz_33lufs.wav",
            "ebu_r128_mono_997hz_23lufs.wav",
            "ebu_r128_gate_test.wav",
            "ebu_r128_lra_test.wav",
        ],
    )
    def test_individual_vectors(
        self,
        filename: str,
        golden_corpus_path: str,
        expected_values: dict,
    ) -> None:
        """Each test vector individually must pass precision validation."""
        path = os.path.join(golden_corpus_path, filename)
        if not os.path.exists(path):
            pytest.skip(f"{filename} not found – run generate script first")

        loader = AudioLoader()
        metering = StandardsMetering()
        validator = PrecisionValidator()

        audio = loader.load_wav(path)
        metrics = metering.compute_overall_metrics(audio)
        expected = expected_values[filename]
        result = validator.validate_against_expected(metrics, expected)

        assert result.overall_pass, (
            f"{filename} FAILED: "
            f"LUFS={'PASS' if result.lufs_pass else 'FAIL'}(diff={result.lufs_diff:.3f}) "
            f"TP={'PASS' if result.true_peak_pass else 'FAIL'}(diff={result.true_peak_diff:.3f}) "
            f"LRA={'PASS' if result.lra_pass else 'FAIL'}(diff={result.lra_diff:.3f})"
        )
