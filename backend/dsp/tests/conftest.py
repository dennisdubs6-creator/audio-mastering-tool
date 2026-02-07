"""
DSP Test Fixtures

Provides pytest fixtures for generating reference audio files and
pre-computed DSP data structures used across the test suite.
"""

import os
import tempfile

import numpy as np
import pytest
import soundfile as sf

from dsp.audio_loader import AudioLoader
from dsp.audio_types import AudioData, STFTData
from dsp.stft_processor import STFTProcessor


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")


def generate_sine_wave(
    frequency: float = 440.0,
    duration: float = 3.0,
    sample_rate: int = 48000,
    bit_depth: int = 16,
    channels: int = 1,
) -> str:
    """Generate a pure sine wave and write it to a temporary WAV file.

    Args:
        frequency: Sine wave frequency in Hz.
        duration: Duration in seconds.
        sample_rate: Sample rate in Hz.
        bit_depth: Bit depth (16 or 24).
        channels: Number of channels (1 = mono, 2 = stereo).

    Returns:
        Absolute path to the generated WAV file.
    """
    t = np.arange(0, duration, 1.0 / sample_rate)
    samples = np.sin(2.0 * np.pi * frequency * t)

    if channels == 2:
        samples = np.column_stack([samples, samples])

    subtype = "PCM_16" if bit_depth == 16 else "PCM_24"

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)

    sf.write(path, samples, sample_rate, subtype=subtype)
    return path


@pytest.fixture
def test_sine_wave_440hz() -> str:
    """Fixture that yields the path to a 440 Hz mono sine wave (48 kHz, 16-bit, 3 s)."""
    path = generate_sine_wave(frequency=440.0, duration=3.0, sample_rate=48000, bit_depth=16)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def sample_audio_data(test_sine_wave_440hz: str) -> AudioData:
    """Pre-loaded AudioData from the 440 Hz test fixture."""
    loader = AudioLoader()
    return loader.load_wav(test_sine_wave_440hz)


@pytest.fixture
def sample_stft_data(sample_audio_data: AudioData) -> STFTData:
    """Pre-computed STFTData from the 440 Hz test audio."""
    processor = STFTProcessor()
    return processor.compute_stft(sample_audio_data)
