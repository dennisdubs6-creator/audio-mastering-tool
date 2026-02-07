"""Tests for STFTProcessor."""

import numpy as np

from dsp.audio_types import AudioData, STFTData
from dsp.stft_processor import STFTProcessor


class TestComputeSTFTShape:
    """Output array shapes match expected dimensions."""

    def test_magnitude_freq_bins(self, sample_stft_data: STFTData) -> None:
        expected_bins = STFTProcessor.FFT_SIZE // 2 + 1  # 2049
        assert sample_stft_data.magnitude.shape[0] == expected_bins

    def test_phase_shape_matches_magnitude(self, sample_stft_data: STFTData) -> None:
        assert sample_stft_data.phase.shape == sample_stft_data.magnitude.shape

    def test_frequencies_length(self, sample_stft_data: STFTData) -> None:
        expected_bins = STFTProcessor.FFT_SIZE // 2 + 1
        assert len(sample_stft_data.frequencies) == expected_bins

    def test_times_length(self, sample_stft_data: STFTData) -> None:
        assert len(sample_stft_data.times) == sample_stft_data.magnitude.shape[1]


class TestSTFTDeterminism:
    """Identical input must produce identical output."""

    def test_magnitude_determinism(self, sample_audio_data: AudioData) -> None:
        processor = STFTProcessor()
        result1 = processor.compute_stft(sample_audio_data)
        result2 = processor.compute_stft(sample_audio_data)
        assert np.allclose(result1.magnitude, result2.magnitude)

    def test_phase_determinism(self, sample_audio_data: AudioData) -> None:
        processor = STFTProcessor()
        result1 = processor.compute_stft(sample_audio_data)
        result2 = processor.compute_stft(sample_audio_data)
        assert np.allclose(result1.phase, result2.phase)


class TestPeakDetection:
    """A 440 Hz sine wave should produce a clear peak near 440 Hz."""

    def test_440hz_peak(self, sample_stft_data: STFTData) -> None:
        # Average magnitude over time to get a single spectrum
        avg_spectrum = np.mean(sample_stft_data.magnitude, axis=1)
        peak_idx = int(np.argmax(avg_spectrum))
        peak_freq = sample_stft_data.frequencies[peak_idx]

        # Frequency resolution at 48 kHz with 4096 FFT ≈ 11.72 Hz
        freq_resolution = 48000 / STFTProcessor.FFT_SIZE
        assert abs(peak_freq - 440.0) <= freq_resolution


class TestFrequencyResolution:
    """get_frequency_resolution returns sample_rate / FFT_SIZE."""

    def test_resolution_48khz(self) -> None:
        processor = STFTProcessor()
        res = processor.get_frequency_resolution(48000)
        assert abs(res - 48000 / 4096) < 1e-6

    def test_resolution_44100(self) -> None:
        processor = STFTProcessor()
        res = processor.get_frequency_resolution(44100)
        assert abs(res - 44100 / 4096) < 1e-6


class TestSTFTParameters:
    """Class constants match the specification."""

    def test_window_size(self) -> None:
        assert STFTProcessor.WINDOW_SIZE == 4096

    def test_hop_size(self) -> None:
        assert STFTProcessor.HOP_SIZE == 1024

    def test_fft_size(self) -> None:
        assert STFTProcessor.FFT_SIZE == 4096
