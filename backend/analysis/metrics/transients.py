"""
Transient metrics for per-band audio analysis.

Computes transient preservation and attack time using librosa's
onset detection and percussive source separation.
"""

import numpy as np

_EPSILON = 1e-10

# RMS energy threshold (linear) below which transient metrics are skipped
_ENERGY_FLOOR = 1e-6

# Chunk size for iterative onset detection (samples).
# ~1 second at 48 kHz; keeps per-chunk cost bounded while covering the
# full signal.
_ONSET_CHUNK_SIZE = 48000


def compute_transient_preservation(
    band_samples: np.ndarray,
    sample_rate: int,
    *,
    percussive: np.ndarray | None = None,
) -> float:
    """Compute the ratio of percussive (transient) energy to total energy.

    When *percussive* is supplied the expensive HPSS step is skipped.

    Parameters
    ----------
    band_samples : np.ndarray
        1-D time-domain audio samples for the band.
    sample_rate : int
        Sample rate in Hz.
    percussive : np.ndarray | None
        Pre-computed percussive component from ``harmonics.compute_hpss``.

    Returns
    -------
    float
        Transient preservation ratio in [0, 1].  Returns 0.0 for
        silence or when no transients are detected.
    """
    if band_samples.size == 0 or np.max(np.abs(band_samples)) < _EPSILON:
        return 0.0

    # Short-circuit when band energy is below threshold
    rms = np.sqrt(np.mean(band_samples ** 2))
    if rms < _ENERGY_FLOOR:
        return 0.0

    samples = band_samples.astype(np.float32)

    if percussive is None:
        import librosa
        try:
            percussive = librosa.effects.percussive(y=samples)
        except Exception:
            return 0.0

    total_energy = np.sum(samples ** 2)
    perc_energy = np.sum(percussive ** 2)

    if total_energy < _EPSILON:
        return 0.0

    ratio = perc_energy / total_energy
    return float(min(ratio, 1.0)) if np.isfinite(ratio) else 0.0


def compute_attack_time_ms(
    band_samples: np.ndarray,
    sample_rate: int,
) -> float:
    """Compute mean attack time in milliseconds.

    Detects onsets using ``librosa.onset.onset_detect``, then for each
    onset measures the time from onset to the next local amplitude peak
    using an RMS envelope.  Returns the mean attack time across all
    detected onsets.

    The full signal is processed iteratively in chunks of
    ``_ONSET_CHUNK_SIZE`` samples to keep per-chunk cost bounded while
    ensuring long tracks are fully represented.

    Parameters
    ----------
    band_samples : np.ndarray
        1-D time-domain audio samples for the band.
    sample_rate : int
        Sample rate in Hz.

    Returns
    -------
    float
        Mean attack time in milliseconds.  Returns 0.0 when no
        onsets are detected.
    """
    import librosa

    if band_samples.size == 0 or np.max(np.abs(band_samples)) < _EPSILON:
        return 0.0

    # Short-circuit when band energy is below threshold
    rms_val = np.sqrt(np.mean(band_samples ** 2))
    if rms_val < _ENERGY_FLOOR:
        return 0.0

    samples = band_samples.astype(np.float32)
    hop_length = 512
    attack_times: list[float] = []

    # Process the full signal in chunks
    for start in range(0, len(samples), _ONSET_CHUNK_SIZE):
        chunk = samples[start : start + _ONSET_CHUNK_SIZE]

        # Need enough samples for at least a couple of RMS frames
        if chunk.size < hop_length * 2:
            continue

        try:
            onset_frames = librosa.onset.onset_detect(
                y=chunk, sr=sample_rate, units="frames"
            )
        except Exception:
            continue

        if onset_frames.size == 0:
            continue

        rms = librosa.feature.rms(y=chunk, hop_length=hop_length)[0]
        num_rms_frames = rms.size

        # Search window: from onset to onset + 50 ms worth of frames
        search_frames = max(1, int(0.05 * sample_rate / hop_length))

        for onset_frame in onset_frames:
            if onset_frame >= num_rms_frames:
                continue

            end_frame = min(onset_frame + search_frames, num_rms_frames)

            if end_frame <= onset_frame:
                continue

            segment = rms[onset_frame:end_frame]
            peak_offset = int(np.argmax(segment))

            # Convert frame offset to milliseconds
            attack_samples = peak_offset * hop_length
            attack_ms = 1000.0 * attack_samples / sample_rate
            attack_times.append(attack_ms)

    if not attack_times:
        return 0.0

    mean_attack = float(np.mean(attack_times))
    return mean_attack if np.isfinite(mean_attack) else 0.0
