"""
Band Integrator Module

Maps STFT frequency bins to predefined frequency bands and computes
per-band energy and time-averaged magnitude. Uses inclusive lower bound
and exclusive upper bound for frequency ranges.
"""

import numpy as np

from .audio_types import BandData, STFTData


class BandIntegrator:
    """Maps STFT output to frequency bands and computes per-band metrics.

    Each band is defined by a name and a (min_hz, max_hz) range.  For each
    band the integrator selects the STFT bins whose centre frequencies fall
    within [min_hz, max_hz) and computes:
      - total energy  = sum of squared magnitudes across bins and frames
      - time-averaged magnitude = mean of magnitude across frequency bins
        for each time frame

    Args:
        band_definitions: Mapping of band name to (min_hz, max_hz).
            Typically ``config.constants.FREQUENCY_BANDS``.

    Example:
        from config.constants import FREQUENCY_BANDS
        integrator = BandIntegrator(FREQUENCY_BANDS)
        bands = integrator.integrate_bands(stft_data)
        for b in bands:
            print(f"{b.band_name}: energy={b.energy:.4f}")
    """

    def __init__(self, band_definitions: dict[str, tuple[int, int]]) -> None:
        self._band_definitions = band_definitions

    def integrate_bands(self, stft_data: STFTData) -> list[BandData]:
        """Integrate STFT magnitude into frequency bands.

        Args:
            stft_data: STFTData from ``STFTProcessor.compute_stft``.

        Returns:
            List of BandData objects, one per band, in the same order as
            the band definitions dict.
        """
        results: list[BandData] = []

        for band_name, (freq_min, freq_max) in self._band_definitions.items():
            indices = self.get_band_bin_indices(
                stft_data.frequencies, float(freq_min), float(freq_max)
            )

            if len(indices) == 0:
                # Fall back to nearest bin when the range contains no bins
                centre = (freq_min + freq_max) / 2.0
                nearest_idx = int(
                    np.argmin(np.abs(stft_data.frequencies - centre))
                )
                indices = np.array([nearest_idx])

            band_mag = stft_data.magnitude[indices, :]
            energy = float(np.sum(band_mag ** 2))
            avg_magnitude = np.mean(band_mag, axis=0)

            results.append(
                BandData(
                    band_name=band_name,
                    freq_min=float(freq_min),
                    freq_max=float(freq_max),
                    energy=energy,
                    magnitude=avg_magnitude,
                )
            )

        return results

    @staticmethod
    def get_band_bin_indices(
        frequencies: np.ndarray,
        freq_min: float,
        freq_max: float,
    ) -> np.ndarray:
        """Return the bin indices whose centre frequencies lie in [freq_min, freq_max).

        Handles Nyquist and empty-range edge cases gracefully.

        Args:
            frequencies: 1-D array of bin centre frequencies in Hz.
            freq_min: Lower frequency boundary (inclusive).
            freq_max: Upper frequency boundary (exclusive).

        Returns:
            1-D integer array of matching bin indices (may be empty).
        """
        return np.where(
            (frequencies >= freq_min) & (frequencies < freq_max)
        )[0]
