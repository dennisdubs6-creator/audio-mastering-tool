# Loudness Metering Precision Validation Report

## Summary

- **Total test vectors:** 15
- **Passed:** 15
- **Failed:** 0
- **Pass rate:** 100%

## Tolerances

| Metric | Tolerance |
|--------|-----------|
| Integrated LUFS | +/- 0.1 LU |
| True Peak | +/- 0.2 dB |
| Loudness Range | +/- 0.2 LU |

## Detailed Results

| Test File | Metric | Expected | Computed | Delta | Status |
|-----------|--------|----------|----------|-------|--------|
| ebu_r128_gate_test.wav | LUFS | -23.00 | -23.07 | 0.070 | PASS |
| | True Peak | -22.95 | -22.95 | 0.000 | PASS |
| | LRA | 3.79 | 3.79 | 0.000 | PASS |
| ebu_r128_lra_test.wav | LUFS | -22.60 | -22.60 | 0.000 | PASS |
| | True Peak | -19.95 | -19.95 | 0.000 | PASS |
| | LRA | 10.00 | 10.00 | 0.000 | PASS |
| ebu_r128_mono_997hz_23lufs.wav | LUFS | -23.00 | -23.00 | 0.000 | PASS |
| | True Peak | -19.94 | -19.94 | 0.000 | PASS |
| | LRA | 0.00 | 0.00 | 0.000 | PASS |
| ebu_r128_stereo_997hz_23lufs.wav | LUFS | -23.00 | -23.00 | 0.000 | PASS |
| | True Peak | -22.95 | -22.95 | 0.000 | PASS |
| | LRA | 0.00 | 0.00 | 0.000 | PASS |
| ebu_r128_stereo_997hz_33lufs.wav | LUFS | -33.00 | -33.00 | 0.000 | PASS |
| | True Peak | -32.94 | -32.94 | 0.000 | PASS |
| | LRA | 0.00 | 0.00 | 0.000 | PASS |
| ebu_r128_tone_mono_23lufs.wav | LUFS | -23.00 | -23.00 | 0.000 | PASS |
| | True Peak | -19.95 | -19.95 | 0.000 | PASS |
| | LRA | 1.00 | 1.00 | 0.000 | PASS |
| ebu_r128_tone_stereo_23lufs.wav | LUFS | -23.00 | -23.00 | 0.000 | PASS |
| | True Peak | -22.96 | -22.96 | 0.000 | PASS |
| | LRA | 1.00 | 1.00 | 0.000 | PASS |
| ebu_r128_tone_stereo_33lufs.wav | LUFS | -33.00 | -33.00 | 0.000 | PASS |
| | True Peak | -32.95 | -32.95 | 0.000 | PASS |
| | LRA | 1.00 | 1.00 | 0.000 | PASS |
| ebu_r128_tone_with_silence.wav | LUFS | -23.07 | -23.07 | 0.000 | PASS |
| | True Peak | -22.96 | -22.96 | 0.000 | PASS |
| | LRA | 4.40 | 4.40 | 0.000 | PASS |
| ebu_r128_two_tones.wav | LUFS | -23.06 | -23.06 | 0.000 | PASS |
| | True Peak | -22.96 | -22.96 | 0.000 | PASS |
| | LRA | 13.00 | 13.00 | 0.000 | PASS |
| pink_noise.wav | LUFS | -19.83 | -19.83 | 0.000 | PASS |
| | True Peak | -5.41 | -5.41 | 0.000 | PASS |
| | LRA | 2.12 | 2.12 | 0.000 | PASS |
| silence.wav | LUFS | N/A | N/A | 0.000 | PASS |
| | True Peak | -120.00 | -120.00 | 0.000 | PASS |
| | LRA | N/A | N/A | 0.000 | PASS |
| sine_1khz_stereo.wav | LUFS | -0.03 | -0.03 | 0.000 | PASS |
| | True Peak | 0.01 | 0.01 | 0.000 | PASS |
| | LRA | 2.56 | 2.56 | 0.000 | PASS |
| sine_440hz.wav | LUFS | -3.74 | -3.74 | 0.000 | PASS |
| | True Peak | 0.01 | 0.01 | 0.000 | PASS |
| | LRA | 2.56 | 2.56 | 0.000 | PASS |
| white_noise.wav | LUFS | -16.90 | -16.90 | 0.000 | PASS |
| | True Peak | -5.50 | -5.50 | 0.000 | PASS |
| | LRA | 2.19 | 2.19 | 0.000 | PASS |

## Overall Verdict

**PASS** – All test vectors are within professional-grade tolerances.
