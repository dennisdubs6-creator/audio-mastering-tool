# Loudness Metering Module

Standards-compliant overall loudness metering for the Audio Mastering Tool.

## Standards Compliance

- **ITU-R BS.1770-4** – Integrated loudness measurement (LUFS) with K-weighting
- **EBU R128** – Loudness Range (LRA) and True Peak measurement

## Library Choices

| Library | Purpose | Standard |
|---------|---------|----------|
| **pyloudnorm** | Primary LUFS computation | ITU-R BS.1770-4 (pure Python) |
| **pyebur128** | LRA, True Peak, LUFS cross-validation | EBU R128 via libebur128 (C bindings) |

### Why Two Libraries?

Using both pyloudnorm and pyebur128 provides:

1. **Cross-validation** – LUFS is computed by both libraries; a warning is raised if they differ by more than 0.1 LU
2. **Best-of-breed accuracy** – pyloudnorm for its well-tested BS.1770-4 implementation, pyebur128/libebur128 for its reference-quality True Peak and LRA
3. **Redundancy** – If one library has a bug for a specific signal type, the cross-check catches it

## Precision Validation Approach

The `PrecisionValidator` class validates computed metrics against a golden corpus of test vectors with strict tolerances:

| Metric | Tolerance |
|--------|-----------|
| Integrated LUFS | +/- 0.1 LU |
| True Peak | +/- 0.2 dB |
| Loudness Range (LRA) | +/- 0.2 LU |

### Golden Corpus

Located in `test_vectors/`, the corpus contains 15 test audio files: 5 synthetic signals and 10 official EBU R128 / ITU-R BS.1770-4 compliance vectors.

**Synthetic Test Signals:**

| File | Description |
|------|-------------|
| `sine_440hz.wav` | Full-scale 440 Hz sine wave (3s, 48 kHz, mono) |
| `sine_1khz_stereo.wav` | Full-scale 1 kHz sine wave (3s, 48 kHz, stereo) |
| `white_noise.wav` | White noise at -20 dBFS RMS (5s, 48 kHz, mono) |
| `silence.wav` | Digital silence (2s, 48 kHz, mono) |
| `pink_noise.wav` | Pink noise at -18 dBFS RMS (5s, 48 kHz, mono) |

**Official EBU R128 / BS.1770-4 Compliance Vectors (1 kHz):**

Generated per EBU Tech 3341 specifications with LUFS targets calibrated via pyloudnorm. All values independently verified against ffmpeg's ebur128 filter (libebur128).

| File | Description | Certified LUFS |
|------|-------------|----------------|
| `ebu_r128_tone_stereo_23lufs.wav` | EBU Tech 3341 Sec 6.1: Stereo 1 kHz at -23 LUFS (10s) | -23.0 LUFS |
| `ebu_r128_tone_stereo_33lufs.wav` | EBU Tech 3341 Sec 6.2: Stereo 1 kHz at -33 LUFS (10s) | -33.0 LUFS |
| `ebu_r128_tone_mono_23lufs.wav` | BS.1770-4 mono reference: Mono 1 kHz at -23 LUFS (10s) | -23.0 LUFS |
| `ebu_r128_tone_with_silence.wav` | EBU Tech 3341 Sec 7: Tone + silence gating test (20s) | -23.0 LUFS |
| `ebu_r128_two_tones.wav` | EBU Tech 3341 Sec 8: Two-tone relative gate test (20s) | -23.0 LUFS |

**Official EBU R128 / BS.1770-4 Compliance Vectors (997 Hz ITU-R):**

Uses 997 Hz per the ITU-R recommendation (K-weighting gain is near-unity at this frequency). Includes LRA compliance testing per EBU Tech 3342.

| File | Description | Certified Value |
|------|-------------|-----------------|
| `ebu_r128_stereo_997hz_23lufs.wav` | EBU Tech 3341 Seq 1: Stereo 997 Hz at -23 LUFS (20s) | I=-23.0 LUFS |
| `ebu_r128_stereo_997hz_33lufs.wav` | EBU Tech 3341 Seq 2: Stereo 997 Hz at -33 LUFS (20s) | I=-33.0 LUFS |
| `ebu_r128_mono_997hz_23lufs.wav` | BS.1770-4 mono: 997 Hz at -23 LUFS (20s) | I=-23.0 LUFS |
| `ebu_r128_gate_test.wav` | EBU Tech 3341 absolute gate: silence + tone (20s) | I=-23.0 LUFS |
| `ebu_r128_lra_test.wav` | EBU Tech 3342 LRA: alternating -20/-30 LUFS (60s) | LRA=10.0 LU |

Expected values are stored in `test_vectors/expected_values.json`. Each EBU entry includes the certified reference values in its description for cross-reference.

## Usage

### Computing Metrics

```python
from dsp.audio_loader import AudioLoader
from analysis.loudness.standards import StandardsMetering

audio = AudioLoader().load_wav("track.wav")
metering = StandardsMetering()
metrics = metering.compute_overall_metrics(audio)

print(f"Integrated LUFS: {metrics.integrated_lufs}")
print(f"Loudness Range:  {metrics.loudness_range_lu} LU")
print(f"True Peak:       {metrics.true_peak_dbfs} dBFS")
```

### Running Precision Validation

```bash
cd backend
python -m analysis.loudness.validate_precision
```

This generates `VALIDATION_REPORT.md` with detailed results.

### Running Tests

```bash
cd backend
pytest analysis/loudness/tests/ -v
```

## Known Limitations

- Audio is loaded as mono (stereo files are averaged by `AudioLoader`); per-channel True Peak requires raw stereo data
- LRA for very short signals (< 3s) may be unreliable due to insufficient gating windows
- Expected values in the golden corpus are approximate and should be validated against commercial reference tools (iZotope Insight, Nugen VisLM) for production use

## Future Improvements

- Add support for per-channel True Peak on stereo sources
- Add short-term and momentary loudness measurements
- Integrate loudness normalization targets (e.g. -14 LUFS for streaming)
