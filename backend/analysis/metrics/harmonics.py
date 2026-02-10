"""
Harmonics metrics for per-band audio analysis.

Computes Total Harmonic Distortion, harmonic ratio, and
inharmonicity using librosa's harmonic-percussive separation
and pitch tracking.
"""

import numpy as np

_EPSILON = 1e-10

# RMS energy threshold (linear) below which harmonic metrics are skipped
_ENERGY_FLOOR = 1e-6

# Window size for windowed inharmonicity analysis (samples).
# ~1 second at 48 kHz.
_INHARMONICITY_WINDOW_SIZE = 48000

# Maximum number of evenly-spaced windows to analyze for inharmonicity.
# Keeps total pyin calls bounded so runtime stays <30 s on 3-5 min tracks.
_MAX_INHARMONICITY_WINDOWS = 6


def compute_hpss(
    band_samples: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Run harmonic-percussive source separation once.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        ``(harmonic, percussive)`` components.  Returns a pair of
        zero-length arrays when the input is empty or silent.
    """
    import librosa

    if band_samples.size == 0 or np.max(np.abs(band_samples)) < _EPSILON:
        empty = np.array([], dtype=np.float32)
        return empty, empty

    samples = band_samples.astype(np.float32)
    harmonic, percussive = librosa.effects.hpss(y=samples)
    return harmonic.astype(np.float32), percussive.astype(np.float32)


def compute_thd_percent(
    band_samples: np.ndarray,
    sample_rate: int,
    fundamental_freq: float | None = None,
    *,
    harmonic: np.ndarray | None = None,
) -> float:
    """Compute Total Harmonic Distortion as a percentage.

    When *harmonic* is supplied the expensive HPSS step is skipped.

    Parameters
    ----------
    band_samples : np.ndarray
        1-D time-domain audio samples for the band.
    sample_rate : int
        Sample rate in Hz.
    fundamental_freq : float | None
        Known fundamental frequency.  If ``None`` the function
        still computes THD via harmonic-percussive separation.
    harmonic : np.ndarray | None
        Pre-computed harmonic component from ``compute_hpss``.

    Returns
    -------
    float
        THD as a percentage (0-100).  Returns 0.0 for silence.
    """
    if band_samples.size == 0 or np.max(np.abs(band_samples)) < _EPSILON:
        return 0.0

    # Short-circuit when band energy is below threshold
    rms = np.sqrt(np.mean(band_samples ** 2))
    if rms < _ENERGY_FLOOR:
        return 0.0

    samples = band_samples.astype(np.float32)

    if harmonic is None:
        import librosa
        harmonic = librosa.effects.harmonic(y=samples)

    residual = samples[: len(harmonic)] - harmonic[: len(samples)]

    total_rms = np.sqrt(np.mean(samples ** 2))
    residual_rms = np.sqrt(np.mean(residual ** 2))

    if total_rms < _EPSILON:
        return 0.0

    thd = 100.0 * residual_rms / total_rms
    return float(thd) if np.isfinite(thd) else 0.0


def compute_harmonic_ratio(
    band_samples: np.ndarray,
    *,
    harmonic: np.ndarray | None = None,
    percussive: np.ndarray | None = None,
) -> float:
    """Compute the ratio of harmonic to total energy.

    When *harmonic* and *percussive* are supplied the expensive HPSS
    step is skipped.

    Parameters
    ----------
    band_samples : np.ndarray
        1-D time-domain audio samples for the band.
    harmonic : np.ndarray | None
        Pre-computed harmonic component from ``compute_hpss``.
    percussive : np.ndarray | None
        Pre-computed percussive component from ``compute_hpss``.

    Returns
    -------
    float
        Harmonic ratio in [0, 1].  Returns 0.0 for silence.
    """
    if band_samples.size == 0 or np.max(np.abs(band_samples)) < _EPSILON:
        return 0.0

    # Short-circuit when band energy is below threshold
    rms = np.sqrt(np.mean(band_samples ** 2))
    if rms < _ENERGY_FLOOR:
        return 0.0

    samples = band_samples.astype(np.float32)

    if harmonic is None or percussive is None:
        import librosa
        harmonic_comp, percussive_comp = librosa.effects.hpss(y=samples)
        harmonic = harmonic_comp if harmonic is None else harmonic
        percussive = percussive_comp if percussive is None else percussive

    harmonic_energy = np.sum(harmonic ** 2)
    percussive_energy = np.sum(percussive ** 2)
    total = harmonic_energy + percussive_energy

    if total < _EPSILON:
        return 0.0

    ratio = harmonic_energy / total
    return float(ratio) if np.isfinite(ratio) else 0.0


def compute_inharmonicity(
    band_samples: np.ndarray,
    sample_rate: int,
) -> float:
    """Measure deviation of detected partials from ideal harmonic series.

    Samples up to ``_MAX_INHARMONICITY_WINDOWS`` evenly-spaced windows of
    ``_INHARMONICITY_WINDOW_SIZE`` samples across the track and averages the
    per-window scores.  This keeps the total number of expensive ``pyin``
    calls bounded so runtime stays well under 30 s on 3-5 minute tracks.

    Parameters
    ----------
    band_samples : np.ndarray
        1-D time-domain audio samples for the band.
    sample_rate : int
        Sample rate in Hz.

    Returns
    -------
    float
        Inharmonicity score in [0, 1] where 0 = perfectly harmonic.
        Returns 0.0 when no clear pitch is detected.
    """
    if band_samples.size == 0 or np.max(np.abs(band_samples)) < _EPSILON:
        return 0.0

    # Short-circuit when band energy is below threshold
    rms = np.sqrt(np.mean(band_samples ** 2))
    if rms < _ENERGY_FLOOR:
        return 0.0

    samples = band_samples.astype(np.float32)
    total_samples = len(samples)
    win = _INHARMONICITY_WINDOW_SIZE

    # Determine how many full windows fit, then cap at the limit.
    n_possible = max(1, total_samples // win)
    n_windows = min(n_possible, _MAX_INHARMONICITY_WINDOWS)

    # Pick evenly-spaced start offsets so the sampled windows cover
    # the full duration of the track.
    if n_possible <= n_windows:
        # Track is short enough to analyze every window.
        starts = [i * win for i in range(n_possible)]
    else:
        step = (total_samples - win) / max(n_windows - 1, 1)
        starts = [int(round(i * step)) for i in range(n_windows)]

    window_scores: list[float] = []

    for start in starts:
        chunk = samples[start : start + win]

        # Need enough samples for a meaningful FFT and pyin analysis
        if chunk.size < 2048:
            continue

        score = _inharmonicity_for_window(chunk, sample_rate)
        if score is not None:
            window_scores.append(score)

    if not window_scores:
        return 0.0

    mean_score = float(np.mean(window_scores))
    return min(mean_score, 1.0) if np.isfinite(mean_score) else 0.0


def _inharmonicity_for_window(
    samples: np.ndarray,
    sample_rate: int,
) -> float | None:
    """Compute inharmonicity for a single window of audio.

    Uses ``librosa.pyin`` to track the fundamental frequency and then
    estimates how far detected spectral peaks deviate from integer
    multiples of the fundamental.

    Returns ``None`` when no clear pitch is detected in the window.
    """
    import librosa

    try:
        f0, voiced_flag, _ = librosa.pyin(
            y=samples,
            sr=sample_rate,
            fmin=20.0,
            fmax=min(sample_rate / 2.0, 8000.0),
        )
    except Exception:
        return None

    # Keep only voiced frames
    voiced_f0 = f0[voiced_flag] if voiced_flag is not None else f0[np.isfinite(f0)]
    if voiced_f0.size == 0:
        return None

    fundamental = float(np.median(voiced_f0[np.isfinite(voiced_f0)]))
    if fundamental < _EPSILON or not np.isfinite(fundamental):
        return None

    # Compute FFT and find spectral peaks
    n_fft = min(4096, samples.size)
    spectrum = np.abs(np.fft.rfft(samples, n=n_fft))
    freqs = np.fft.rfftfreq(n_fft, d=1.0 / sample_rate)

    # Find prominent peaks (above 10% of max)
    threshold = np.max(spectrum) * 0.1
    peak_indices = np.where(spectrum > threshold)[0]

    if peak_indices.size == 0:
        return None

    peak_freqs = freqs[peak_indices]
    deviations = []
    for pf in peak_freqs:
        if pf < fundamental * 0.5:
            continue
        nearest_harmonic = round(pf / fundamental) * fundamental
        if nearest_harmonic < _EPSILON:
            continue
        dev = abs(pf - nearest_harmonic) / nearest_harmonic
        deviations.append(dev)

    if not deviations:
        return None

    score = float(np.mean(deviations))
    return min(score, 1.0) if np.isfinite(score) else None
