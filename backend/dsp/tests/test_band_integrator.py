"""Tests for BandIntegrator."""

import numpy as np
import pytest

from config.constants import BAND_NAMES, FREQUENCY_BANDS
from dsp.audio_types import STFTData
from dsp.band_integrator import BandIntegrator


@pytest.fixture
def integrator() -> BandIntegrator:
    return BandIntegrator(FREQUENCY_BANDS)


class TestIntegrateBandsCount:
    """Exactly 5 BandData objects with expected names."""

    def test_band_count(self, integrator: BandIntegrator, sample_stft_data: STFTData) -> None:
        bands = integrator.integrate_bands(sample_stft_data)
        assert len(bands) == 5

    def test_band_names(self, integrator: BandIntegrator, sample_stft_data: STFTData) -> None:
        bands = integrator.integrate_bands(sample_stft_data)
        names = [b.band_name for b in bands]
        assert names == BAND_NAMES


class Test440HzInMidBand:
    """440 Hz sine wave energy should concentrate in the low_mid band (200-500 Hz)."""

    def test_highest_energy_band(self, integrator: BandIntegrator, sample_stft_data: STFTData) -> None:
        bands = integrator.integrate_bands(sample_stft_data)
        energies = {b.band_name: b.energy for b in bands}
        max_band = max(energies, key=energies.get)
        # 440 Hz falls in the low_mid band (200-500 Hz)
        assert max_band == "low_mid"

    def test_other_bands_lower(self, integrator: BandIntegrator, sample_stft_data: STFTData) -> None:
        bands = integrator.integrate_bands(sample_stft_data)
        energies = {b.band_name: b.energy for b in bands}
        dominant_energy = energies["low_mid"]
        for name, energy in energies.items():
            if name != "low_mid":
                assert energy < dominant_energy


class TestBandFrequencyRanges:
    """Each BandData carries the correct frequency boundaries."""

    def test_frequency_ranges(self, integrator: BandIntegrator, sample_stft_data: STFTData) -> None:
        bands = integrator.integrate_bands(sample_stft_data)
        for band in bands:
            expected_min, expected_max = FREQUENCY_BANDS[band.band_name]
            assert band.freq_min == float(expected_min)
            assert band.freq_max == float(expected_max)


class TestBandEnergyCalculation:
    """Energy values are positive sums of squared magnitudes."""

    def test_energy_positive(self, integrator: BandIntegrator, sample_stft_data: STFTData) -> None:
        bands = integrator.integrate_bands(sample_stft_data)
        for band in bands:
            assert band.energy >= 0.0

    def test_energy_sum_of_squares(self, integrator: BandIntegrator, sample_stft_data: STFTData) -> None:
        """Manually recompute energy for one band and compare."""
        bands = integrator.integrate_bands(sample_stft_data)
        band = bands[0]  # low band
        indices = BandIntegrator.get_band_bin_indices(
            sample_stft_data.frequencies, band.freq_min, band.freq_max
        )
        expected_energy = float(np.sum(sample_stft_data.magnitude[indices, :] ** 2))
        assert abs(band.energy - expected_energy) < 1e-6


class TestBinIndicesEdgeCases:
    """get_band_bin_indices handles boundary and edge conditions."""

    def test_exact_boundary(self) -> None:
        freqs = np.array([0.0, 100.0, 200.0, 300.0])
        indices = BandIntegrator.get_band_bin_indices(freqs, 100.0, 200.0)
        np.testing.assert_array_equal(indices, [1])

    def test_empty_range(self) -> None:
        freqs = np.array([0.0, 100.0, 200.0])
        indices = BandIntegrator.get_band_bin_indices(freqs, 150.0, 160.0)
        assert len(indices) == 0

    def test_nyquist_handling(self) -> None:
        freqs = np.array([0.0, 12000.0, 24000.0])
        indices = BandIntegrator.get_band_bin_indices(freqs, 6000.0, 20000.0)
        np.testing.assert_array_equal(indices, [1])


class TestBandIntegrationDeterminism:
    """Repeated integration yields identical results."""

    def test_determinism(self, integrator: BandIntegrator, sample_stft_data: STFTData) -> None:
        bands1 = integrator.integrate_bands(sample_stft_data)
        bands2 = integrator.integrate_bands(sample_stft_data)
        for b1, b2 in zip(bands1, bands2):
            assert b1.band_name == b2.band_name
            assert b1.energy == b2.energy
            np.testing.assert_array_equal(b1.magnitude, b2.magnitude)
