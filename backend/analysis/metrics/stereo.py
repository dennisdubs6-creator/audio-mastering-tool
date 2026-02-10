"""
Stereo metrics for per-band audio analysis.

Computes stereo width, phase correlation, and mid/side energy
from separate left and right channel arrays.  All functions return
``None`` for mono audio.
"""

import logging

import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)

_DB_FLOOR = -120.0
_EPSILON = 1e-10


def load_stereo_audio(
    file_path: str,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Load a WAV file preserving stereo channels.

    Parameters
    ----------
    file_path : str
        Path to the WAV file.

    Returns
    -------
    tuple[np.ndarray, np.ndarray] | None
        ``(left, right)`` channel arrays as float32, or ``None`` if the
        file is mono or cannot be read.
    """
    try:
        info = sf.info(file_path)
        if info.channels < 2:
            return None

        data, sr = sf.read(file_path, dtype="float32")
        if data.ndim != 2 or data.shape[1] < 2:
            return None

        return data[:, 0], data[:, 1]
    except Exception:
        logger.warning("Failed to load stereo audio from %s", file_path)
        return None


def compute_stereo_width_percent(
    left: np.ndarray,
    right: np.ndarray,
) -> float | None:
    """Compute stereo width as a percentage (0-100 %).

    Uses mid/side analysis:
        mid  = (L + R) / 2
        side = (L - R) / 2
        width = 100 * side_energy / (mid_energy + side_energy)

    A mono signal yields 0 %; fully out-of-phase L/R yields 100 %.

    Parameters
    ----------
    left : np.ndarray
        Left channel samples.
    right : np.ndarray
        Right channel samples.

    Returns
    -------
    float | None
        Stereo width percentage, or ``None`` if inputs are invalid.
    """
    if left is None or right is None:
        return None
    if left.size == 0 or right.size == 0:
        return None

    mid = (left + right) / 2.0
    side = (left - right) / 2.0

    mid_energy = np.sum(mid ** 2)
    side_energy = np.sum(side ** 2)
    total = mid_energy + side_energy

    if total < _EPSILON:
        return 0.0

    return float(100.0 * side_energy / total)


def compute_phase_correlation(
    left: np.ndarray,
    right: np.ndarray,
) -> float | None:
    """Compute Pearson correlation between left and right channels.

    Parameters
    ----------
    left : np.ndarray
        Left channel samples.
    right : np.ndarray
        Right channel samples.

    Returns
    -------
    float | None
        Correlation coefficient in [-1, 1].  +1 = perfect correlation
        (mono-compatible), -1 = perfectly out of phase, 0 = uncorrelated.
        Returns ``None`` for invalid inputs or silence.
    """
    if left is None or right is None:
        return None
    if left.size == 0 or right.size == 0:
        return None

    left_std = np.std(left)
    right_std = np.std(right)

    if left_std < _EPSILON or right_std < _EPSILON:
        return None

    corr = np.corrcoef(left, right)[0, 1]
    return float(corr) if np.isfinite(corr) else None


def compute_mid_energy_db(
    left: np.ndarray,
    right: np.ndarray,
) -> float | None:
    """Compute mid-channel energy in dB.

    mid = (left + right) / 2
    energy_db = 10 * log10(sum(mid ** 2))

    Parameters
    ----------
    left : np.ndarray
        Left channel samples.
    right : np.ndarray
        Right channel samples.

    Returns
    -------
    float | None
        Mid energy in dB, or ``None`` for invalid inputs.
    """
    if left is None or right is None:
        return None
    if left.size == 0 or right.size == 0:
        return None

    mid = (left + right) / 2.0
    energy = np.sum(mid ** 2)

    if energy < _EPSILON:
        return _DB_FLOOR

    val = 10.0 * np.log10(np.maximum(energy, _EPSILON))
    return float(val) if np.isfinite(val) else _DB_FLOOR


def compute_side_energy_db(
    left: np.ndarray,
    right: np.ndarray,
) -> float | None:
    """Compute side-channel energy in dB.

    side = (left - right) / 2
    energy_db = 10 * log10(sum(side ** 2))

    Parameters
    ----------
    left : np.ndarray
        Left channel samples.
    right : np.ndarray
        Right channel samples.

    Returns
    -------
    float | None
        Side energy in dB, or ``None`` for invalid inputs.
    """
    if left is None or right is None:
        return None
    if left.size == 0 or right.size == 0:
        return None

    side = (left - right) / 2.0
    energy = np.sum(side ** 2)

    if energy < _EPSILON:
        return _DB_FLOOR

    val = 10.0 * np.log10(np.maximum(energy, _EPSILON))
    return float(val) if np.isfinite(val) else _DB_FLOOR
