"""
Generate official EBU R128 / ITU-R BS.1770-4 compliance test vectors.

Creates test signals defined by EBU Tech 3341 (Loudness Metering: 'EBU Mode')
and ITU-R BS.1770-4 with precisely calibrated loudness levels using
pyloudnorm's loudness normalization.

Test signals generated:
  1. ebu_r128_tone_stereo_23lufs.wav  - EBU Tech 3341 Sec 6.1: stereo 1 kHz at -23 LUFS
  2. ebu_r128_tone_stereo_33lufs.wav  - EBU Tech 3341 Sec 6.2: stereo 1 kHz at -33 LUFS
  3. ebu_r128_tone_mono_23lufs.wav    - BS.1770-4 mono reference: mono 1 kHz at -23 LUFS
  4. ebu_r128_tone_with_silence.wav   - EBU Tech 3341 Sec 7: tone + silence gating test
  5. ebu_r128_two_tones.wav           - EBU Tech 3341 Sec 8: relative gate test

All signals use 48 kHz sample rate, 16-bit PCM, matching EBU recommended
broadcast format. Signal levels are calibrated via pyloudnorm.normalize to
achieve precise LUFS targets.

Usage:
    cd backend
    python -m analysis.loudness.test_vectors.generate_ebu_vectors
"""

import os

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

SAMPLE_RATE = 48000
BIT_DEPTH = "PCM_16"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_sine_stereo(frequency: float, duration: float, rate: int = SAMPLE_RATE) -> np.ndarray:
    """Generate a full-scale stereo sine wave.

    Returns shape (num_samples, 2) with identical channels.
    """
    t = np.arange(0, int(duration * rate)) / rate
    mono = np.sin(2.0 * np.pi * frequency * t)
    return np.column_stack([mono, mono])


def generate_sine_mono(frequency: float, duration: float, rate: int = SAMPLE_RATE) -> np.ndarray:
    """Generate a full-scale mono sine wave.

    Returns shape (num_samples,).
    """
    t = np.arange(0, int(duration * rate)) / rate
    return np.sin(2.0 * np.pi * frequency * t)


def normalize_to_lufs(samples: np.ndarray, rate: int, target_lufs: float) -> np.ndarray:
    """Normalize audio to a target integrated LUFS using pyloudnorm.

    Args:
        samples: Audio samples (1-D mono or 2-D stereo).
        rate: Sample rate in Hz.
        target_lufs: Desired integrated loudness in LUFS.

    Returns:
        Normalized audio samples clipped to [-1, 1].
    """
    meter = pyln.Meter(rate)
    current_lufs = meter.integrated_loudness(samples)
    normalized = pyln.normalize.loudness(samples, current_lufs, target_lufs)
    return np.clip(normalized, -1.0, 1.0)


def main() -> None:
    print(f"Generating EBU R128 / BS.1770-4 test vectors in: {OUTPUT_DIR}")
    print()

    # ---- 1. EBU Tech 3341 Sec 6.1: Stereo 1 kHz at -23 LUFS ----
    # Standard reference signal for EBU R128 loudness metering.
    # 1 kHz chosen because K-weighting gain is ~0 dB at this frequency.
    fname = "ebu_r128_tone_stereo_23lufs.wav"
    path = os.path.join(OUTPUT_DIR, fname)
    samples = generate_sine_stereo(1000.0, 10.0)
    samples = normalize_to_lufs(samples, SAMPLE_RATE, -23.0)
    sf.write(path, samples, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: {fname} (stereo, 10s, -23 LUFS target)")

    # ---- 2. EBU Tech 3341 Sec 6.2: Stereo 1 kHz at -33 LUFS ----
    # Tests metering linearity at a lower level (10 dB below reference).
    fname = "ebu_r128_tone_stereo_33lufs.wav"
    path = os.path.join(OUTPUT_DIR, fname)
    samples = generate_sine_stereo(1000.0, 10.0)
    samples = normalize_to_lufs(samples, SAMPLE_RATE, -33.0)
    sf.write(path, samples, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: {fname} (stereo, 10s, -33 LUFS target)")

    # ---- 3. BS.1770-4 Mono Reference: Mono 1 kHz at -23 LUFS ----
    # Verifies correct mono channel handling per BS.1770-4.
    fname = "ebu_r128_tone_mono_23lufs.wav"
    path = os.path.join(OUTPUT_DIR, fname)
    samples = generate_sine_mono(1000.0, 10.0)
    samples = normalize_to_lufs(samples, SAMPLE_RATE, -23.0)
    sf.write(path, samples, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: {fname} (mono, 10s, -23 LUFS target)")

    # ---- 4. EBU Tech 3341 Sec 7: Tone + Silence (Gating Test) ----
    # Stereo 1 kHz at -23 LUFS for 10s followed by 10s digital silence.
    # BS.1770-4 absolute gating should exclude silence blocks, so
    # integrated LUFS should remain -23.0.
    fname = "ebu_r128_tone_with_silence.wav"
    path = os.path.join(OUTPUT_DIR, fname)
    tone = generate_sine_stereo(1000.0, 10.0)
    tone = normalize_to_lufs(tone, SAMPLE_RATE, -23.0)
    silence = np.zeros((10 * SAMPLE_RATE, 2))
    combined = np.vstack([tone, silence])
    sf.write(path, combined, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: {fname} (stereo, 20s = 10s tone + 10s silence)")

    # ---- 5. EBU Tech 3341 Sec 8: Two-Tone Relative Gate Test ----
    # First 10s at -36 LUFS, then 10s at -23 LUFS.
    # The relative threshold gate (-10 LU below ungated mean) should
    # exclude the quiet segment, yielding integrated LUFS near -23.
    fname = "ebu_r128_two_tones.wav"
    path = os.path.join(OUTPUT_DIR, fname)
    tone_quiet = generate_sine_stereo(1000.0, 10.0)
    tone_quiet = normalize_to_lufs(tone_quiet, SAMPLE_RATE, -36.0)
    tone_loud = generate_sine_stereo(1000.0, 10.0)
    tone_loud = normalize_to_lufs(tone_loud, SAMPLE_RATE, -23.0)
    combined = np.vstack([tone_quiet, tone_loud])
    sf.write(path, combined, SAMPLE_RATE, subtype=BIT_DEPTH)
    print(f"  Created: {fname} (stereo, 20s = 10s@-36 + 10s@-23 LUFS)")

    print()
    print("Done! All EBU R128 test vectors generated.")
    print("Run ffmpeg -i <file> -af ebur128 -f null - to verify values.")


if __name__ == "__main__":
    main()
