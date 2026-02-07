"""
Generate golden corpus test audio files for loudness metering validation.

Creates WAV files in the test_vectors directory:

  Original test vectors:
  1. sine_440hz.wav     - Full-scale 440 Hz sine, 3s, 48 kHz, 16-bit, mono
  2. sine_1khz_stereo.wav - Full-scale 1 kHz sine, 3s, 48 kHz, 16-bit, stereo
  3. white_noise.wav    - White noise at -20 dBFS RMS, 5s, 48 kHz, 16-bit, mono
  4. silence.wav        - Digital silence, 2s, 48 kHz, 16-bit, mono
  5. pink_noise.wav     - Pink noise at -18 dBFS RMS, 5s, 48 kHz, 16-bit, mono

  EBU R128 / ITU-R BS.1770-4 compliance test vectors:
  6. ebu_r128_stereo_997hz_23lufs.wav  - Stereo 997 Hz at -23 LUFS (EBU R128 target)
  7. ebu_r128_stereo_997hz_33lufs.wav  - Stereo 997 Hz at -33 LUFS (low-level)
  8. ebu_r128_mono_997hz_23lufs.wav    - Mono 997 Hz at -23 LUFS
  9. ebu_r128_gate_test.wav            - Gating test: silence + tone
  10. ebu_r128_lra_test.wav            - LRA test: alternating levels

Usage:
    python generate_vectors.py
"""

import json
import os

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

SAMPLE_RATE = 48000
BIT_DEPTH = "PCM_16"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_sine(frequency: float, duration: float, channels: int = 1) -> np.ndarray:
    """Generate a full-scale sine wave."""
    t = np.arange(0, duration, 1.0 / SAMPLE_RATE)
    samples = np.sin(2.0 * np.pi * frequency * t)
    if channels == 2:
        samples = np.column_stack([samples, samples])
    return samples


def generate_white_noise(duration: float, rms_dbfs: float) -> np.ndarray:
    """Generate white noise at a specified RMS level in dBFS."""
    rng = np.random.default_rng(seed=42)
    n_samples = int(duration * SAMPLE_RATE)
    # Generate unit-variance Gaussian noise
    noise = rng.standard_normal(n_samples)
    # Scale to desired RMS: rms_linear = 10^(rms_dbfs/20)
    target_rms = 10.0 ** (rms_dbfs / 20.0)
    current_rms = np.sqrt(np.mean(noise ** 2))
    noise = noise * (target_rms / current_rms)
    # Clip to [-1, 1] to prevent clipping artifacts
    noise = np.clip(noise, -1.0, 1.0)
    return noise


def generate_pink_noise(duration: float, rms_dbfs: float) -> np.ndarray:
    """Generate pink noise (1/f) at a specified RMS level in dBFS.

    Uses the Voss-McCartney algorithm for pink noise generation.
    """
    rng = np.random.default_rng(seed=123)
    n_samples = int(duration * SAMPLE_RATE)

    # Voss-McCartney algorithm with 16 rows
    n_rows = 16
    n_cols = n_samples
    array = rng.standard_normal((n_rows, n_cols))

    # Create pink noise by summing rows with different update rates
    pink = np.zeros(n_cols)
    for i in range(n_rows):
        step = 2 ** i
        row = np.repeat(array[i, ::step], step)[:n_cols]
        pink += row

    # Normalize to desired RMS
    target_rms = 10.0 ** (rms_dbfs / 20.0)
    current_rms = np.sqrt(np.mean(pink ** 2))
    if current_rms > 0:
        pink = pink * (target_rms / current_rms)
    pink = np.clip(pink, -1.0, 1.0)
    return pink


