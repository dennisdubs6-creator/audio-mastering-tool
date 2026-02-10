"""
Standards-compliant overall loudness metering.

Implements ITU-R BS.1770-4 integrated loudness (LUFS) and loudness range (LRA)
using pyloudnorm.  When pyebur128 (libebur128 bindings) is available, True Peak
is computed via ``state.true_peak()`` per BS.1770-4 and LUFS cross-validation
uses the independent libebur128 engine; otherwise True Peak falls back to 4x
oversampled peak detection and cross-validation uses a second pyloudnorm pass.
"""

import logging
import math

import numpy as np
import pyloudnorm as pyln
from scipy.signal import resample_poly

from dsp.audio_types import AudioData
from api.models import OverallMetrics

logger = logging.getLogger(__name__)

# Try to import pyebur128; fall back gracefully.
try:
    import pyebur128
    _HAS_PYEBUR128 = True
    logger.debug("pyebur128 available – will use for true peak and LUFS cross-validation")
except ImportError:
    _HAS_PYEBUR128 = False
    logger.warning(
        "pyebur128 not installed – BS.1770-4 true peak will use 4x oversample "
        "fallback and LUFS cross-validation will use pyloudnorm recheck. "
        "Install pyebur128>=0.3.1 for spec-required cross-check."
    )

# Maximum acceptable difference (in LU) between primary and cross-check
# integrated loudness measurements before a warning is raised.
CROSS_VALIDATION_THRESHOLD_LU = 0.1

# True Peak floor value for digital silence.
_TRUE_PEAK_FLOOR_DBFS = -120.0

# Oversampling factor for ITU-R BS.1770-4 True Peak measurement.
_TRUE_PEAK_OVERSAMPLE = 4


