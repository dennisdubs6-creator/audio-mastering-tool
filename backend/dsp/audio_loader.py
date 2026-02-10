"""
Audio Loader Module

Loads and validates WAV files, extracting audio samples and metadata.
Supports 44.1/48 kHz sample rates, 16/24-bit depth, and mono/stereo files.
Stereo files are automatically converted to mono by averaging channels.
Includes edge case detection for silence, clipping, and DC offset.
"""

import logging
import os

import numpy as np
import soundfile as sf

from .audio_types import AudioData

logger = logging.getLogger(__name__)

SUPPORTED_SAMPLE_RATES = {44100, 48000}
SUPPORTED_BIT_DEPTHS = {16, 24}
SUPPORTED_SUBTYPES = {
    "PCM_16": 16,
    "PCM_24": 24,
}


def detect_silence(samples: np.ndarray) -> bool:
    """Detect if audio is essentially silent.

    Args:
        samples: Audio samples as float array.

    Returns:
        True if RMS is below -120 dBFS threshold.
    """
    rms = np.sqrt(np.mean(samples ** 2))
    return rms < 1e-6


def detect_clipping(samples: np.ndarray) -> bool:
    """Detect if audio contains clipping.

    Args:
        samples: Audio samples as float array.

    Returns:
        True if max absolute sample exceeds -0.1 dBFS (0.99).
    """
    max_sample = np.max(np.abs(samples))
    return max_sample > 0.99


def detect_dc_offset(samples: np.ndarray) -> tuple[bool, float]:
    """Detect significant DC offset in audio.

    Args:
        samples: Audio samples as float array.

    Returns:
        Tuple of (has_offset, mean_value). has_offset is True
        if abs(mean) > 0.01.
    """
    mean = float(np.mean(samples))
    return (abs(mean) > 0.01, mean)


def remove_dc_offset(samples: np.ndarray) -> np.ndarray:
    """Remove DC offset by subtracting the mean.

    Args:
        samples: Audio samples as float array.

    Returns:
        Samples with DC offset removed.
    """
    return samples - np.mean(samples)


class AudioLoader:
    """Loads and validates WAV audio files.

    Reads WAV files using the soundfile library, validates format constraints
    (sample rate, bit depth, channel count), converts stereo to mono, and
    normalizes samples to float32 in the range [-1.0, 1.0].

    Example:
        loader = AudioLoader()
        if loader.validate_file("track.wav"):
            audio = loader.load_wav("track.wav")
            print(f"Loaded {audio.duration:.1f}s of audio at {audio.sample_rate} Hz")
    """

    def load_wav(self, file_path: str) -> AudioData:
        """Load a WAV file and return an AudioData instance.

        Args:
            file_path: Path to the WAV file to load.

        Returns:
            AudioData with samples normalized to float32 [-1.0, 1.0],
            converted to mono if the source is stereo.

        Raises:
            ValueError: If the file does not exist, is not a valid WAV,
                has an unsupported sample rate, bit depth, or channel count.
        """
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext != ".wav":
            raise ValueError(
                f"Unsupported file format '{ext}'. Only .wav files are accepted."
            )

        try:
            info = sf.info(file_path)
        except sf.LibsndfileError as exc:
            raise ValueError(f"Cannot read audio file: {exc}") from exc

        # Validate sample rate
        if info.samplerate not in SUPPORTED_SAMPLE_RATES:
            raise ValueError(
                f"Unsupported sample rate {info.samplerate} Hz. "
                f"Supported rates: {sorted(SUPPORTED_SAMPLE_RATES)}"
            )

        # Validate bit depth via subtype
        if info.subtype not in SUPPORTED_SUBTYPES:
            raise ValueError(
                f"Unsupported bit depth (subtype '{info.subtype}'). "
                f"Supported: 16-bit (PCM_16), 24-bit (PCM_24)."
            )
        bit_depth = SUPPORTED_SUBTYPES[info.subtype]

        # Validate channel count
        if info.channels not in (1, 2):
            raise ValueError(
                f"Unsupported channel count {info.channels}. "
                f"Only mono (1) and stereo (2) files are accepted."
            )

        original_channels = info.channels

        # Read audio samples as float64 (soundfile default)
        try:
            samples, sample_rate = sf.read(file_path, dtype="float64")
        except sf.LibsndfileError as exc:
            raise ValueError(f"Error reading audio data: {exc}") from exc

        # Preserve untouched stereo frames before mono conversion
        stereo_samples: np.ndarray | None = None
        if samples.ndim == 2:
            stereo_samples = samples.astype(np.float32)
            # Convert stereo to mono by averaging channels
            samples = np.mean(samples, axis=1)

        # Normalize to float32 in [-1.0, 1.0]
        samples = samples.astype(np.float32)

        # Edge case detection
        if detect_silence(samples):
            logger.warning("File appears to be silent (RMS < -120 dBFS): %s", file_path)

        if detect_clipping(samples):
            logger.warning("File contains clipping (true peak > -0.1 dBFS): %s", file_path)

        has_dc_offset, dc_mean = detect_dc_offset(samples)
        if has_dc_offset:
            logger.warning(
                "DC offset detected (mean=%.6f) in %s — removing automatically",
                dc_mean,
                file_path,
            )
            samples = remove_dc_offset(samples)

        duration = len(samples) / sample_rate

        logger.info(
            "Loaded %s: %d Hz, %d-bit, %d ch, %.2f s",
            file_path,
            sample_rate,
            bit_depth,
            original_channels,
            duration,
        )

        return AudioData(
            samples=samples,
            sample_rate=sample_rate,
            bit_depth=bit_depth,
            duration=duration,
            channels=original_channels,
            file_path=file_path,
            stereo_samples=stereo_samples,
            dc_offset_detected=has_dc_offset,
            dc_offset_mean=dc_mean,
        )

    def validate_file(self, file_path: str) -> bool:
        """Check whether a file is a valid, loadable WAV.

        Performs lightweight validation without loading the entire file.

        Args:
            file_path: Path to the file to validate.

        Returns:
            True if the file is a valid WAV with supported parameters,
            False otherwise.
        """
        if not os.path.exists(file_path):
            return False

        ext = os.path.splitext(file_path)[1].lower()
        if ext != ".wav":
            return False

        try:
            info = sf.info(file_path)
        except sf.LibsndfileError:
            return False

        if info.samplerate not in SUPPORTED_SAMPLE_RATES:
            return False

        if info.subtype not in SUPPORTED_SUBTYPES:
            return False

        if info.channels not in (1, 2):
            return False

        return True
