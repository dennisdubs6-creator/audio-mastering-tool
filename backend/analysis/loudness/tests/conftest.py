"""
Pytest fixtures for loudness metering tests.

Provides access to the golden test vectors directory, expected values,
and audio file generation helpers.
"""

import json
import os
import tempfile

import numpy as np
import pytest
import soundfile as sf

from dsp.audio_types import AudioData

# Paths
_MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEST_VECTORS_DIR = os.path.join(_MODULE_DIR, "test_vectors")
_EXPECTED_VALUES_PATH = os.path.join(_TEST_VECTORS_DIR, "expected_values.json")


@pytest.fixture
def golden_corpus_path() -> str:
    """Return the absolute path to the test_vectors directory."""
    return _TEST_VECTORS_DIR


@pytest.fixture
def expected_values() -> dict:
    """Load and return the expected_values.json as a dict."""
    with open(_EXPECTED_VALUES_PATH, "r") as f:
        return json.load(f)


@pytest.fixture
def test_audio_files(golden_corpus_path: str) -> list[str]:
    """Return a list of absolute paths to all .wav files in test_vectors."""
    wav_files = []
    for fname in sorted(os.listdir(golden_corpus_path)):
        if fname.endswith(".wav"):
            wav_files.append(os.path.join(golden_corpus_path, fname))
    return wav_files


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


def make_audio_data(
    samples: np.ndarray,
    sample_rate: int = 48000,
    bit_depth: int = 16,
    channels: int = 1,
) -> AudioData:
    """Create an AudioData instance from raw samples without writing to disk.

    If *samples* is 2-D (multichannel), ``stereo_samples`` is populated
    with the untouched frames and ``samples`` receives the mono downmix.
    """
    arr = samples.astype(np.float32)
    stereo_samples: np.ndarray | None = None
    if arr.ndim == 2:
        stereo_samples = arr
        mono = np.mean(arr, axis=1).astype(np.float32)
    else:
        mono = arr
    return AudioData(
        samples=mono,
        sample_rate=sample_rate,
        bit_depth=bit_depth,
        duration=len(mono) / sample_rate,
        channels=channels,
        file_path="<in-memory>",
        stereo_samples=stereo_samples,
    )


@pytest.fixture
def sine_440_audio() -> AudioData:
    """Full-scale 440 Hz mono sine, 3 s, 48 kHz."""
    t = np.arange(0, 3.0, 1.0 / 48000)
    samples = np.sin(2.0 * np.pi * 440.0 * t).astype(np.float32)
    return AudioData(
        samples=samples,
        sample_rate=48000,
        bit_depth=16,
        duration=3.0,
        channels=1,
        file_path="<sine_440>",
    )


@pytest.fixture
def sine_1khz_stereo_audio() -> AudioData:
    """Full-scale 1 kHz stereo sine, 3 s, 48 kHz.

    Both channels carry the same signal.  ``stereo_samples`` holds the
    untouched 2-channel frames so that :class:`StandardsMetering` can
    meter them without a mono downmix.
    """
    t = np.arange(0, 3.0, 1.0 / 48000)
    mono = np.sin(2.0 * np.pi * 1000.0 * t).astype(np.float32)
    stereo = np.column_stack([mono, mono])
    return AudioData(
        samples=mono,
        sample_rate=48000,
        bit_depth=16,
        duration=3.0,
        channels=2,
        file_path="<sine_1khz_stereo>",
        stereo_samples=stereo,
    )


@pytest.fixture
def silence_audio() -> AudioData:
    """Digital silence, 2 s, 48 kHz."""
    samples = np.zeros(2 * 48000, dtype=np.float32)
    return AudioData(
        samples=samples,
        sample_rate=48000,
        bit_depth=16,
        duration=2.0,
        channels=1,
        file_path="<silence>",
    )
