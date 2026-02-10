"""Integration tests for ``AnalysisEngine.analyze_audio``.

Runs the full analysis pipeline on a short synthesized WAV fixture and
verifies that:
- exactly five ``BandMetrics`` objects are returned (one per band),
- each ``BandMetrics`` contains populated metric fields,
- the progress callback is invoked once per band with metric data.
"""

import os
import tempfile
import wave

import numpy as np
import pytest

from analysis.engine import AnalysisEngine
from api.models import BandMetrics, OverallMetrics
from config.constants import BAND_NAMES
from dsp.audio_loader import AudioLoader
from dsp.band_integrator import BandIntegrator
from dsp.stft_processor import STFTProcessor
from config.constants import FREQUENCY_BANDS


SAMPLE_RATE = 48000
DURATION = 1.0  # 1 second – short enough for fast tests
NUM_SAMPLES = int(SAMPLE_RATE * DURATION)

# --- Metric field names expected on every BandMetrics ---
_METRIC_FIELDS = [
    "band_rms_dbfs",
    "band_true_peak_dbfs",
    "band_level_range_db",
    "dynamic_range_db",
    "crest_factor_db",
    "rms_db",
    "spectral_centroid_hz",
    "spectral_rolloff_hz",
    "spectral_flatness",
    "energy_db",
    "thd_percent",
    "harmonic_ratio",
    "inharmonicity",
    "transient_preservation",
    "attack_time_ms",
]


@pytest.fixture()
def short_wav_path() -> str:
    """Write a 1-second 48 kHz mono WAV with broadband content to a temp file.

    A mix of a 440 Hz sine and white noise ensures all five bands
    contain measurable energy.
    """
    t = np.linspace(0, DURATION, NUM_SAMPLES, endpoint=False)
    sine = 0.5 * np.sin(2.0 * np.pi * 440.0 * t)
    rng = np.random.default_rng(seed=42)
    noise = 0.1 * rng.uniform(-1.0, 1.0, size=NUM_SAMPLES)
    samples = (sine + noise).astype(np.float32)

    # Scale to 16-bit PCM
    pcm = (samples * 32767).astype(np.int16)

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())

    yield path

    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture()
def engine() -> AnalysisEngine:
    return AnalysisEngine(
        stft_processor=STFTProcessor(),
        band_integrator=BandIntegrator(FREQUENCY_BANDS),
        audio_loader=AudioLoader(),
    )


class TestAnalyzeAudioEndToEnd:
    """End-to-end tests for ``AnalysisEngine.analyze_audio``."""

    def test_returns_five_band_metrics(self, engine, short_wav_path):
        """The engine must return exactly five BandMetrics (one per band)."""
        band_metrics, overall = engine.analyze_audio(
            file_path=short_wav_path,
            analysis_id="test-id-001",
        )

        assert len(band_metrics) == 5
        returned_names = {bm.band_name for bm in band_metrics}
        assert returned_names == set(BAND_NAMES)

    def test_band_metrics_have_populated_fields(self, engine, short_wav_path):
        """Each BandMetrics must have non-None values for core metric fields."""
        band_metrics, _ = engine.analyze_audio(
            file_path=short_wav_path,
            analysis_id="test-id-002",
        )

        for bm in band_metrics:
            assert isinstance(bm, BandMetrics)
            assert bm.band_name in BAND_NAMES
            assert isinstance(bm.freq_min, int)
            assert isinstance(bm.freq_max, int)

            # At least the level / dynamics / spectral metrics should be set
            for field in _METRIC_FIELDS:
                value = getattr(bm, field)
                assert value is not None, (
                    f"BandMetrics.{field} is None for band '{bm.band_name}'"
                )

    def test_overall_metrics_populated(self, engine, short_wav_path):
        """OverallMetrics must contain integrated LUFS and true peak.

        Note: ``loudness_range_lu`` may be ``None`` for very short clips
        because EBU R128 LRA requires a minimum number of gating blocks.
        """
        _, overall = engine.analyze_audio(
            file_path=short_wav_path,
            analysis_id="test-id-003",
        )

        assert isinstance(overall, OverallMetrics)
        assert overall.integrated_lufs is not None
        assert overall.true_peak_dbfs is not None

    def test_progress_callback_invoked_per_band(self, engine, short_wav_path):
        """The progress callback must fire once per band with metric data."""
        progress_calls: list[tuple[str, dict]] = []

        def on_progress(band_name: str, metrics: dict) -> None:
            progress_calls.append((band_name, metrics))

        engine.analyze_audio(
            file_path=short_wav_path,
            analysis_id="test-id-004",
            progress_callback=on_progress,
        )

        assert len(progress_calls) == 5
        callback_band_names = {name for name, _ in progress_calls}
        assert callback_band_names == set(BAND_NAMES)

        for _, metrics_dict in progress_calls:
            assert isinstance(metrics_dict, dict)
            assert len(metrics_dict) > 0

    def test_fewer_bands_detected_fails(self, engine, short_wav_path):
        """Sanity guard: if we somehow got <5 bands the test suite notices."""
        band_metrics, _ = engine.analyze_audio(
            file_path=short_wav_path,
            analysis_id="test-id-005",
        )
        # This assertion will fail loudly if the engine ever returns
        # fewer than 5 bands, catching regressions.
        assert len(band_metrics) == 5, (
            f"Expected 5 band metrics, got {len(band_metrics)}"
        )
