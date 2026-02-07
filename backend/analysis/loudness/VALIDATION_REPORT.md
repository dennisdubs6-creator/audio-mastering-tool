# Loudness Metering Precision Validation Report

## Summary

- **Total test vectors:** 5
- **Passed:** 5
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
| pink_noise.wav | LUFS | -19.83 | -19.83 | 0.000 | PASS |
| | True Peak | -5.41 | -5.41 | 0.000 | PASS |
| | LRA | 2.12 | 2.12 | 0.000 | PASS |
| silence.wav | LUFS | N/A | N/A | 0.000 | PASS |
| | True Peak | -120.00 | -120.00 | 0.000 | PASS |
| | LRA | N/A | N/A | 0.000 | PASS |
| sine_1khz_stereo.wav | LUFS | -3.05 | -3.05 | 0.000 | PASS |
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
