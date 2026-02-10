"""
Spectral metrics for per-band audio analysis.

Computes spectral centroid, rolloff, flatness, and energy using
librosa for spectral feature extraction and NumPy for energy
calculations.
"""

import numpy as np

_DB_FLOOR = -120.0
_EPSILON = 1e-10


def compute_spectral_centroid_hz(
    band_samples: np.ndarray,
    sample_rate: int,
) -> float:
    """Compute the mean spectral centroid in Hz.

    The spectral centroid is the *centre of mass* of the spectrum,
    indicating where most of the signal energy is concentrated.

    Parameters
    ----------
    band_samples : np.ndarray
        1-D time-domain audio samples for the band.
    sample_rate : int
        Sample rate in Hz.

    Returns
    -------
    float
        Mean spectral centroid in Hz.  Returns 0.0 for silence.
    """
    import librosa

    if band_samples.size == 0 or np.max(np.abs(band_samples)) < _EPSILON:
        return 0.0

    centroid = librosa.feature.spectral_centroid(
        y=band_samples.astype(np.float32), sr=sample_rate
    )
    mean_val = float(np.mean(centroid))
    return mean_val if np.isfinite(mean_val) else 0.0


def compute_spectral_rolloff_hz(
    band_samples: np.ndarray,
    sample_rate: int,
    roll_percent: float = 0.85,
) -> float:
    """Compute the mean spectral roll-off frequency in Hz.

    The roll-off frequency is the value below which *roll_percent*
    (default 85 %) of the total spectral energy is contained.

    Parameters
    ----------
    band_samples : np.ndarray
        1-D time-domain audio samples for the band.
    sample_rate : int
        Sample rate in Hz.
    roll_percent : float
        Energy proportion threshold (default 0.85).

    Returns
    -------
    float
        Mean spectral roll-off in Hz.  Returns 0.0 for silence.
    """
    import librosa

    if band_samples.size == 0 or np.max(np.abs(band_samples)) < _EPSILON:
        return 0.0

    rolloff = librosa.feature.spectral_rolloff(
        y=band_samples.astype(np.float32),
        sr=sample_rate,
        roll_percent=roll_percent,
    )
    mean_val = float(np.mean(rolloff))
    return mean_val if np.isfinite(mean_val) else 0.0


def compute_spectral_flatness(band_samples: np.ndarray) -> float:
    """Compute the mean spectral flatness (Wiener entropy).

    Values near 0 indicate tonal (harmonic) content; values near 1
    indicate noise-like content.

    Parameters
    ----------
    band_samples : np.ndarray
        1-D time-domain audio samples for the band.

    Returns
    -------
    float
        Mean spectral flatness in [0, 1].  Returns 0.0 for silence.
    """
    import librosa

    if band_samples.size == 0 or np.max(np.abs(band_samples)) < _EPSILON:
        return 0.0

    flatness = librosa.feature.spectral_flatness(
        y=band_samples.astype(np.float32)
    )
    mean_val = float(np.mean(flatness))
    return mean_val if np.isfinite(mean_val) else 0.0


def compute_energy_db(magnitude: np.ndarray) -> float:
    """Compute total band energy in dB.

    Energy is the sum of squared magnitudes across all bins and
    frames, expressed in dB: ``10 * log10(sum(magnitude**2))``.

    Parameters
    ----------
    magnitude : np.ndarray
        1-D array of per-frame magnitude values.

    Returns
    -------
    float
        Total energy in dB.  Returns ``_DB_FLOOR`` for silence.
    """
    if magnitude.size == 0:
        return _DB_FLOOR

    total_energy = np.sum(magnitude ** 2)
    if total_energy < _EPSILON:
        return _DB_FLOOR

    energy_db = 10.0 * np.log10(np.maximum(total_energy, _EPSILON))
    return float(energy_db) if np.isfinite(energy_db) else _DB_FLOOR


def compute_energy_db_from_energy(energy: float, num_frames: int) -> float:
    """Convert a pre-computed total band energy to dB as mean-square power.

    Normalizes the total energy by *num_frames* before applying
    ``10 * log10`` so the result reflects average power and does not
    scale with track length.

    Parameters
    ----------
    energy : float
        Total energy as sum of squared magnitudes.
    num_frames : int
        Number of STFT time frames used to compute the energy.
        Used as the divisor for mean-square normalization.

    Returns
    -------
    float
        Mean-square energy in dB.  Returns ``_DB_FLOOR`` for silence /
        near-zero energy.
    """
    if energy < _EPSILON:
        return _DB_FLOOR

    mean_power = energy / max(num_frames, 1)
    energy_db = 10.0 * np.log10(max(mean_power, _EPSILON))
    return float(energy_db) if np.isfinite(energy_db) else _DB_FLOOR