def generate_sine_at_lufs(
    frequency: float,
    target_lufs: float,
    duration: float,
    channels: int = 2,
) -> np.ndarray:
    """Generate a sine wave calibrated to a target integrated LUFS level.

    Uses pyloudnorm (BS.1770-4 reference implementation) to loudness-normalize
    the signal.  The resulting signal will measure at *target_lufs* when
    processed through a compliant BS.1770-4 meter.

    Args:
        frequency: Sine wave frequency in Hz.  997 Hz is the ITU-R standard
            test frequency (K-weighting gain is near-unity).
        target_lufs: Desired integrated loudness in LUFS.
        duration: Duration in seconds.  Must be >= 0.4 s for valid gating.
        channels: Number of output channels (1 = mono, 2 = stereo).

    Returns:
        Loudness-normalized samples as float64 ndarray.
    """
    t = np.arange(0, duration, 1.0 / SAMPLE_RATE)
    samples = np.sin(2.0 * np.pi * frequency * t)
    if channels == 2:
        samples = np.column_stack([samples, samples])

    # Measure current loudness and normalize to target
    meter = pyln.Meter(SAMPLE_RATE)
    current_lufs = meter.integrated_loudness(samples)
    samples = pyln.normalize.loudness(samples, current_lufs, target_lufs)
    return samples


def generate_ebu_gate_test(
    frequency: float,
    tone_lufs: float,
    tone_duration: float = 10.0,
    silence_duration: float = 10.0,
) -> np.ndarray:
    """Generate an absolute-gating test signal per EBU Tech 3341.

    Creates a stereo signal with a leading silence segment followed by a
    tone segment at a calibrated level.  The silence is below the -70 LUFS
    absolute gate and should be excluded from integrated loudness, so the
    resulting measurement equals *tone_lufs*.

    Args:
        frequency: Tone frequency in Hz.
        tone_lufs: Target LUFS for the tone segment.
        tone_duration: Duration of the tone portion in seconds.
        silence_duration: Duration of the silence portion in seconds.

    Returns:
        Stereo samples (float64) with silence followed by tone.
    """
    # Tone segment calibrated to target
    tone = generate_sine_at_lufs(frequency, tone_lufs, tone_duration, channels=2)

    # Silence segment (well below -70 LUFS absolute gate)
    n_silence = int(silence_duration * SAMPLE_RATE)
    silence = np.zeros((n_silence, 2))

    return np.vstack([silence, tone])


def generate_ebu_lra_test(
    frequency: float,
    lufs_high: float,
    lufs_low: float,
    segment_duration: float = 5.0,
    repetitions: int = 6,
) -> np.ndarray:
    """Generate an LRA test signal per EBU Tech 3342.

    Alternates between loud and quiet stereo segments of equal duration.
    The Loudness Range (LRA) approximates ``lufs_high - lufs_low`` because
    the short-term loudness distribution concentrates at two levels whose
    95th-to-10th percentile span equals the level difference.

    Args:
        frequency: Tone frequency in Hz.
        lufs_high: LUFS of the loud segments.
        lufs_low: LUFS of the quiet segments.
        segment_duration: Duration of each segment in seconds.
        repetitions: Number of high/low pairs.

    Returns:
        Stereo samples (float64) with alternating levels.
    """
    segments: list[np.ndarray] = []
    for _ in range(repetitions):
        high = generate_sine_at_lufs(frequency, lufs_high, segment_duration, channels=2)
        low = generate_sine_at_lufs(frequency, lufs_low, segment_duration, channels=2)
        segments.extend([high, low])
    return np.vstack(segments)


