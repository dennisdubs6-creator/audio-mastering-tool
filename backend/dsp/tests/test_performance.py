"""Performance test for the full DSP pipeline."""

import os
import time

import pytest

from dsp.audio_loader import AudioLoader
from dsp.band_integrator import BandIntegrator
from dsp.stft_processor import STFTProcessor
from dsp.tests.conftest import generate_sine_wave
from config.constants import FREQUENCY_BANDS


class TestPerformance:
    """The full pipeline must process 30 seconds of audio in < 5 seconds."""

    @pytest.mark.slow
    def test_processing_time_30s_audio(self) -> None:
        path = generate_sine_wave(
            frequency=440.0,
            duration=30.0,  # 30 seconds
            sample_rate=48000,
            bit_depth=16,
        )

        try:
            loader = AudioLoader()
            processor = STFTProcessor()
            integrator = BandIntegrator(FREQUENCY_BANDS)

            start = time.perf_counter()
            audio = loader.load_wav(path)
            stft_data = processor.compute_stft(audio)
            bands = integrator.integrate_bands(stft_data)
            elapsed = time.perf_counter() - start

            assert len(bands) == 5
            assert elapsed < 5.0, (
                f"Pipeline took {elapsed:.2f}s for 30s audio (limit 5s)"
            )
        finally:
            os.remove(path)
