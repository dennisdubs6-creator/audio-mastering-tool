"""
Audio Mastering Tool - Constants and Band Definitions

Defines the frequency bands, recommendation levels, and genre list used
throughout the application for audio analysis and mastering recommendations.
"""

FREQUENCY_BANDS: dict[str, tuple[int, int]] = {
    "low": (20, 200),
    "low_mid": (200, 500),
    "mid": (500, 2000),
    "high_mid": (2000, 6000),
    "high": (6000, 20000),
}
"""Frequency band definitions mapping band name to (min_hz, max_hz) range.

- low: Sub-bass and bass fundamentals (20-200 Hz)
- low_mid: Warmth and body region (200-500 Hz)
- mid: Presence and vocal clarity region (500-2000 Hz)
- high_mid: Brightness and detail region (2000-6000 Hz)
- high: Air and brilliance region (6000-20000 Hz)
"""

BAND_NAMES: list[str] = ["low", "low_mid", "mid", "high_mid", "high"]
"""Ordered list of frequency band names from lowest to highest."""

RECOMMENDATION_LEVELS: list[str] = ["analytical", "suggestive", "prescriptive"]
"""Available recommendation verbosity levels.

- analytical: Data-driven observations without specific suggestions.
- suggestive: Gentle recommendations with reasoning.
- prescriptive: Direct, actionable instructions for mastering adjustments.
"""

GENRE_LIST: list[str] = [
    "rock",
    "pop",
    "hip_hop",
    "electronic",
    "jazz",
    "classical",
    "r_and_b",
    "country",
    "metal",
    "folk",
    "blues",
    "reggae",
    "latin",
    "ambient",
    "indie",
    "punk",
    "soul",
    "funk",
    "world",
    "other",
]
"""Common audio genres supported by the analysis engine.

Used for genre-specific reference track matching and recommendation
calibration. The 'other' genre serves as a catch-all category.
"""
