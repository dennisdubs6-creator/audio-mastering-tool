"""
Analysis Engine — orchestrates per-band metric computation.

Loads audio, computes the STFT, integrates frequency bands, and
dispatches each band to the six metric modules (level, dynamics,
spectral, stereo, harmonics, transients).  Results are returned as
a list of ``BandMetrics`` ORM instances ready for database persistence.
"""

import logging
import math
from typing import Callable

import numpy as np
from scipy.signal import istft as scipy_istft, stft as scipy_stft

from api.models import BandMetrics, OverallMetrics
from config.constants import FREQUENCY_BANDS
from dsp.audio_loader import AudioLoader, detect_silence, detect_clipping
from dsp.audio_types import AudioData, BandData, STFTData
from dsp.band_integrator import BandIntegrator
from dsp.stft_processor import STFTProcessor

from .loudness.standards import StandardsMetering
from .metrics import dynamics, harmonics, level, spectral, stereo, transients

logger = logging.getLogger(__name__)


def _sanitize(value: float | None) -> float | None:
    """Replace NaN / Inf with ``None`` so the value is safe for SQLite."""
    if value is None:
        return None
    if not math.isfinite(value):
        return None
    return value


class AnalysisEngine:
    """Orchestrates per-band audio metric computation and overall loudness.

    Parameters
    ----------
    stft_processor : STFTProcessor
        Computes the Short-Time Fourier Transform.
    band_integrator : BandIntegrator
        Maps STFT bins to frequency bands.
    audio_loader : AudioLoader
        Loads and validates WAV files.

    Example
    -------
    >>> engine = AnalysisEngine(
    ...     STFTProcessor(),
    ...     BandIntegrator(FREQUENCY_BANDS),
    ...     AudioLoader(),
    ... )
    >>> band_metrics, overall = engine.analyze_audio("track.wav", "some-uuid")
    """

    def __init__(
        self,
        stft_processor: STFTProcessor,
        band_integrator: BandIntegrator,
        audio_loader: AudioLoader,
    ) -> None:
        self._stft = stft_processor
        self._bands = band_integrator
        self._loader = audio_loader
        self._standards_metering = StandardsMetering()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_audio(
        self,
        file_path: str,
        analysis_id: str,
        progress_callback: Callable[[str, dict], None] | None = None,
    ) -> tuple[list[BandMetrics], OverallMetrics, list[str]]:
        """Run the full analysis pipeline on a WAV file.

        Computes per-band metrics and overall loudness metrics
        (Integrated LUFS, LRA, True Peak) via ``StandardsMetering``.

        Parameters
        ----------
        file_path : str
            Path to the WAV file.
        analysis_id : str
            UUID of the parent ``Analysis`` record.
        progress_callback : callable, optional
            ``callback(band_name, metrics_dict)`` invoked after each
            band completes.

        Returns
        -------
        tuple[list[BandMetrics], OverallMetrics, list[str]]
            Per-band ``BandMetrics`` ORM instances, an ``OverallMetrics``
            instance with ``integrated_lufs``, ``loudness_range_lu``, and
            ``true_peak_dbfs`` populated, and a list of warning messages.
        """
        # 1. Load mono audio and compute STFT
        audio_data: AudioData = self._loader.load_wav(file_path)

        # Edge case detection
        warnings: list[str] = []
        if detect_silence(audio_data.samples):
            warnings.append("File appears to be silent (RMS < -120 dBFS)")
            logger.warning("Silent file detected: %s", file_path)
        if detect_clipping(audio_data.samples):
            warnings.append("File contains clipping (true peak > -0.1 dBFS)")
            logger.warning("Clipping detected: %s", file_path)
        if audio_data.dc_offset_detected:
            warnings.append("DC offset detected and removed")
            logger.warning(
                "DC offset (mean=%.6f) removed: %s",
                audio_data.dc_offset_mean,
                file_path,
            )

        stft_data: STFTData = self._stft.compute_stft(audio_data)

        # 2. Integrate bands
        band_data_list: list[BandData] = self._bands.integrate_bands(stft_data)

        # 3. Reuse already-loaded stereo frames; only re-read as fallback
        if audio_data.channels == 2 and audio_data.stereo_samples is not None:
            stereo_pair = (
                audio_data.stereo_samples[:, 0],
                audio_data.stereo_samples[:, 1],
            )
        else:
            stereo_pair = stereo.load_stereo_audio(file_path)
        stereo_stft_pair = (
            self._compute_stereo_stft(stereo_pair, audio_data.sample_rate)
            if stereo_pair is not None
            else None
        )

        # 4. Process each band
        band_results: list[BandMetrics] = []

        for band_data in band_data_list:
            band_samples = self._reconstruct_band_samples(
                stft_data, band_data, audio_data.sample_rate
            )

            # Extract per-band stereo slices via canonical STFT path
            left_band, right_band = self._get_band_stereo_samples(
                stereo_stft_pair, band_data, audio_data.sample_rate
            )

            metrics_dict = self._compute_all_metrics(
                band_data=band_data,
                band_samples=band_samples,
                sample_rate=audio_data.sample_rate,
                left=left_band,
                right=right_band,
            )

            bm = BandMetrics(
                analysis_id=analysis_id,
                band_name=band_data.band_name,
                freq_min=int(band_data.freq_min),
                freq_max=int(band_data.freq_max),
                **{k: _sanitize(v) for k, v in metrics_dict.items()},
            )
            band_results.append(bm)

            if progress_callback is not None:
                progress_callback(band_data.band_name, metrics_dict)

            logger.info(
                "Band '%s' analysis complete (%d-%d Hz)",
                band_data.band_name,
                int(band_data.freq_min),
                int(band_data.freq_max),
            )

        # 5. Compute overall loudness metrics (ITU-R BS.1770-4 / EBU R128)
        overall_metrics = self._standards_metering.compute_overall_metrics(
            audio_data
        )
        overall_metrics.analysis_id = analysis_id

        # Store warnings as JSON in overall metrics
        if warnings:
            import json
            overall_metrics.warnings = json.dumps(warnings)

        return band_results, overall_metrics, warnings

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _reconstruct_band_samples(
        self,
        stft_data: STFTData,
        band_data: BandData,
        sample_rate: int,
    ) -> np.ndarray:
        """Reconstruct time-domain samples for a single band via inverse STFT.

        Zeroes all frequency bins outside the band, then uses
        ``scipy.signal.istft`` to synthesise time-domain audio.
        """
        indices = BandIntegrator.get_band_bin_indices(
            stft_data.frequencies, band_data.freq_min, band_data.freq_max
        )

        if indices.size == 0:
            centre = (band_data.freq_min + band_data.freq_max) / 2.0
            nearest = int(np.argmin(np.abs(stft_data.frequencies - centre)))
            indices = np.array([nearest])

        # Build band-limited complex STFT
        band_stft = np.zeros_like(stft_data.magnitude, dtype=complex)
        band_stft[indices, :] = (
            stft_data.magnitude[indices, :]
            * np.exp(1j * stft_data.phase[indices, :])
        )

        _, band_samples = scipy_istft(
            band_stft,
            fs=sample_rate,
            window="hann",
            nperseg=stft_data.window_size,
            noverlap=stft_data.window_size - stft_data.hop_size,
            nfft=stft_data.window_size,
        )

        return band_samples.astype(np.float32)

    def _compute_stereo_stft(
        self,
        stereo_pair: tuple[np.ndarray, np.ndarray],
        sample_rate: int,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute STFT for both stereo channels using canonical parameters.

        Uses the same window size, hop size, and FFT size as
        ``STFTProcessor`` so that the frequency bins are identical to the
        mono STFT used elsewhere in the pipeline.

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray]
            ``(stft_left, stft_right, frequencies)`` where each STFT is
            the complex-valued output with the same bin layout as the
            mono STFT.
        """
        left, right = stereo_pair
        ws = self._stft.WINDOW_SIZE
        hs = self._stft.HOP_SIZE

        freqs, _, stft_left = scipy_stft(
            left, fs=sample_rate, window="hann",
            nperseg=ws, noverlap=ws - hs, nfft=ws,
        )
        _, _, stft_right = scipy_stft(
            right, fs=sample_rate, window="hann",
            nperseg=ws, noverlap=ws - hs, nfft=ws,
        )

        return stft_left, stft_right, freqs

    def _get_band_stereo_samples(
        self,
        stereo_stft_pair: tuple[np.ndarray, np.ndarray, np.ndarray] | None,
        band_data: BandData,
        sample_rate: int,
    ) -> tuple[np.ndarray | None, np.ndarray | None]:
        """Reconstruct band-limited stereo signals via the canonical STFT path.

        Uses the same ``BandIntegrator.get_band_bin_indices`` bin selection
        as ``_reconstruct_band_samples`` so that all per-band metrics are
        aligned to the canonical STFT.  Returns ``(None, None)`` when the
        input is mono.
        """
        if stereo_stft_pair is None:
            return None, None

        stft_left, stft_right, frequencies = stereo_stft_pair

        indices = BandIntegrator.get_band_bin_indices(
            frequencies, band_data.freq_min, band_data.freq_max
        )

        if indices.size == 0:
            centre = (band_data.freq_min + band_data.freq_max) / 2.0
            nearest = int(np.argmin(np.abs(frequencies - centre)))
            indices = np.array([nearest])

        ws = self._stft.WINDOW_SIZE
        hs = self._stft.HOP_SIZE

        # Left channel — zero bins outside band, inverse STFT
        band_l = np.zeros_like(stft_left)
        band_l[indices, :] = stft_left[indices, :]
        _, left_band = scipy_istft(
            band_l, fs=sample_rate, window="hann",
            nperseg=ws, noverlap=ws - hs, nfft=ws,
        )

        # Right channel — same bin selection
        band_r = np.zeros_like(stft_right)
        band_r[indices, :] = stft_right[indices, :]
        _, right_band = scipy_istft(
            band_r, fs=sample_rate, window="hann",
            nperseg=ws, noverlap=ws - hs, nfft=ws,
        )

        return left_band.astype(np.float32), right_band.astype(np.float32)

    @staticmethod
    def _compute_all_metrics(
        band_data: BandData,
        band_samples: np.ndarray,
        sample_rate: int,
        left: np.ndarray | None,
        right: np.ndarray | None,
    ) -> dict[str, float | None]:
        """Compute all 19 metrics for a single band.

        Each metric call is wrapped in a try/except so that a failure
        in one metric does not prevent the rest from being computed.
        """
        results: dict[str, float | None] = {}

        # --- Level ---
        try:
            results["band_rms_dbfs"] = level.compute_band_rms_dbfs(
                band_samples
            )
        except Exception:
            logger.exception("band_rms_dbfs failed")
            results["band_rms_dbfs"] = None

        try:
            results["band_true_peak_dbfs"] = level.compute_band_true_peak_dbfs(
                band_samples
            )
        except Exception:
            logger.exception("band_true_peak_dbfs failed")
            results["band_true_peak_dbfs"] = None

        try:
            results["band_level_range_db"] = level.compute_band_level_range_db(
                band_samples, sample_rate
            )
        except Exception:
            logger.exception("band_level_range_db failed")
            results["band_level_range_db"] = None

        # --- Dynamics ---
        try:
            results["dynamic_range_db"] = dynamics.compute_dynamic_range_db(
                band_samples
            )
        except Exception:
            logger.exception("dynamic_range_db failed")
            results["dynamic_range_db"] = None

        try:
            results["crest_factor_db"] = dynamics.compute_crest_factor_db(
                band_samples
            )
        except Exception:
            logger.exception("crest_factor_db failed")
            results["crest_factor_db"] = None

        try:
            results["rms_db"] = dynamics.compute_rms_db(band_samples)
        except Exception:
            logger.exception("rms_db failed")
            results["rms_db"] = None

        # --- Spectral ---
        try:
            results["spectral_centroid_hz"] = (
                spectral.compute_spectral_centroid_hz(band_samples, sample_rate)
            )
        except Exception:
            logger.exception("spectral_centroid_hz failed")
            results["spectral_centroid_hz"] = None

        try:
            results["spectral_rolloff_hz"] = (
                spectral.compute_spectral_rolloff_hz(band_samples, sample_rate)
            )
        except Exception:
            logger.exception("spectral_rolloff_hz failed")
            results["spectral_rolloff_hz"] = None

        try:
            results["spectral_flatness"] = spectral.compute_spectral_flatness(
                band_samples
            )
        except Exception:
            logger.exception("spectral_flatness failed")
            results["spectral_flatness"] = None

        try:
            results["energy_db"] = spectral.compute_energy_db_from_energy(
                band_data.energy, num_frames=band_data.magnitude.shape[0]
            )
        except Exception:
            logger.exception("energy_db failed")
            results["energy_db"] = None

        # --- Stereo ---
        try:
            results["stereo_width_percent"] = (
                stereo.compute_stereo_width_percent(left, right)
            )
        except Exception:
            logger.exception("stereo_width_percent failed")
            results["stereo_width_percent"] = None

        try:
            results["phase_correlation"] = stereo.compute_phase_correlation(
                left, right
            )
        except Exception:
            logger.exception("phase_correlation failed")
            results["phase_correlation"] = None

        try:
            results["mid_energy_db"] = stereo.compute_mid_energy_db(left, right)
        except Exception:
            logger.exception("mid_energy_db failed")
            results["mid_energy_db"] = None

        try:
            results["side_energy_db"] = stereo.compute_side_energy_db(
                left, right
            )
        except Exception:
            logger.exception("side_energy_db failed")
            results["side_energy_db"] = None

        # --- HPSS (run once, reuse for harmonics + transients) ---
        hpss_harmonic: np.ndarray | None = None
        hpss_percussive: np.ndarray | None = None
        try:
            hpss_harmonic, hpss_percussive = harmonics.compute_hpss(
                band_samples
            )
        except Exception:
            logger.exception("HPSS separation failed")

        # --- Harmonics ---
        try:
            results["thd_percent"] = harmonics.compute_thd_percent(
                band_samples, sample_rate, harmonic=hpss_harmonic
            )
        except Exception:
            logger.exception("thd_percent failed")
            results["thd_percent"] = None

        try:
            results["harmonic_ratio"] = harmonics.compute_harmonic_ratio(
                band_samples,
                harmonic=hpss_harmonic,
                percussive=hpss_percussive,
            )
        except Exception:
            logger.exception("harmonic_ratio failed")
            results["harmonic_ratio"] = None

        try:
            results["inharmonicity"] = harmonics.compute_inharmonicity(
                band_samples, sample_rate
            )
        except Exception:
            logger.exception("inharmonicity failed")
            results["inharmonicity"] = None

        # --- Transients ---
        try:
            results["transient_preservation"] = (
                transients.compute_transient_preservation(
                    band_samples, sample_rate,
                    percussive=hpss_percussive,
                )
            )
        except Exception:
            logger.exception("transient_preservation failed")
            results["transient_preservation"] = None

        try:
            results["attack_time_ms"] = transients.compute_attack_time_ms(
                band_samples, sample_rate
            )
        except Exception:
            logger.exception("attack_time_ms failed")
            results["attack_time_ms"] = None

        return results
