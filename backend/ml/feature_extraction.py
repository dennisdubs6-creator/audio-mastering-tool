"""
Feature extraction from audio analysis metrics.

Extracts a 128-dimensional feature vector from per-band and overall metrics
for use in cosine similarity matching against reference tracks.

Feature Vector Composition (128 dimensions):
    - Spectral features (40 dims): Per-band centroid, rolloff, flatness, energy
      (5 bands x 4 = 20) plus mean/std aggregates (20 dims)
    - Dynamics features (20 dims): Overall LUFS, LRA, true peak, DR, crest factor
      (5 dims) plus per-band DR, crest factor, RMS mean/std (15 dims)
    - Energy distribution (5 dims): Normalized energy per band
    - Stereo features (10 dims): Overall width, phase correlation (2 dims)
      plus per-band width, phase correlation mean/std (8 dims)
    - Harmonic/Transient features (8 dims): Per-band THD, harmonic ratio,
      transient preservation, attack time mean/std
    - Padding (45 dims): Reserved for future features
"""

from typing import List, Optional, Sequence, Union

import numpy as np


# Band ordering used throughout feature extraction
BAND_ORDER = ["low", "low_mid", "mid", "high_mid", "high"]


class FeatureExtractor:
    """Extracts fixed-size feature vectors from audio analysis metrics.

    The feature vector is 128-dimensional, L2-normalized, and designed for
    cosine similarity comparison between user analyses and reference tracks.
    """

    VECTOR_DIM = 128

    def extract_from_metrics(
        self,
        band_metrics: Sequence,
        overall_metrics,
    ) -> np.ndarray:
        """Extract a 128-dimensional feature vector from analysis metrics.

        Args:
            band_metrics: List of BandMetrics (or ReferenceBandMetrics) ORM
                instances, one per frequency band.
            overall_metrics: An OverallMetrics (or ReferenceOverallMetrics)
                ORM instance with aggregate metrics.

        Returns:
            L2-normalized numpy array of shape (128,) with dtype float32.
        """
        # Index band metrics by name for ordered access
        band_map = {bm.band_name: bm for bm in band_metrics}

        features: List[float] = []

        # --- Spectral features (40 dims) ---
        spectral_features = self._extract_spectral(band_map)
        features.extend(spectral_features)

        # --- Dynamics features (20 dims) ---
        dynamics_features = self._extract_dynamics(band_map, overall_metrics)
        features.extend(dynamics_features)

        # --- Energy distribution (5 dims) ---
        energy_features = self._extract_energy_distribution(band_map)
        features.extend(energy_features)

        # --- Stereo features (10 dims) ---
        stereo_features = self._extract_stereo(band_map, overall_metrics)
        features.extend(stereo_features)

        # --- Harmonic/Transient features (8 dims) ---
        harmonic_features = self._extract_harmonic_transient(band_map)
        features.extend(harmonic_features)

        # --- Padding to reach 128 dims ---
        current_len = len(features)
        if current_len < self.VECTOR_DIM:
            features.extend([0.0] * (self.VECTOR_DIM - current_len))

        vec = np.array(features[: self.VECTOR_DIM], dtype=np.float32)

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec

    # ------------------------------------------------------------------
    # Internal extraction helpers
    # ------------------------------------------------------------------

    def _extract_spectral(self, band_map: dict) -> List[float]:
        """Extract spectral features: 5 bands x 4 metrics + mean/std = 40 dims."""
        per_band_centroid = []
        per_band_rolloff = []
        per_band_flatness = []
        per_band_energy = []

        features = []
        for band_name in BAND_ORDER:
            bm = band_map.get(band_name)
            centroid = _safe(bm, "spectral_centroid_hz")
            rolloff = _safe(bm, "spectral_rolloff_hz")
            flatness = _safe(bm, "spectral_flatness")
            energy = _safe(bm, "energy_db")

            features.extend([centroid, rolloff, flatness, energy])
            per_band_centroid.append(centroid)
            per_band_rolloff.append(rolloff)
            per_band_flatness.append(flatness)
            per_band_energy.append(energy)

        # Mean and std aggregates (4 metrics x 2 stats = 8, but we need 20 more)
        # We add mean, std, min, max, range for each of the 4 spectral metrics
        for values in [per_band_centroid, per_band_rolloff, per_band_flatness, per_band_energy]:
            arr = np.array(values, dtype=np.float32)
            features.append(float(np.mean(arr)))
            features.append(float(np.std(arr)))
            features.append(float(np.min(arr)))
            features.append(float(np.max(arr)))
            features.append(float(np.max(arr) - np.min(arr)))

        return features  # 20 + 20 = 40

    def _extract_dynamics(self, band_map: dict, overall_metrics) -> List[float]:
        """Extract dynamics features: 5 overall + 15 per-band stats = 20 dims."""
        features = []

        # Overall dynamics (5 dims)
        features.append(_safe(overall_metrics, "integrated_lufs"))
        features.append(_safe(overall_metrics, "loudness_range_lu"))
        features.append(_safe(overall_metrics, "true_peak_dbfs"))
        features.append(_safe(overall_metrics, "dynamic_range_db"))
        features.append(_safe(overall_metrics, "crest_factor_db"))

        # Per-band dynamics stats (3 metrics x 5 stats = 15 dims)
        per_band_dr = []
        per_band_crest = []
        per_band_rms = []

        for band_name in BAND_ORDER:
            bm = band_map.get(band_name)
            per_band_dr.append(_safe(bm, "dynamic_range_db"))
            per_band_crest.append(_safe(bm, "crest_factor_db"))
            per_band_rms.append(_safe(bm, "rms_db"))

        for values in [per_band_dr, per_band_crest, per_band_rms]:
            arr = np.array(values, dtype=np.float32)
            features.append(float(np.mean(arr)))
            features.append(float(np.std(arr)))
            features.append(float(np.min(arr)))
            features.append(float(np.max(arr)))
            features.append(float(np.max(arr) - np.min(arr)))

        return features  # 5 + 15 = 20

    def _extract_energy_distribution(self, band_map: dict) -> List[float]:
        """Extract normalized energy distribution across bands: 5 dims."""
        energies = []
        for band_name in BAND_ORDER:
            bm = band_map.get(band_name)
            energies.append(_safe(bm, "energy_db"))

        # Convert from dB to linear for normalization
        linear = np.array([10 ** (e / 10.0) if e != 0.0 else 1e-10 for e in energies], dtype=np.float32)
        total = float(np.sum(linear))
        if total > 0:
            normalized = (linear / total).tolist()
        else:
            normalized = [0.2] * 5  # uniform fallback

        return normalized

    def _extract_stereo(self, band_map: dict, overall_metrics) -> List[float]:
        """Extract stereo features: 2 overall + 8 per-band stats = 10 dims."""
        features = []

        # Overall stereo (2 dims)
        features.append(_safe(overall_metrics, "avg_stereo_width_percent"))
        features.append(_safe(overall_metrics, "avg_phase_correlation"))

        # Per-band stereo stats (2 metrics x 4 stats = 8 dims)
        per_band_width = []
        per_band_phase = []

        for band_name in BAND_ORDER:
            bm = band_map.get(band_name)
            per_band_width.append(_safe(bm, "stereo_width_percent"))
            per_band_phase.append(_safe(bm, "phase_correlation"))

        for values in [per_band_width, per_band_phase]:
            arr = np.array(values, dtype=np.float32)
            features.append(float(np.mean(arr)))
            features.append(float(np.std(arr)))
            features.append(float(np.min(arr)))
            features.append(float(np.max(arr)))

        return features  # 2 + 8 = 10

    def _extract_harmonic_transient(self, band_map: dict) -> List[float]:
        """Extract harmonic/transient features: 4 metrics x 2 stats = 8 dims."""
        per_band_thd = []
        per_band_harmonic_ratio = []
        per_band_transient = []
        per_band_attack = []

        for band_name in BAND_ORDER:
            bm = band_map.get(band_name)
            per_band_thd.append(_safe(bm, "thd_percent"))
            per_band_harmonic_ratio.append(_safe(bm, "harmonic_ratio"))
            per_band_transient.append(_safe(bm, "transient_preservation"))
            per_band_attack.append(_safe(bm, "attack_time_ms"))

        features = []
        for values in [per_band_thd, per_band_harmonic_ratio, per_band_transient, per_band_attack]:
            arr = np.array(values, dtype=np.float32)
            features.append(float(np.mean(arr)))
            features.append(float(np.std(arr)))

        return features  # 8


def _safe(obj, attr: str, default: float = 0.0) -> float:
    """Safely extract a float attribute, replacing None with default."""
    if obj is None:
        return default
    val = getattr(obj, attr, None)
    if val is None:
        return default
    return float(val)
