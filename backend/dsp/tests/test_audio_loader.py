"""Tests for AudioLoader."""

import os
import tempfile

import numpy as np
import pytest
import soundfile as sf

from dsp.audio_loader import AudioLoader
from dsp.tests.conftest import generate_sine_wave


class TestLoadValidWav:
    """Loading a well-formed WAV file."""

    def test_sample_rate(self, test_sine_wave_440hz: str) -> None:
        audio = AudioLoader().load_wav(test_sine_wave_440hz)
        assert audio.sample_rate == 48000

    def test_bit_depth(self, test_sine_wave_440hz: str) -> None:
        audio = AudioLoader().load_wav(test_sine_wave_440hz)
        assert audio.bit_depth == 16

    def test_channels(self, test_sine_wave_440hz: str) -> None:
        audio = AudioLoader().load_wav(test_sine_wave_440hz)
        assert audio.channels == 1

    def test_duration(self, test_sine_wave_440hz: str) -> None:
        audio = AudioLoader().load_wav(test_sine_wave_440hz)
        assert abs(audio.duration - 3.0) < 0.01

    def test_samples_dtype(self, test_sine_wave_440hz: str) -> None:
        audio = AudioLoader().load_wav(test_sine_wave_440hz)
        assert audio.samples.dtype == np.float32

    def test_samples_range(self, test_sine_wave_440hz: str) -> None:
        audio = AudioLoader().load_wav(test_sine_wave_440hz)
        assert audio.samples.min() >= -1.0
        assert audio.samples.max() <= 1.0

    def test_samples_shape(self, test_sine_wave_440hz: str) -> None:
        audio = AudioLoader().load_wav(test_sine_wave_440hz)
        expected_samples = int(48000 * 3.0)
        assert audio.samples.shape == (expected_samples,)


class TestLoadInvalidFiles:
    """Rejection of invalid or unsupported files."""

    def test_load_invalid_file_format(self, tmp_path) -> None:
        txt_file = tmp_path / "not_audio.txt"
        txt_file.write_text("hello")
        with pytest.raises(ValueError, match="Unsupported file format"):
            AudioLoader().load_wav(str(txt_file))

    def test_load_unsupported_sample_rate(self) -> None:
        path = generate_sine_wave(sample_rate=96000)
        try:
            # Write with a supported subtype but unsupported rate
            # generate_sine_wave already wrote at 96000
            with pytest.raises(ValueError, match="Unsupported sample rate"):
                AudioLoader().load_wav(path)
        finally:
            os.remove(path)

    def test_load_nonexistent_file(self) -> None:
        with pytest.raises(ValueError, match="File not found"):
            AudioLoader().load_wav("/nonexistent/path/file.wav")


class TestValidateFile:
    """AudioLoader.validate_file quick checks."""

    def test_valid_file(self, test_sine_wave_440hz: str) -> None:
        assert AudioLoader().validate_file(test_sine_wave_440hz) is True

    def test_nonexistent_file(self) -> None:
        assert AudioLoader().validate_file("/no/such/file.wav") is False

    def test_non_wav_extension(self, tmp_path) -> None:
        p = tmp_path / "audio.mp3"
        p.write_bytes(b"\x00")
        assert AudioLoader().validate_file(str(p)) is False


class TestStereoToMono:
    """Stereo files are averaged down to mono."""

    def test_stereo_to_mono_conversion(self) -> None:
        path = generate_sine_wave(channels=2)
        try:
            audio = AudioLoader().load_wav(path)
            assert audio.channels == 2  # original channel count preserved
            assert audio.samples.ndim == 1  # but samples are mono
        finally:
            os.remove(path)

    def test_stereo_averaging(self) -> None:
        """Left=1.0 and right=-1.0 should average to ~0.0."""
        sr = 48000
        n = sr  # 1 second
        left = np.ones(n, dtype=np.float64)
        right = -np.ones(n, dtype=np.float64)
        stereo = np.column_stack([left, right])

        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        sf.write(path, stereo, sr, subtype="PCM_16")

        try:
            audio = AudioLoader().load_wav(path)
            # After int16 quantisation and averaging the result won't be
            # exactly 0 but should be very close.
            assert np.max(np.abs(audio.samples)) < 0.01
        finally:
            os.remove(path)