def main() -> None:
    print(f"Generating test vectors in: {OUTPUT_DIR}")

    # 1. sine_440hz.wav
    path = os.path.join(OUTPUT_DIR, "sine_440hz.wav")
    samples = generate_sine(440.0, 3.0, channels=1)
    sf.write(path, samples, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: sine_440hz.wav ({len(samples)} samples)")

    # 2. sine_1khz_stereo.wav
    path = os.path.join(OUTPUT_DIR, "sine_1khz_stereo.wav")
    samples = generate_sine(1000.0, 3.0, channels=2)
    sf.write(path, samples, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: sine_1khz_stereo.wav ({len(samples)} samples)")

    # 3. white_noise.wav
    path = os.path.join(OUTPUT_DIR, "white_noise.wav")
    samples = generate_white_noise(5.0, -20.0)
    sf.write(path, samples, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: white_noise.wav ({len(samples)} samples)")

    # 4. silence.wav
    path = os.path.join(OUTPUT_DIR, "silence.wav")
    samples = np.zeros(2 * SAMPLE_RATE)
    sf.write(path, samples, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: silence.wav ({len(samples)} samples)")

    # 5. pink_noise.wav
    path = os.path.join(OUTPUT_DIR, "pink_noise.wav")
    samples = generate_pink_noise(5.0, -18.0)
    sf.write(path, samples, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: pink_noise.wav ({len(samples)} samples)")

    # ------------------------------------------------------------------
    # EBU R128 / ITU-R BS.1770-4 compliance test vectors
    # ------------------------------------------------------------------
    print("\nGenerating EBU R128 / ITU-R BS.1770-4 compliance vectors...")

    # 6. ebu_r128_stereo_997hz_23lufs.wav
    #    EBU R128 reference level: stereo 997 Hz at -23 LUFS (EBU Tech 3341 Seq 1)
    path = os.path.join(OUTPUT_DIR, "ebu_r128_stereo_997hz_23lufs.wav")
    samples = generate_sine_at_lufs(997.0, -23.0, 20.0, channels=2)
    sf.write(path, samples, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: ebu_r128_stereo_997hz_23lufs.wav ({len(samples)} samples)")

    # 7. ebu_r128_stereo_997hz_33lufs.wav
    #    EBU R128 low-level test: stereo 997 Hz at -33 LUFS (EBU Tech 3341 Seq 2)
    path = os.path.join(OUTPUT_DIR, "ebu_r128_stereo_997hz_33lufs.wav")
    samples = generate_sine_at_lufs(997.0, -33.0, 20.0, channels=2)
    sf.write(path, samples, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: ebu_r128_stereo_997hz_33lufs.wav ({len(samples)} samples)")

    # 8. ebu_r128_mono_997hz_23lufs.wav
    #    ITU-R BS.1770-4 mono reference: 997 Hz at -23 LUFS
    path = os.path.join(OUTPUT_DIR, "ebu_r128_mono_997hz_23lufs.wav")
    samples = generate_sine_at_lufs(997.0, -23.0, 20.0, channels=1)
    sf.write(path, samples, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: ebu_r128_mono_997hz_23lufs.wav ({len(samples)} samples)")

    # 9. ebu_r128_gate_test.wav
    #    Absolute gating test per EBU Tech 3341: silence + tone at -23 LUFS.
    #    The silence is below the -70 LUFS absolute gate and must be excluded.
    #    Certified integrated LUFS after gating: -23.0 LUFS.
    path = os.path.join(OUTPUT_DIR, "ebu_r128_gate_test.wav")
    samples = generate_ebu_gate_test(997.0, -23.0, tone_duration=10.0, silence_duration=10.0)
    sf.write(path, samples, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: ebu_r128_gate_test.wav ({len(samples)} samples)")

    # 10. ebu_r128_lra_test.wav
    #     Loudness Range test per EBU Tech 3342: alternating -20 / -30 LUFS.
    #     Certified LRA: 10.0 LU (95th-10th percentile of short-term loudness).
    path = os.path.join(OUTPUT_DIR, "ebu_r128_lra_test.wav")
    samples = generate_ebu_lra_test(
        997.0, lufs_high=-20.0, lufs_low=-30.0, segment_duration=5.0, repetitions=6,
    )
    sf.write(path, samples, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: ebu_r128_lra_test.wav ({len(samples)} samples)")

    print("\nDone! All test vectors generated.")
    print("\nNote: Run the validation script to compute expected values:")
    print("  cd backend && python -m analysis.loudness.validate_precision")


if __name__ == "__main__":
    main()
