# Analysis Package

Per-band audio metric computation engine for the Audio Mastering Tool.

## Architecture

```
analysis/
├── __init__.py          # Package entry point, exports AnalysisEngine
├── engine.py            # Orchestrator: loads audio, computes STFT, dispatches metrics
├── metrics/
│   ├── __init__.py
│   ├── level.py         # RMS (dBFS), true peak (dBFS), level range (dB)
│   ├── dynamics.py      # Dynamic range, crest factor, RMS (dB)
│   ├── spectral.py      # Spectral centroid, roll-off, flatness, energy
│   ├── stereo.py        # Stereo width, phase correlation, mid/side energy
│   ├── harmonics.py     # THD, harmonic ratio, inharmonicity
│   └── transients.py    # Transient preservation, attack time
└── tests/
    ├── conftest.py      # Shared fixtures (sine, noise, impulse, stereo, silence)
    ├── test_level_metrics.py
    ├── test_dynamics.py
    ├── test_spectral.py
    ├── test_stereo.py
    ├── test_harmonics.py
    └── test_transients.py
```

## Metric Computation Formulas

### Level Metrics
| Metric | Formula | Unit |
|--------|---------|------|
| Band RMS | `20 * log10(rms(magnitude))` | dBFS |
| True Peak | `20 * log10(max(abs(samples)))` | dBFS |
| Level Range | `percentile(90) - percentile(10)` of per-frame dB values | dB |

### Dynamics Metrics
| Metric | Formula | Unit |
|--------|---------|------|
| Dynamic Range | `20 * log10(peak / rms)` | dB |
| Crest Factor | `20 * log10(peak / rms)` | dB |
| RMS | `20 * log10(rms(magnitude))` | dB |

### Spectral Metrics
| Metric | Source | Unit |
|--------|--------|------|
| Spectral Centroid | `librosa.feature.spectral_centroid` | Hz |
| Spectral Roll-off | `librosa.feature.spectral_rolloff` (85 %) | Hz |
| Spectral Flatness | `librosa.feature.spectral_flatness` | [0, 1] |
| Energy | `10 * log10(sum(magnitude ** 2))` | dB |

### Stereo Metrics
| Metric | Formula | Unit |
|--------|---------|------|
| Stereo Width | `100 * side_energy / (mid_energy + side_energy)` | % |
| Phase Correlation | `corrcoef(left, right)` | [-1, 1] |
| Mid Energy | `10 * log10(sum(((L+R)/2) ** 2))` | dB |
| Side Energy | `10 * log10(sum(((L-R)/2) ** 2))` | dB |

### Harmonics Metrics
| Metric | Method | Unit |
|--------|--------|------|
| THD | `100 * residual_rms / total_rms` after harmonic separation | % |
| Harmonic Ratio | `harmonic_energy / (harmonic + percussive)` | [0, 1] |
| Inharmonicity | Mean deviation of peaks from ideal harmonics | [0, 1] |

### Transient Metrics
| Metric | Method | Unit |
|--------|--------|------|
| Transient Preservation | `percussive_energy / total_energy` | [0, 1] |
| Attack Time | Mean onset-to-peak time across detected onsets | ms |

## Usage

```python
from analysis.engine import AnalysisEngine
from config.constants import FREQUENCY_BANDS
from dsp.audio_loader import AudioLoader
from dsp.band_integrator import BandIntegrator
from dsp.stft_processor import STFTProcessor

engine = AnalysisEngine(
    stft_processor=STFTProcessor(),
    band_integrator=BandIntegrator(FREQUENCY_BANDS),
    audio_loader=AudioLoader(),
)

band_metrics = engine.analyze_audio(
    file_path="track.wav",
    analysis_id="some-uuid",
    progress_callback=lambda band, metrics: print(f"{band}: done"),
)
```

## Testing

```bash
cd backend
pytest analysis/tests/ -v
```

### Test Signals

| Fixture | Description | Expected behaviour |
|---------|-------------|-------------------|
| `sine_wave_440hz` | Pure 440 Hz, 3 s, 48 kHz | Centroid ~440 Hz, low THD, low flatness |
| `white_noise` | Uniform [-1,1], 3 s | High flatness (>0.5), low harmonic ratio |
| `impulse` | Dirac delta at sample 0 | High transient preservation |
| `stereo_test` | L=440 Hz, R=880 Hz | Measurable width, correlation !=1 |
| `silence` | All zeros | Floor values, no NaN/Inf |

## Performance

- STFT is computed once and reused for all metrics and bands.
- Band samples are reconstructed via inverse STFT (cached per band).
- Stereo channels are bandpass-filtered once per band.
- Librosa calls use float32 to reduce memory pressure.
- Target: < 30 s for a 3-minute stereo track at 48 kHz.
