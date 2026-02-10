"""
Genre-specific rules for the recommendation engine.

Defines target metric values, tolerances, and severity thresholds
for each supported electronic music genre, derived from the genre
profiles in ``scripts/populate_references.py``.
"""

BANDS = ["low", "low_mid", "mid", "high_mid", "high"]

BAND_FREQ_RANGES = {
    "low": "20-200 Hz",
    "low_mid": "200-500 Hz",
    "mid": "500-2000 Hz",
    "high_mid": "2-6 kHz",
    "high": "6-20 kHz",
}

# Severity thresholds (in dB for level metrics, absolute for others)
SEVERITY_THRESHOLDS = {
    "issue": 4.0,
    "attention": 2.0,
}

GENRE_RULES = {
    "Psytrance": {
        "overall": {
            "integrated_lufs": {"target": -7.0, "tolerance": 1.0, "min": -10.0, "max": -5.0},
            "loudness_range_lu": {"target": 5.5, "tolerance": 1.0, "min": 3.5, "max": 7.5},
            "true_peak_dbfs": {"target": -0.5, "tolerance": 0.3, "min": -1.5, "max": 0.0},
            "dynamic_range_db": {"target": 7.0, "tolerance": 1.0, "min": 5.0, "max": 9.0},
            "crest_factor_db": {"target": 8.0, "tolerance": 1.5, "min": 5.0, "max": 11.0},
            "avg_stereo_width_percent": {"target": 80.0, "tolerance": 10.0, "min": 60.0, "max": 95.0},
            "avg_phase_correlation": {"target": 0.75, "tolerance": 0.1, "min": 0.5, "max": 1.0},
        },
        "band_rms_dbfs": {
            "low": -20.0, "low_mid": -24.0, "mid": -22.0, "high_mid": -26.0, "high": -32.0,
        },
        "band_energy_db": {
            "low": -18.0, "low_mid": -22.0, "mid": -20.0, "high_mid": -24.0, "high": -30.0,
        },
        "band_dynamic_range_db": {
            "low": 6.0, "low_mid": 7.0, "mid": 8.0, "high_mid": 7.5, "high": 6.5,
        },
        "band_stereo_width_percent": {
            "low": 40.0, "low_mid": 60.0, "mid": 80.0, "high_mid": 90.0, "high": 85.0,
        },
    },
    "Trance": {
        "overall": {
            "integrated_lufs": {"target": -7.5, "tolerance": 1.0, "min": -10.5, "max": -5.5},
            "loudness_range_lu": {"target": 6.0, "tolerance": 1.0, "min": 4.0, "max": 8.0},
            "true_peak_dbfs": {"target": -0.8, "tolerance": 0.3, "min": -1.5, "max": 0.0},
            "dynamic_range_db": {"target": 7.5, "tolerance": 1.0, "min": 5.5, "max": 9.5},
            "crest_factor_db": {"target": 8.5, "tolerance": 1.5, "min": 5.5, "max": 11.5},
            "avg_stereo_width_percent": {"target": 82.0, "tolerance": 8.0, "min": 60.0, "max": 95.0},
            "avg_phase_correlation": {"target": 0.78, "tolerance": 0.08, "min": 0.5, "max": 1.0},
        },
        "band_rms_dbfs": {
            "low": -21.0, "low_mid": -25.0, "mid": -21.0, "high_mid": -24.0, "high": -30.0,
        },
        "band_energy_db": {
            "low": -19.0, "low_mid": -23.0, "mid": -19.0, "high_mid": -22.0, "high": -28.0,
        },
        "band_dynamic_range_db": {
            "low": 6.5, "low_mid": 7.5, "mid": 8.5, "high_mid": 8.0, "high": 7.0,
        },
        "band_stereo_width_percent": {
            "low": 35.0, "low_mid": 55.0, "mid": 82.0, "high_mid": 92.0, "high": 88.0,
        },
    },
    "Techno": {
        "overall": {
            "integrated_lufs": {"target": -5.0, "tolerance": 1.0, "min": -8.0, "max": -3.0},
            "loudness_range_lu": {"target": 4.0, "tolerance": 0.8, "min": 2.5, "max": 5.5},
            "true_peak_dbfs": {"target": -0.3, "tolerance": 0.2, "min": -1.0, "max": 0.0},
            "dynamic_range_db": {"target": 6.0, "tolerance": 1.0, "min": 4.0, "max": 8.0},
            "crest_factor_db": {"target": 6.5, "tolerance": 1.0, "min": 4.5, "max": 8.5},
            "avg_stereo_width_percent": {"target": 88.0, "tolerance": 7.0, "min": 65.0, "max": 98.0},
            "avg_phase_correlation": {"target": 0.80, "tolerance": 0.08, "min": 0.5, "max": 1.0},
        },
        "band_rms_dbfs": {
            "low": -17.0, "low_mid": -22.0, "mid": -20.0, "high_mid": -24.0, "high": -30.0,
        },
        "band_energy_db": {
            "low": -15.0, "low_mid": -20.0, "mid": -18.0, "high_mid": -22.0, "high": -28.0,
        },
        "band_dynamic_range_db": {
            "low": 5.0, "low_mid": 6.0, "mid": 6.5, "high_mid": 6.0, "high": 5.5,
        },
        "band_stereo_width_percent": {
            "low": 30.0, "low_mid": 65.0, "mid": 88.0, "high_mid": 95.0, "high": 90.0,
        },
    },
    "House": {
        "overall": {
            "integrated_lufs": {"target": -6.0, "tolerance": 1.0, "min": -9.0, "max": -4.0},
            "loudness_range_lu": {"target": 5.0, "tolerance": 1.0, "min": 3.0, "max": 7.0},
            "true_peak_dbfs": {"target": -0.5, "tolerance": 0.3, "min": -1.5, "max": 0.0},
            "dynamic_range_db": {"target": 7.5, "tolerance": 1.5, "min": 4.5, "max": 10.5},
            "crest_factor_db": {"target": 8.0, "tolerance": 1.5, "min": 5.0, "max": 11.0},
            "avg_stereo_width_percent": {"target": 82.0, "tolerance": 8.0, "min": 60.0, "max": 95.0},
            "avg_phase_correlation": {"target": 0.82, "tolerance": 0.08, "min": 0.5, "max": 1.0},
        },
        "band_rms_dbfs": {
            "low": -19.0, "low_mid": -23.0, "mid": -21.0, "high_mid": -25.0, "high": -31.0,
        },
        "band_energy_db": {
            "low": -17.0, "low_mid": -21.0, "mid": -19.0, "high_mid": -23.0, "high": -29.0,
        },
        "band_dynamic_range_db": {
            "low": 6.5, "low_mid": 7.5, "mid": 8.0, "high_mid": 7.5, "high": 7.0,
        },
        "band_stereo_width_percent": {
            "low": 35.0, "low_mid": 58.0, "mid": 82.0, "high_mid": 90.0, "high": 85.0,
        },
    },
    "Drum & Bass": {
        "overall": {
            "integrated_lufs": {"target": -4.0, "tolerance": 1.0, "min": -7.0, "max": -2.0},
            "loudness_range_lu": {"target": 4.5, "tolerance": 0.8, "min": 3.0, "max": 6.0},
            "true_peak_dbfs": {"target": -0.2, "tolerance": 0.2, "min": -1.0, "max": 0.0},
            "dynamic_range_db": {"target": 5.0, "tolerance": 1.0, "min": 3.0, "max": 7.0},
            "crest_factor_db": {"target": 5.5, "tolerance": 1.0, "min": 3.5, "max": 7.5},
            "avg_stereo_width_percent": {"target": 90.0, "tolerance": 5.0, "min": 70.0, "max": 98.0},
            "avg_phase_correlation": {"target": 0.78, "tolerance": 0.08, "min": 0.5, "max": 1.0},
        },
        "band_rms_dbfs": {
            "low": -16.0, "low_mid": -22.0, "mid": -20.0, "high_mid": -22.0, "high": -26.0,
        },
        "band_energy_db": {
            "low": -14.0, "low_mid": -20.0, "mid": -18.0, "high_mid": -20.0, "high": -24.0,
        },
        "band_dynamic_range_db": {
            "low": 4.5, "low_mid": 5.0, "mid": 5.5, "high_mid": 5.0, "high": 4.5,
        },
        "band_stereo_width_percent": {
            "low": 30.0, "low_mid": 70.0, "mid": 90.0, "high_mid": 95.0, "high": 92.0,
        },
    },
    "Dubstep": {
        "overall": {
            "integrated_lufs": {"target": -3.0, "tolerance": 1.0, "min": -6.0, "max": -1.0},
            "loudness_range_lu": {"target": 4.0, "tolerance": 0.8, "min": 2.5, "max": 5.5},
            "true_peak_dbfs": {"target": -0.1, "tolerance": 0.1, "min": -0.5, "max": 0.0},
            "dynamic_range_db": {"target": 4.0, "tolerance": 1.0, "min": 2.0, "max": 6.0},
            "crest_factor_db": {"target": 4.5, "tolerance": 1.0, "min": 2.5, "max": 6.5},
            "avg_stereo_width_percent": {"target": 88.0, "tolerance": 7.0, "min": 65.0, "max": 98.0},
            "avg_phase_correlation": {"target": 0.72, "tolerance": 0.10, "min": 0.4, "max": 1.0},
        },
        "band_rms_dbfs": {
            "low": -14.0, "low_mid": -18.0, "mid": -17.0, "high_mid": -22.0, "high": -28.0,
        },
        "band_energy_db": {
            "low": -12.0, "low_mid": -16.0, "mid": -15.0, "high_mid": -20.0, "high": -26.0,
        },
        "band_dynamic_range_db": {
            "low": 3.5, "low_mid": 4.0, "mid": 4.5, "high_mid": 4.0, "high": 3.5,
        },
        "band_stereo_width_percent": {
            "low": 35.0, "low_mid": 75.0, "mid": 88.0, "high_mid": 92.0, "high": 88.0,
        },
    },
}
