"""
DSP Audio Data Types

Dataclasses for type-safe audio data representation used throughout
the DSP pipeline: loading, STFT computation, and band integration.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class AudioData:
    """Container for loaded audio data and metadata.

    Attributes:
        samples: Audio samples as a 1-D float32 array normalized to [-1.0, 1.0].
            Shape: (num_samples,) after mono conversion.
        sample_rate: Sample rate in Hz (44100 or 48000).
        bit_depth: Bit depth of the original file (16 or 24).
        duration: Duration in seconds (num_samples / sample_rate).
        channels: Number of channels in the original file (1 or 2).
        file_path: Absolute path to the source WAV file.
    """

    samples: np.ndarray
    sample_rate: int
    bit_depth: int
    duration: float
    channels: int
    file_path: str


@dataclass
class STFTData:
    """Container for Short-Time Fourier Transform results.

    Attributes:
        magnitude: Magnitude spectrum as a 2-D float64 array.
            Shape: (num_freq_bins, num_time_frames).
        phase: Phase spectrum as a 2-D float64 array in radians.
            Shape: (num_freq_bins, num_time_frames).
        frequencies: Frequency axis as a 1-D array in Hz.
            Shape: (num_freq_bins,) where num_freq_bins = FFT_SIZE // 2 + 1.
        times: Time axis as a 1-D array in seconds.
            Shape: (num_time_frames,).
        window_size: STFT window size in samples.
        hop_size: STFT hop size in samples.
    """

    magnitude: np.ndarray
    phase: np.ndarray
    frequencies: np.ndarray
    times: np.ndarray
    window_size: int
    hop_size: int


@dataclass
class BandData:
    """Container for per-frequency-band analysis data.

    Attributes:
        band_name: Name of the frequency band (e.g., 'low', 'mid', 'high').
        freq_min: Lower frequency boundary in Hz (inclusive).
        freq_max: Upper frequency boundary in Hz (exclusive).
        energy: Total energy in the band, computed as the sum of squared
            magnitudes across all bins and time frames.
        magnitude: Time-averaged magnitude across the band's frequency bins.
            Shape: (num_time_frames,).
    """

    band_name: str
    freq_min: float
    freq_max: float
    energy: float
    magnitude: np.ndarray