class StandardsMetering:
    """Compute overall loudness metrics using standards-compliant algorithms.

    Uses pyloudnorm (ITU-R BS.1770-4 pure-Python implementation) for
    Integrated LUFS and Loudness Range (LRA).  True Peak is measured via
    pyebur128 (libebur128) when available, with a 4x oversampled peak
    detection fallback per ITU-R BS.1770-4.  When pyebur128 is installed
    it also provides an independent LUFS cross-validation check.

    When the supplied :class:`AudioData` carries ``stereo_samples``, all
    metering operates on the untouched stereo frames so that inter-sample
    peaks and loudness are computed per BS.1770-4 multichannel rules
    rather than on a mono downmix.

    Example::

        from dsp.audio_loader import AudioLoader
        from analysis.loudness.standards import StandardsMetering

        audio = AudioLoader().load_wav("track.wav")
        metering = StandardsMetering()
        metrics = metering.compute_overall_metrics(audio)
        print(f"LUFS: {metrics.integrated_lufs}")
    """

    def compute_overall_metrics(self, audio: AudioData) -> OverallMetrics:
        """Compute Integrated LUFS, LRA, and True Peak for *audio*.

        Args:
            audio: Loaded audio data.  When ``stereo_samples`` is present
                the original stereo frames are used for all metering so
                that true-peak and LUFS reflect the full multichannel
                signal.

        Returns:
            An ``OverallMetrics`` ORM instance (without ``analysis_id``)
            populated with loudness values.
        """
        # Prefer untouched stereo frames when available so that true-peak
        # and LUFS measurements are not degraded by mono downmixing.
        if audio.stereo_samples is not None:
            samples = audio.stereo_samples
        else:
            samples = audio.samples
        rate = audio.sample_rate

        # --- pyloudnorm: Integrated LUFS (primary) -----------------------
        lufs_primary = self._compute_lufs_pyloudnorm(samples, rate)

        # --- pyloudnorm: Loudness Range (LRA) ----------------------------
        lra = self._compute_lra_pyloudnorm(samples, rate)

        # --- True Peak (per-channel, ITU-R BS.1770-4) ---------------------
        true_peak_dbfs = self._compute_true_peak(samples, rate)

        # --- Cross-validation (pyebur128 if available) --------------------
        lufs_check = self._compute_lufs_cross_check(samples, rate)
        self._cross_validate_lufs(lufs_primary, lufs_check)

        # Handle silence / -inf values
        integrated_lufs: float | None = None
        if lufs_primary is not None and math.isfinite(lufs_primary):
            integrated_lufs = round(lufs_primary, 2)

        loudness_range_lu: float | None = None
        if lra is not None and math.isfinite(lra):
            loudness_range_lu = round(lra, 2)

        true_peak_rounded: float | None = None
        if true_peak_dbfs is not None and math.isfinite(true_peak_dbfs):
            true_peak_rounded = round(true_peak_dbfs, 2)

        logger.info(
            "Overall metrics – LUFS: %s, LRA: %s LU, True Peak: %s dBFS",
            integrated_lufs,
            loudness_range_lu,
            true_peak_rounded,
        )

        return OverallMetrics(
            integrated_lufs=integrated_lufs,
            loudness_range_lu=loudness_range_lu,
            true_peak_dbfs=true_peak_rounded,
        )

    # ------------------------------------------------------------------
    # pyloudnorm helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_lufs_pyloudnorm(
        samples: np.ndarray, rate: int
    ) -> float | None:
        """Compute integrated loudness in LUFS using pyloudnorm.

        *samples* may be 1-D (mono) or 2-D ``(num_samples, channels)``
        (stereo / multichannel).  pyloudnorm handles both shapes
        natively.

        Returns ``None`` when the signal is too quiet for a valid
        measurement (pyloudnorm returns ``-inf``).
        """
        meter = pyln.Meter(rate)
        data = samples.astype(np.float64) if samples.dtype != np.float64 else samples
        lufs = meter.integrated_loudness(data)
        if not math.isfinite(lufs):
            logger.debug("pyloudnorm returned non-finite LUFS (silence?): %s", lufs)
            return None
        return float(lufs)

    @staticmethod
    def _compute_lra_pyloudnorm(
        samples: np.ndarray, rate: int
    ) -> float | None:
        """Compute Loudness Range (LRA) in LU using pyloudnorm.

        *samples* may be 1-D (mono) or 2-D ``(num_samples, channels)``.

        Returns ``None`` when the measurement is undefined (e.g. silence).
        """
        meter = pyln.Meter(rate)
        data = samples.astype(np.float64) if samples.dtype != np.float64 else samples
        try:
            lra = meter.loudness_range(data)
        except Exception:
            logger.debug("pyloudnorm loudness_range() failed", exc_info=True)
            return None
        if not math.isfinite(lra):
            return None
        return float(lra)

    # ------------------------------------------------------------------
    # True Peak (ITU-R BS.1770-4)
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_true_peak(
        samples: np.ndarray, rate: int
    ) -> float | None:
        """Compute True Peak in dBFS per ITU-R BS.1770-4.

        *samples* may be 1-D (mono) or 2-D ``(num_samples, channels)``.
        All channels are evaluated and the maximum true peak across
        channels is returned.

        Uses pyebur128 (libebur128) when available for per-channel true
        peak measurement.  Falls back to 4x oversampled peak detection
        when pyebur128 is absent.

        Returns:
            True Peak in dBFS, or ``_TRUE_PEAK_FLOOR_DBFS`` for silence.
        """
        if _HAS_PYEBUR128:
            result = StandardsMetering._compute_true_peak_pyebur128(
                samples, rate
            )
            if result is not None:
                return result
            logger.debug(
                "pyebur128 true peak failed, falling back to oversample"
            )

        return StandardsMetering._compute_true_peak_oversample(samples, rate)

    @staticmethod
    def _compute_true_peak_pyebur128(
        samples: np.ndarray, rate: int
    ) -> float | None:
        """Compute True Peak in dBFS using pyebur128 (libebur128 bindings).

        *samples* may be 1-D (mono) or 2-D ``(num_samples, channels)``.
        The pyebur128 ``State`` is configured with the actual channel
        count so that inter-sample peaks on every channel are evaluated.
        Per BS.1770-4, returns the maximum true peak across all channels.
        """
        if not _HAS_PYEBUR128:
            return None
        try:
            data = (
                samples.astype(np.float64)
                if samples.dtype != np.float64
                else samples
            )
            channels = 1 if data.ndim == 1 else data.shape[1]
            mode = pyebur128.Mode.TRUE_PEAK
            state = pyebur128.State(
                channels=channels, samplerate=rate, mode=mode
            )
            state.add_frames(data)

            # Per-channel max true peak
            peak_linear = max(
                state.true_peak(ch) for ch in range(channels)
            )

            if peak_linear <= 0.0:
                return _TRUE_PEAK_FLOOR_DBFS

            return 20.0 * math.log10(peak_linear)
        except Exception:
            logger.debug(
                "pyebur128 true peak computation failed", exc_info=True
            )
            return None

    @staticmethod
    def _compute_true_peak_oversample(
        samples: np.ndarray, rate: int
    ) -> float | None:
        """Compute True Peak in dBFS using 4x oversampled peak detection.

        Fallback method when pyebur128 is unavailable.  Per ITU-R BS.1770-4,
        each channel is oversampled by a factor of 4 using a low-pass
        interpolation filter.  The maximum absolute sample value across all
        channels of the oversampled signal is converted to dBFS.

        *samples* may be 1-D (mono) or 2-D ``(num_samples, channels)``.

        Returns:
            True Peak in dBFS, or ``_TRUE_PEAK_FLOOR_DBFS`` for silence.
        """
        data = samples.astype(np.float64) if samples.dtype != np.float64 else samples

        if data.size == 0:
            return _TRUE_PEAK_FLOOR_DBFS

        # Build a list of per-channel 1-D arrays to oversample independently
        if data.ndim == 1:
            channel_list = [data]
        else:
            channel_list = [data[:, ch] for ch in range(data.shape[1])]

        # 4x upsample each channel and take the maximum across all channels
        peak_linear = 0.0
        for ch_data in channel_list:
            oversampled = resample_poly(ch_data, up=_TRUE_PEAK_OVERSAMPLE, down=1)
            ch_peak = float(np.max(np.abs(oversampled)))
            peak_linear = max(peak_linear, ch_peak)

        if peak_linear <= 0.0:
            return _TRUE_PEAK_FLOOR_DBFS

        true_peak_db = 20.0 * math.log10(peak_linear)
        return true_peak_db

    # ------------------------------------------------------------------
    # Cross-validation
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_lufs_cross_check(
        samples: np.ndarray, rate: int
    ) -> float | None:
        """Compute LUFS for cross-validation.

        *samples* may be 1-D (mono) or 2-D ``(num_samples, channels)``.
        Uses pyebur128 when available, otherwise falls back to a second
        pyloudnorm computation (which will inherently match).
        """
        if _HAS_PYEBUR128:
            return StandardsMetering._compute_lufs_pyebur128(samples, rate)

        # Fallback: re-compute with pyloudnorm (same engine → diff ≈ 0)
        logger.debug(
            "Cross-validation fallback: using pyloudnorm (pyebur128 unavailable)"
        )
        return StandardsMetering._compute_lufs_pyloudnorm(samples, rate)

    @staticmethod
    def _compute_lufs_pyebur128(
        samples: np.ndarray, rate: int
    ) -> float | None:
        """Compute integrated LUFS using pyebur128 (libebur128 bindings).

        *samples* may be 1-D (mono) or 2-D ``(num_samples, channels)``.
        The ``State`` is configured with the actual channel count so that
        multichannel loudness is computed per BS.1770-4.
        """
        if not _HAS_PYEBUR128:
            return None
        try:
            data = samples.astype(np.float64) if samples.dtype != np.float64 else samples
            channels = 1 if data.ndim == 1 else data.shape[1]
            mode = (
                pyebur128.Mode.I
                | pyebur128.Mode.LRA
                | pyebur128.Mode.TRUE_PEAK
            )
            state = pyebur128.State(
                channels=channels, samplerate=rate, mode=mode
            )
            state.add_frames(data)
            raw_lufs = state.loudness_global()
            if math.isfinite(raw_lufs):
                return float(raw_lufs)
        except Exception:
            logger.debug("pyebur128 LUFS computation failed", exc_info=True)
        return None

    @staticmethod
    def _cross_validate_lufs(
        lufs_primary: float | None,
        lufs_check: float | None,
    ) -> None:
        """Compare primary and cross-check LUFS, warn on divergence.

        Logs a warning when the absolute difference exceeds
        ``CROSS_VALIDATION_THRESHOLD_LU`` (0.1 LU).
        """
        engine = "pyebur128" if _HAS_PYEBUR128 else "pyloudnorm-recheck"

        if lufs_primary is None or lufs_check is None:
            logger.info(
                "LUFS cross-validation skipped (one or both values undefined): "
                "pyloudnorm=%s, %s=%s",
                lufs_primary,
                engine,
                lufs_check,
            )
            return

        diff = abs(lufs_primary - lufs_check)
        logger.info(
            "LUFS cross-validation – pyloudnorm: %.2f, %s: %.2f, "
            "diff: %.3f LU",
            lufs_primary,
            engine,
            lufs_check,
            diff,
        )

        if diff > CROSS_VALIDATION_THRESHOLD_LU:
            logger.warning(
                "LUFS cross-validation WARNING: difference %.3f LU exceeds "
                "threshold %.1f LU (pyloudnorm=%.2f, %s=%.2f)",
                diff,
                CROSS_VALIDATION_THRESHOLD_LU,
                lufs_primary,
                engine,
                lufs_check,
            )
