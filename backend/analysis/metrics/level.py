"""
Level metrics for per-band audio analysis.

Computes RMS level, true peak, and level range from time-domain band
samples (float32, normalised to [-1, 1]).  All dB values are in dBFS
(decibels relative to full scale).
"""

import numpy as np

_DB_FLOOR = -120.0
_EPSILON = 1e-10


def compute_band_rms_dbfs(samples: np.ndarray) -> float:
    """Compute RMS level in dBFS from time-domain band samples.

    Parameters
    ----------
    samples : np.ndarray
        1-D array of time-domain audio samples for the band,
        normalised to [-1.0, 1.0].

    Returns
    -------
    float
        RMS level in dBFS.  Returns ``_DB_FLOOR`` (-120 dBFS) when
        the signal is silent.
    """
    if samples.size == 0:
        return _DB_FLOOR

    rms = np.sqrt(np.mean(samples.astype(np.float64) ** 2))
    if rms < _EPSILON:
        return _DB_FLOOR

    return float(20.0 * np.log10(np.maximum(rms, _EPSILON)))


def compute_band_true_peak_dbfs(band_samples: np.ndarray) -> float:
    """Compute true peak in dBFS from time-domain band samples.

    True peak is the maximum absolute sample value converted to dBFS.

    Parameters
    ----------
    band_samples : np.ndarray
        1-D array of time-domain audio samples for the band,
        normalised to [-1.0, 1.0].

    Returns
    -------
    float
        True peak level in dBFS.  Returns ``_DB_FLOOR`` for silence.
    """
    if band_samples.size == 0:
        return _DB_FLOOR

    peak = np.max(np.abs(band_samples))
    if peak < _EPSILON:
        return _DB_FLOOR

    return float(20.0 * np.log10(np.maximum(peak, _EPSILON)))


def compute_band_level_range_db(
    samples: np.ndarray,
    sample_rate: int = 48000,
    frame_duration_ms: float = 50.0,
    percentile_low: float = 10,
    percentile_high: float = 90,
) -> float:
    """Compute level range as the inter-percentile dB difference.

    Splits the time-domain signal into short frames, computes per-frame
    RMS in dBFS, then returns the difference between the
    *percentile_high*-th and *percentile_low*-th percentiles.

    Parameters
    ----------
    samples : np.ndarray
        1-D array of time-domain audio samples, normalised to [-1, 1].
    sample_rate : int
        Sample rate in Hz (used for frame sizing).
    frame_duration_ms : float
        Duration of each analysis frame in milliseconds (default 50 ms).
    percentile_low : float
        Lower percentile (default 10).
    percentile_high : float
        Upper percentile (default 90).

    Returns
    -------
    float
        Level range in dB.  Returns 0.0 when the signal is silent or
        when the range is indeterminate.
    """
    if samples.size == 0:
        return 0.0

    frame_size = max(1, int(sample_rate * frame_duration_ms / 1000.0))
    num_frames = samples.size // frame_size

    if num_frames < 2:
        return 0.0

    # Truncate to whole frames and reshape
    truncated = samples[: num_frames * frame_size].astype(np.float64)
    frames = truncated.reshape(num_frames, frame_size)

    # Per-frame RMS
    frame_rms = np.sqrt(np.mean(frames ** 2, axis=1))

    # Convert to dB, clamping silent frames at the floor
    frame_db = np.where(
        frame_rms < _EPSILON,
        _DB_FLOOR,
        20.0 * np.log10(np.maximum(frame_rms, _EPSILON)),
    )

    low = float(np.percentile(frame_db, percentile_low))
    high = float(np.percentile(frame_db, percentile_high))

    range_db = high - low
    if not np.isfinite(range_db) or range_db < 0.0:
        return 0.0

    return range_db
