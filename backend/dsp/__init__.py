"""
DSP Module - Audio analysis pipeline.

Provides three core components:
  - AudioLoader:     WAV file loading and validation
  - STFTProcessor:   Short-Time Fourier Transform computation
  - BandIntegrator:  Frequency-band energy integration
"""

from .audio_loader import AudioLoader
from .audio_types import AudioData, BandData, STFTData
from .band_integrator import BandIntegrator
from .stft_processor import STFTProcessor

__all__ = [
    "AudioLoader",
    "STFTProcessor",
    "BandIntegrator",
    "AudioData",
    "STFTData",
    "BandData",
]
