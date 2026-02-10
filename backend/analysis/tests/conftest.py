"""
Shared pytest fixtures for analysis metric tests.

Provides deterministic test signals: sine wave, white noise, impulse,
stereo pair, and silence.  All signals are 3 seconds at 48 kHz unless
otherwise noted.
"""

import numpy as np
import pytest

SAMPLE_RATE = 48000
DURATION = 3.0
NUM_SAMPLES = int(SAMPLE_RATE * DURATION)


@pytest.fixture
def sine_wave_440hz() -> np.ndarray:
    """Pure 440 Hz sine wave at full scale, 3 seconds, 48 kHz."""
    t = np.linspace(0, DURATION, NUM_SAMPLES, endpoint=False)
    return np.sin(2.0 * np.pi * 440.0 * t).astype(np.float32)


@pytest.fixture
def white_noise() -> np.ndarray:
    """White noise uniformly distributed in [-1, 1], 3 seconds, 48 kHz."""
    rng = np.random.default_rng(seed=42)
    return rng.uniform(-1.0, 1.0, size=NUM_SAMPLES).astype(np.float32)


@pytest.fixture
def impulse() -> np.ndarray:
    """Single-sample impulse (Dirac delta) at full scale."""
    sig = np.zeros(NUM_SAMPLES, dtype=np.float32)
    sig[0] = 1.0
    return sig


@pytest.fixture
def stereo_test() -> tuple[np.ndarray, np.ndarray]:
    """Stereo pair: left = 440 Hz sine, right = 880 Hz sine."""
    t = np.linspace(0, DURATION, NUM_SAMPLES, endpoint=False)
    left = np.sin(2.0 * np.pi * 440.0 * t).astype(np.float32)
    right = np.sin(2.0 * np.pi * 880.0 * t).astype(np.float32)
    return left, right


@pytest.fixture
def silence() -> np.ndarray:
    """All-zero signal, 3 seconds, 48 kHz."""
    return np.zeros(NUM_SAMPLES, dtype=np.float32)


@pytest.fixture
def sample_rate() -> int:
    """Common sample rate for test signals."""
    return SAMPLE_RATE


@pytest.fixture
def clipping() -> np.ndarray:
    """Hard-clipped sine wave (2x gain, clipped to [-1, 1])."""
    t = np.linspace(0, DURATION, NUM_SAMPLES, endpoint=False)
    return np.clip(
        2.0 * np.sin(2.0 * np.pi * 440.0 * t), -1.0, 1.0
    ).astype(np.float32)


@pytest.fixture
def hard_panned_stereo() -> tuple[np.ndarray, np.ndarray]:
    """Hard-panned stereo: left = 440 Hz sine, right = inverted.

    Produces ~100 % stereo width in mid/side analysis.
    """
    t = np.linspace(0, DURATION, NUM_SAMPLES, endpoint=False)
    sig = np.sin(2.0 * np.pi * 440.0 * t).astype(np.float32)
    return sig, -sig
