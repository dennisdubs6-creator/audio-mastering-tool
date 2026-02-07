# DSP Module

Audio analysis pipeline for the Audio Mastering Tool. Provides WAV file loading, STFT computation, and frequency-band energy integration.

## Components

| Class | Responsibility |
|-------|---------------|
| `AudioLoader` | Load and validate WAV files (44.1/48 kHz, 16/24-bit, mono/stereo) |
| `STFTProcessor` | Compute Short-Time Fourier Transform with fixed parameters |
| `BandIntegrator` | Map STFT bins to 5 frequency bands and compute per-band energy |

## Usage

```python
from dsp import AudioLoader, STFTProcessor, BandIntegrator
from config.constants import FREQUENCY_BANDS

# Load audio
loader = AudioLoader()
audio = loader.load_wav('path/to/file.wav')

# Compute STFT
stft_processor = STFTProcessor()
stft = stft_processor.compute_stft(audio)

# Integrate bands
band_integrator = BandIntegrator(FREQUENCY_BANDS)
bands = band_integrator.integrate_bands(stft)

# Access results
for band in bands:
    print(f"{band.band_name}: {band.freq_min}-{band.freq_max} Hz, Energy: {band.energy}")
```

## STFT Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Window size | 4096 samples | ~85 ms at 48 kHz |
| Hop size | 1024 samples | 75% overlap |
| Window type | Hann | Smooth spectral leakage reduction |
| FFT size | 4096 | ~11.7 Hz frequency resolution at 48 kHz |

## Frequency Bands

| Band | Range | Character |
|------|-------|-----------|
| Low | 20–200 Hz | Sub-bass and bass fundamentals |
| Low Mid | 200–500 Hz | Warmth and body |
| Mid | 500–2000 Hz | Presence and vocal clarity |
| High Mid | 2000–6000 Hz | Brightness and detail |
| High | 6000–20000 Hz | Air and brilliance |

## Data Types

- **`AudioData`** — loaded samples (float32, mono, [-1, 1]) plus metadata
- **`STFTData`** — magnitude/phase spectra with frequency and time axes
- **`BandData`** — per-band energy and time-averaged magnitude

## Performance

The full pipeline (load → STFT → band integration) processes a 3-minute WAV file in under 5 seconds.

## Testing

Run the DSP tests from the `backend/` directory:

```bash
pytest dsp/tests/ -v
```

Tests use a generated 440 Hz sine wave fixture (48 kHz, 16-bit, 3 s) to ensure deterministic, reproducible results. The test suite covers:

- Valid WAV loading and metadata extraction
- Invalid file rejection with clear error messages
- STFT output shapes, determinism, and peak detection
- Band integration counts, frequency ranges, and energy calculation
- Edge cases (band boundaries, Nyquist frequency, empty ranges)
- Performance (3-minute audio < 5 s)
