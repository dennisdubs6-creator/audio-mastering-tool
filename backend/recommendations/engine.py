"""
Rule-based recommendation engine for audio mastering comparison.

Generates per-band and overall recommendations by comparing user analysis
metrics against either a reference track or genre-specific target values.
"""

import logging
from typing import Optional

from api.models import (
    BandMetrics,
    OverallMetrics,
    ReferenceBandMetrics,
    ReferenceOverallMetrics,
    Recommendation,
)
from recommendations.rules import (
    BANDS,
    BAND_FREQ_RANGES,
    GENRE_RULES,
    SEVERITY_THRESHOLDS,
)
from recommendations.templates import (
    generate_analytical_text,
    generate_suggestive_text,
    generate_prescriptive_text,
    generate_overall_analytical_text,
    generate_overall_suggestive_text,
    generate_overall_prescriptive_text,
)

logger = logging.getLogger(__name__)

_VALID_RECOMMENDATION_LEVELS = {"analytical", "suggestive", "prescriptive"}
_DEFAULT_RECOMMENDATION_LEVEL = "suggestive"


class RecommendationEngine:
    """Generates mastering recommendations based on metric comparisons.

    Supports two modes:
    - Reference comparison: computes deltas against a specific reference track.
    - Genre rules: computes deltas against genre-specific target values.
    """

    def __init__(self) -> None:
        self._genre_rules = GENRE_RULES

    @staticmethod
    def _classify_severity(delta: float) -> str:
        """Classify severity based on the absolute magnitude of a delta.

        Args:
            delta: The difference between user and reference/target values.

        Returns:
            One of 'info', 'attention', or 'issue'.
        """
        abs_delta = abs(delta)
        if abs_delta >= SEVERITY_THRESHOLDS["issue"]:
            return "issue"
        if abs_delta >= SEVERITY_THRESHOLDS["attention"]:
            return "attention"
        return "info"

    @staticmethod
    def _band_freq_range(band_name: str) -> str:
        """Return a human-readable frequency range string."""
        return BAND_FREQ_RANGES.get(band_name, band_name)

    def generate(
        self,
        user_band_metrics: list,
        user_overall_metrics,
        reference_band_metrics: Optional[list] = None,
        reference_overall_metrics=None,
        genre: Optional[str] = None,
        recommendation_level: str = _DEFAULT_RECOMMENDATION_LEVEL,
    ) -> list[dict]:
        """Generate recommendations comparing user metrics against a reference or genre targets.

        Args:
            user_band_metrics: List of user BandMetrics ORM objects.
            user_overall_metrics: User OverallMetrics ORM object.
            reference_band_metrics: Optional list of ReferenceBandMetrics ORM objects.
            reference_overall_metrics: Optional ReferenceOverallMetrics ORM object.
            genre: Optional genre string for genre-rule-based recommendations.
            recommendation_level: Active recommendation text level.

        Returns:
            List of recommendation dicts with keys matching the Recommendation model fields.
        """
        normalized_level = self._normalize_recommendation_level(recommendation_level)

        if reference_band_metrics is not None:
            recommendations = self._compare_with_reference(
                user_band_metrics,
                user_overall_metrics,
                reference_band_metrics,
                reference_overall_metrics,
            )
        else:
            recommendations = self._apply_genre_rules(
                user_band_metrics,
                user_overall_metrics,
                genre,
            )

        return self._set_active_recommendation_text(recommendations, normalized_level)

    @staticmethod
    def _normalize_recommendation_level(level: Optional[str]) -> str:
        """Normalize recommendation level to a supported value."""
        if level is None:
            return _DEFAULT_RECOMMENDATION_LEVEL

        normalized = level.strip().lower()
        if normalized in _VALID_RECOMMENDATION_LEVELS:
            return normalized
        return _DEFAULT_RECOMMENDATION_LEVEL

    @staticmethod
    def _set_active_recommendation_text(
        recommendations: list[dict],
        recommendation_level: str,
    ) -> list[dict]:
        """Set recommendation_text to the active verbosity level text."""
        text_key = f"{recommendation_level}_text"
        for recommendation in recommendations:
            recommendation["recommendation_text"] = recommendation.get(text_key)
        return recommendations

    def _compare_with_reference(
        self,
        user_bands: list,
        user_overall,
        ref_bands: list,
        ref_overall,
    ) -> list[dict]:
        """Generate delta-based recommendations from a reference track comparison."""
        recommendations = []

        # Build lookup by band_name for reference
        ref_band_map = {b.band_name: b for b in ref_bands}

        for user_band in user_bands:
            band_name = user_band.band_name
            ref_band = ref_band_map.get(band_name)
            if ref_band is None:
                continue

            # RMS level comparison
            if user_band.band_rms_dbfs is not None and ref_band.band_rms_dbfs is not None:
                delta = user_band.band_rms_dbfs - ref_band.band_rms_dbfs
                if abs(delta) >= SEVERITY_THRESHOLDS["attention"]:
                    recommendations.append(self._build_recommendation(
                        band_name=band_name,
                        metric_category="loudness",
                        delta=delta,
                    ))

            # Energy comparison
            if user_band.energy_db is not None and ref_band.energy_db is not None:
                delta = user_band.energy_db - ref_band.energy_db
                if abs(delta) >= SEVERITY_THRESHOLDS["attention"]:
                    recommendations.append(self._build_recommendation(
                        band_name=band_name,
                        metric_category="frequency",
                        delta=delta,
                    ))

            # Dynamic range comparison
            if user_band.dynamic_range_db is not None and ref_band.dynamic_range_db is not None:
                delta = user_band.dynamic_range_db - ref_band.dynamic_range_db
                if abs(delta) >= SEVERITY_THRESHOLDS["attention"]:
                    recommendations.append(self._build_recommendation(
                        band_name=band_name,
                        metric_category="dynamic_range",
                        delta=delta,
                    ))

            # Stereo width comparison
            if user_band.stereo_width_percent is not None and ref_band.stereo_width_percent is not None:
                delta = user_band.stereo_width_percent - ref_band.stereo_width_percent
                if abs(delta) >= SEVERITY_THRESHOLDS["attention"]:
                    recommendations.append(self._build_recommendation(
                        band_name=band_name,
                        metric_category="stereo_width",
                        delta=delta,
                    ))

        # Overall metric comparisons
        if user_overall and ref_overall:
            overall_comparisons = [
                ("integrated_lufs", "Integrated loudness", "LUFS"),
                ("dynamic_range_db", "Dynamic range", "dB"),
                ("true_peak_dbfs", "True peak", "dBFS"),
                ("avg_stereo_width_percent", "Stereo width", "%"),
            ]
            for attr, name, unit in overall_comparisons:
                user_val = getattr(user_overall, attr, None)
                ref_val = getattr(ref_overall, attr, None)
                if user_val is not None and ref_val is not None:
                    delta = user_val - ref_val
                    if abs(delta) >= SEVERITY_THRESHOLDS["attention"]:
                        severity = self._classify_severity(delta)
                        recommendations.append({
                            "band_name": None,
                            "metric_category": attr,
                            "severity": severity,
                            "recommendation_text": generate_overall_suggestive_text(name, user_val, ref_val, unit),
                            "analytical_text": generate_overall_analytical_text(name, user_val, ref_val, unit),
                            "suggestive_text": generate_overall_suggestive_text(name, user_val, ref_val, unit),
                            "prescriptive_text": generate_overall_prescriptive_text(name, user_val, ref_val, unit),
                        })

        return recommendations

    def _apply_genre_rules(
        self,
        user_bands: list,
        user_overall,
        genre: Optional[str],
    ) -> list[dict]:
        """Generate recommendations based on genre-specific target values."""
        if not genre or genre not in self._genre_rules:
            return []

        rules = self._genre_rules[genre]
        recommendations = []

        for user_band in user_bands:
            band_name = user_band.band_name

            # Check band RMS against genre targets
            if user_band.band_rms_dbfs is not None and band_name in rules.get("band_rms_dbfs", {}):
                target = rules["band_rms_dbfs"][band_name]
                delta = user_band.band_rms_dbfs - target
                if abs(delta) >= SEVERITY_THRESHOLDS["attention"]:
                    recommendations.append(self._build_recommendation(
                        band_name=band_name,
                        metric_category="loudness",
                        delta=delta,
                    ))

            # Check band energy against genre targets
            if user_band.energy_db is not None and band_name in rules.get("band_energy_db", {}):
                target = rules["band_energy_db"][band_name]
                delta = user_band.energy_db - target
                if abs(delta) >= SEVERITY_THRESHOLDS["attention"]:
                    recommendations.append(self._build_recommendation(
                        band_name=band_name,
                        metric_category="frequency",
                        delta=delta,
                    ))

            # Check dynamic range against genre targets
            if user_band.dynamic_range_db is not None and band_name in rules.get("band_dynamic_range_db", {}):
                target = rules["band_dynamic_range_db"][band_name]
                delta = user_band.dynamic_range_db - target
                if abs(delta) >= SEVERITY_THRESHOLDS["attention"]:
                    recommendations.append(self._build_recommendation(
                        band_name=band_name,
                        metric_category="dynamic_range",
                        delta=delta,
                    ))

            # Check stereo width against genre targets
            if user_band.stereo_width_percent is not None and band_name in rules.get("band_stereo_width_percent", {}):
                target = rules["band_stereo_width_percent"][band_name]
                delta = user_band.stereo_width_percent - target
                if abs(delta) >= SEVERITY_THRESHOLDS["attention"]:
                    recommendations.append(self._build_recommendation(
                        band_name=band_name,
                        metric_category="stereo_width",
                        delta=delta,
                    ))

        # Check overall metrics against genre targets
        if user_overall and "overall" in rules:
            overall_rules = rules["overall"]
            metric_display = {
                "integrated_lufs": ("Integrated loudness", "LUFS"),
                "dynamic_range_db": ("Dynamic range", "dB"),
                "true_peak_dbfs": ("True peak", "dBFS"),
                "avg_stereo_width_percent": ("Stereo width", "%"),
                "loudness_range_lu": ("Loudness range", "LU"),
                "crest_factor_db": ("Crest factor", "dB"),
                "avg_phase_correlation": ("Phase correlation", ""),
            }
            for attr, rule in overall_rules.items():
                user_val = getattr(user_overall, attr, None)
                if user_val is not None:
                    target = rule["target"]
                    delta = user_val - target
                    if abs(delta) >= rule.get("tolerance", SEVERITY_THRESHOLDS["attention"]):
                        severity = self._classify_severity(delta)
                        name, unit = metric_display.get(attr, (attr, ""))
                        recommendations.append({
                            "band_name": None,
                            "metric_category": attr,
                            "severity": severity,
                            "recommendation_text": generate_overall_suggestive_text(name, user_val, target, unit),
                            "analytical_text": generate_overall_analytical_text(name, user_val, target, unit),
                            "suggestive_text": generate_overall_suggestive_text(name, user_val, target, unit),
                            "prescriptive_text": generate_overall_prescriptive_text(name, user_val, target, unit),
                        })

        return recommendations

    def _build_recommendation(
        self,
        band_name: str,
        metric_category: str,
        delta: float,
    ) -> dict:
        """Build a recommendation dict with all three text levels."""
        severity = self._classify_severity(delta)
        return {
            "band_name": band_name,
            "metric_category": metric_category,
            "severity": severity,
            "recommendation_text": generate_suggestive_text(band_name, metric_category, delta),
            "analytical_text": generate_analytical_text(band_name, metric_category, delta),
            "suggestive_text": generate_suggestive_text(band_name, metric_category, delta),
            "prescriptive_text": generate_prescriptive_text(band_name, metric_category, delta),
        }
