"""
STFT Processor Module

Computes the Short-Time Fourier Transform of audio data using fixed
parameters: 4096-sample Hann window, 1024-sample hop (75% overlap),
and 4096-point FFT. The output is deterministic for identical input.
"""

import numpy as np
from scipy.signal import stft

from .audio_types import AudioData, STFTData


class STFTProcessor:
    """Computes the Short-Time Fourier Transform with fixed parameters.

    Parameters are chosen for high frequency resolution (~11.7 Hz at 48 kHz)
    while maintaining reasonable time resolution (~21 ms hop).

    Class Constants:
        WINDOW_SIZE: Analysis window length in samples (4096).
        HOP_SIZE: Hop between successive windows in samples (1024).
        WINDOW_TYPE: Window function applied before FFT ('hann').
        FFT_SIZE: Number of FFT points (4096).

    Example:
        processor = STFTProcessor()
        stft_data = processor.compute_stft(audio)
        print(f"Frequency bins: {stft_data.magnitude.shape[0]}")
        print(f"Time frames: {stft_data.magnitude.shape[1]}")
    """

    WINDOW_SIZE: int = 4096
    HOP_SIZE: int = 1024
    WINDOW_TYPE: str = "hann"
    FFT_SIZE: int = 4096

    def compute_stft(self, audio: AudioData) -> STFTData:
        """Compute the STFT of the given audio data.

        Uses scipy.signal.stft with fixed parameters. The computation is
        deterministic: the same input always produces the same output.

        Args:
            audio: AudioData instance with mono float32 samples.

        Returns:
            STFTData containing magnitude and phase spectra together with
            their frequency and time axes.
        """
        frequencies, times, stft_complex = stft(
            audio.samples,
            fs=audio.sample_rate,
            window=self.WINDOW_TYPE,
            nperseg=self.WINDOW_SIZE,
            noverlap=self.WINDOW_SIZE - self.HOP_SIZE,
            nfft=self.FFT_SIZE,
        )

        magnitude = np.abs(stft_complex)
        phase = np.angle(stft_complex)

        return STFTData(
            magnitude=magnitude,
            phase=phase,
            frequencies=frequencies,
            times=times,
            window_size=self.WINDOW_SIZE,
            hop_size=self.HOP_SIZE,
        )

    def get_frequency_resolution(self, sample_rate: int) -> float:
        """Return the frequency resolution in Hz.

        Args:
            sample_rate: Audio sample rate in Hz.

        Returns:
            Spacing between adjacent frequency bins (sample_rate / FFT_SIZE).
        """
        return sample_rate / self.FFT_SIZE
