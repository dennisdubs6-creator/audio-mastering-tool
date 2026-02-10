"""
Dynamics metrics for per-band audio analysis.

Computes dynamic range, crest factor, and RMS level from time-domain
band samples (float32, normalised to [-1, 1]).  All results are in dB
or dBFS.
"""

import numpy as np

_DB_FLOOR = -120.0
_EPSILON = 1e-10


def compute_dynamic_range_db(samples: np.ndarray) -> float:
    """Compute dynamic range as max–min of frame RMS levels in dB.

    Measures level variation across short-time frames, making it a
    compression / macro-dynamics indicator.  Distinct from crest factor,
    which measures instantaneous peak-to-RMS ratio.

    Parameters
    ----------
    samples : np.ndarray
        1-D array of time-domain audio samples, normalised to [-1, 1].

    Returns
    -------
    float
        Dynamic range in dB.  Returns 0.0 for silence or signals shorter
        than one analysis frame.
    """
    if samples.size == 0:
        return 0.0

    frame_size = 1024
    hop_size = frame_size // 2  # 50% overlap

    if samples.size < frame_size:
        return 0.0

    frames = np.lib.stride_tricks.sliding_window_view(
        samples, frame_size
    )[::hop_size]
    frame_rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=-1))
    frame_rms_db = 20.0 * np.log10(frame_rms + _EPSILON)

    dr = float(np.max(frame_rms_db) - np.min(frame_rms_db))
    return dr if np.isfinite(dr) else 0.0


def compute_crest_factor_db(samples: np.ndarray) -> float:
    """Compute crest factor (peak-to-RMS ratio) in dB.

    Crest factor quantifies the *peakiness* of the signal. A pure
    sine wave has a crest factor of ~3.01 dB; heavily compressed
    signals approach 0 dB.

    Parameters
    ----------
    samples : np.ndarray
        1-D array of time-domain audio samples, normalised to [-1, 1].

    Returns
    -------
    float
        Crest factor in dB.  Returns 0.0 for silence.
    """
    if samples.size == 0:
        return 0.0

    peak = np.max(np.abs(samples))
    rms = np.sqrt(np.mean(samples.astype(np.float64) ** 2))

    if rms < _EPSILON or peak < _EPSILON:
        return 0.0

    cf = 20.0 * np.log10(peak / rms)
    return float(cf) if np.isfinite(cf) else 0.0


def compute_rms_db(samples: np.ndarray) -> float:
    """Compute overall RMS level in dBFS from time-domain samples.

    Parameters
    ----------
    samples : np.ndarray
        1-D array of time-domain audio samples, normalised to [-1, 1].

    Returns
    -------
    float
        RMS level in dBFS.  Returns ``_DB_FLOOR`` for silence.
    """
    if samples.size == 0:
        return _DB_FLOOR

    rms = np.sqrt(np.mean(samples.astype(np.float64) ** 2))
    if rms < _EPSILON:
        return _DB_FLOOR

    return float(20.0 * np.log10(np.maximum(rms, _EPSILON)))
