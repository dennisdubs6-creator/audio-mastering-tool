"""
Populate the reference database with electronic music reference tracks.

Loads metadata from reference_metadata.json, generates synthetic metrics
based on genre characteristics, extracts feature vectors, and stores
everything in the database.

Usage:
    python -m scripts.populate_references
    python -m scripts.populate_references --force  # Delete existing built-ins first
"""

import argparse
import json
import logging
import random
import sys
from pathlib import Path

from api.database import SessionFactory, init_db
from api.models import (
    ReferenceBandMetrics,
    ReferenceOverallMetrics,
    ReferenceTrack,
)
from ml.feature_extraction import FeatureExtractor
from ml.similarity import serialize_vector

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

METADATA_PATH = Path(__file__).parent.parent / "data" / "references" / "reference_metadata.json"

BANDS = [
    ("low", 20, 200),
    ("low_mid", 200, 500),
    ("mid", 500, 2000),
    ("high_mid", 2000, 6000),
    ("high", 6000, 20000),
]

# Genre-specific metric profiles: (mean, variance_factor)
# Each profile defines typical ranges for key metrics per genre.
GENRE_PROFILES = {
    "Psytrance": {
        "integrated_lufs": (-7.0, 1.0),
        "loudness_range_lu": (5.5, 1.0),
        "true_peak_dbfs": (-0.5, 0.3),
        "dynamic_range_db": (7.0, 1.0),
        "crest_factor_db": (8.0, 1.5),
        "avg_stereo_width_percent": (80.0, 10.0),
        "avg_phase_correlation": (0.75, 0.1),
        "spectral_centroid_hz": (3500.0, 500.0),
        "spectral_bandwidth_hz": (4000.0, 500.0),
        "band_energy_profile": [-18.0, -22.0, -20.0, -24.0, -30.0],
        "band_spectral_centroid": [110.0, 350.0, 1200.0, 3800.0, 12000.0],
        "band_spectral_rolloff": [180.0, 480.0, 1800.0, 5500.0, 18000.0],
        "band_spectral_flatness": [0.15, 0.20, 0.25, 0.35, 0.45],
        "band_dynamic_range": [6.0, 7.0, 8.0, 7.5, 6.5],
        "band_crest_factor": [7.0, 8.0, 9.0, 8.5, 7.5],
        "band_rms": [-20.0, -24.0, -22.0, -26.0, -32.0],
        "band_stereo_width": [40.0, 60.0, 80.0, 90.0, 85.0],
        "band_phase_correlation": [0.95, 0.85, 0.75, 0.70, 0.65],
        "band_thd": [2.0, 1.5, 1.0, 0.8, 0.5],
        "band_harmonic_ratio": [0.7, 0.6, 0.5, 0.4, 0.3],
        "band_transient_preservation": [0.6, 0.65, 0.7, 0.75, 0.8],
        "band_attack_time": [15.0, 12.0, 8.0, 5.0, 3.0],
    },
    "Trance": {
        "integrated_lufs": (-7.5, 1.0),
        "loudness_range_lu": (6.0, 1.0),
        "true_peak_dbfs": (-0.8, 0.3),
        "dynamic_range_db": (7.5, 1.0),
        "crest_factor_db": (8.5, 1.5),
        "avg_stereo_width_percent": (82.0, 8.0),
        "avg_phase_correlation": (0.78, 0.08),
        "spectral_centroid_hz": (3200.0, 500.0),
        "spectral_bandwidth_hz": (3800.0, 500.0),
        "band_energy_profile": [-19.0, -23.0, -19.0, -22.0, -28.0],
        "band_spectral_centroid": [100.0, 340.0, 1100.0, 3600.0, 11500.0],
        "band_spectral_rolloff": [175.0, 470.0, 1750.0, 5200.0, 17500.0],
        "band_spectral_flatness": [0.12, 0.18, 0.22, 0.30, 0.40],
        "band_dynamic_range": [6.5, 7.5, 8.5, 8.0, 7.0],
        "band_crest_factor": [7.5, 8.5, 9.5, 9.0, 8.0],
        "band_rms": [-21.0, -25.0, -21.0, -24.0, -30.0],
        "band_stereo_width": [35.0, 55.0, 82.0, 92.0, 88.0],
        "band_phase_correlation": [0.96, 0.88, 0.78, 0.72, 0.68],
        "band_thd": [1.8, 1.2, 0.8, 0.6, 0.4],
        "band_harmonic_ratio": [0.75, 0.65, 0.55, 0.45, 0.35],
        "band_transient_preservation": [0.55, 0.60, 0.65, 0.72, 0.78],
        "band_attack_time": [18.0, 14.0, 10.0, 6.0, 4.0],
    },
    "Techno": {
        "integrated_lufs": (-5.0, 1.0),
        "loudness_range_lu": (4.0, 0.8),
        "true_peak_dbfs": (-0.3, 0.2),
        "dynamic_range_db": (6.0, 1.0),
        "crest_factor_db": (6.5, 1.0),
        "avg_stereo_width_percent": (88.0, 7.0),
        "avg_phase_correlation": (0.80, 0.08),
        "spectral_centroid_hz": (2800.0, 400.0),
        "spectral_bandwidth_hz": (3500.0, 400.0),
        "band_energy_profile": [-15.0, -20.0, -18.0, -22.0, -28.0],
        "band_spectral_centroid": [120.0, 360.0, 1150.0, 3500.0, 11000.0],
        "band_spectral_rolloff": [185.0, 485.0, 1850.0, 5600.0, 18500.0],
        "band_spectral_flatness": [0.18, 0.25, 0.30, 0.40, 0.50],
        "band_dynamic_range": [5.0, 6.0, 6.5, 6.0, 5.5],
        "band_crest_factor": [5.5, 6.5, 7.0, 6.5, 6.0],
        "band_rms": [-17.0, -22.0, -20.0, -24.0, -30.0],
        "band_stereo_width": [30.0, 65.0, 88.0, 95.0, 90.0],
        "band_phase_correlation": [0.97, 0.87, 0.80, 0.75, 0.70],
        "band_thd": [3.0, 2.0, 1.5, 1.0, 0.7],
        "band_harmonic_ratio": [0.65, 0.55, 0.45, 0.35, 0.25],
        "band_transient_preservation": [0.70, 0.72, 0.75, 0.78, 0.82],
        "band_attack_time": [10.0, 8.0, 6.0, 4.0, 2.5],
    },
    "House": {
        "integrated_lufs": (-6.0, 1.0),
        "loudness_range_lu": (5.0, 1.0),
        "true_peak_dbfs": (-0.5, 0.3),
        "dynamic_range_db": (7.5, 1.5),
        "crest_factor_db": (8.0, 1.5),
        "avg_stereo_width_percent": (82.0, 8.0),
        "avg_phase_correlation": (0.82, 0.08),
        "spectral_centroid_hz": (3000.0, 500.0),
        "spectral_bandwidth_hz": (3600.0, 500.0),
        "band_energy_profile": [-17.0, -21.0, -19.0, -23.0, -29.0],
        "band_spectral_centroid": [105.0, 345.0, 1100.0, 3600.0, 11500.0],
        "band_spectral_rolloff": [178.0, 475.0, 1780.0, 5400.0, 17800.0],
        "band_spectral_flatness": [0.14, 0.20, 0.24, 0.32, 0.42],
        "band_dynamic_range": [6.5, 7.5, 8.0, 7.5, 7.0],
        "band_crest_factor": [7.0, 8.0, 8.5, 8.0, 7.5],
        "band_rms": [-19.0, -23.0, -21.0, -25.0, -31.0],
        "band_stereo_width": [35.0, 58.0, 82.0, 90.0, 85.0],
        "band_phase_correlation": [0.96, 0.88, 0.80, 0.74, 0.68],
        "band_thd": [1.5, 1.0, 0.7, 0.5, 0.3],
        "band_harmonic_ratio": [0.72, 0.62, 0.52, 0.42, 0.32],
        "band_transient_preservation": [0.58, 0.62, 0.68, 0.74, 0.80],
        "band_attack_time": [16.0, 13.0, 9.0, 5.5, 3.5],
    },
    "Drum & Bass": {
        "integrated_lufs": (-4.0, 1.0),
        "loudness_range_lu": (4.5, 0.8),
        "true_peak_dbfs": (-0.2, 0.2),
        "dynamic_range_db": (5.0, 1.0),
        "crest_factor_db": (5.5, 1.0),
        "avg_stereo_width_percent": (90.0, 5.0),
        "avg_phase_correlation": (0.78, 0.08),
        "spectral_centroid_hz": (3800.0, 500.0),
        "spectral_bandwidth_hz": (4500.0, 500.0),
        "band_energy_profile": [-14.0, -20.0, -18.0, -20.0, -24.0],
        "band_spectral_centroid": [130.0, 370.0, 1250.0, 4000.0, 13000.0],
        "band_spectral_rolloff": [190.0, 490.0, 1900.0, 5800.0, 19000.0],
        "band_spectral_flatness": [0.20, 0.28, 0.35, 0.45, 0.55],
        "band_dynamic_range": [4.5, 5.0, 5.5, 5.0, 4.5],
        "band_crest_factor": [5.0, 5.5, 6.0, 5.5, 5.0],
        "band_rms": [-16.0, -22.0, -20.0, -22.0, -26.0],
        "band_stereo_width": [30.0, 70.0, 90.0, 95.0, 92.0],
        "band_phase_correlation": [0.97, 0.85, 0.75, 0.70, 0.65],
        "band_thd": [3.5, 2.5, 2.0, 1.5, 1.0],
        "band_harmonic_ratio": [0.60, 0.50, 0.40, 0.30, 0.20],
        "band_transient_preservation": [0.75, 0.78, 0.80, 0.82, 0.85],
        "band_attack_time": [8.0, 6.0, 4.0, 3.0, 2.0],
    },
    "Dubstep": {
        "integrated_lufs": (-3.0, 1.0),
        "loudness_range_lu": (4.0, 0.8),
        "true_peak_dbfs": (-0.1, 0.1),
        "dynamic_range_db": (4.0, 1.0),
        "crest_factor_db": (4.5, 1.0),
        "avg_stereo_width_percent": (88.0, 7.0),
        "avg_phase_correlation": (0.72, 0.10),
        "spectral_centroid_hz": (2500.0, 600.0),
        "spectral_bandwidth_hz": (4200.0, 600.0),
        "band_energy_profile": [-12.0, -16.0, -15.0, -20.0, -26.0],
        "band_spectral_centroid": [140.0, 380.0, 1300.0, 3900.0, 12500.0],
        "band_spectral_rolloff": [195.0, 495.0, 1950.0, 5900.0, 19500.0],
        "band_spectral_flatness": [0.22, 0.30, 0.38, 0.48, 0.55],
        "band_dynamic_range": [3.5, 4.0, 4.5, 4.0, 3.5],
        "band_crest_factor": [4.0, 4.5, 5.0, 4.5, 4.0],
        "band_rms": [-14.0, -18.0, -17.0, -22.0, -28.0],
        "band_stereo_width": [35.0, 75.0, 88.0, 92.0, 88.0],
        "band_phase_correlation": [0.95, 0.80, 0.70, 0.65, 0.60],
        "band_thd": [4.0, 3.5, 3.0, 2.0, 1.5],
        "band_harmonic_ratio": [0.55, 0.45, 0.35, 0.25, 0.18],
        "band_transient_preservation": [0.68, 0.72, 0.75, 0.78, 0.82],
        "band_attack_time": [12.0, 8.0, 5.0, 3.5, 2.0],
    },
}


def _jitter(value: float, variance: float) -> float:
    """Add random gaussian jitter to a value."""
    return value + random.gauss(0, variance * 0.3)


def _generate_band_metrics(
    reference_track_id: str,
    genre: str,
) -> list[ReferenceBandMetrics]:
    """Generate synthetic per-band metrics for a reference track."""
    profile = GENRE_PROFILES.get(genre, GENRE_PROFILES["House"])
    metrics = []

    for i, (band_name, freq_min, freq_max) in enumerate(BANDS):
        bm = ReferenceBandMetrics(
            reference_track_id=reference_track_id,
            band_name=band_name,
            freq_min=freq_min,
            freq_max=freq_max,
            band_rms_dbfs=_jitter(profile["band_rms"][i], 2.0),
            band_true_peak_dbfs=_jitter(profile["band_rms"][i] + 3.0, 1.0),
            band_level_range_db=_jitter(profile["band_dynamic_range"][i] * 0.8, 1.0),
            dynamic_range_db=_jitter(profile["band_dynamic_range"][i], 1.0),
            crest_factor_db=_jitter(profile["band_crest_factor"][i], 1.0),
            rms_db=_jitter(profile["band_rms"][i], 2.0),
            spectral_centroid_hz=_jitter(profile["band_spectral_centroid"][i], profile["band_spectral_centroid"][i] * 0.1),
            spectral_rolloff_hz=_jitter(profile["band_spectral_rolloff"][i], profile["band_spectral_rolloff"][i] * 0.1),
            spectral_flatness=max(0.0, min(1.0, _jitter(profile["band_spectral_flatness"][i], 0.05))),
            energy_db=_jitter(profile["band_energy_profile"][i], 2.0),
            stereo_width_percent=max(0.0, min(100.0, _jitter(profile["band_stereo_width"][i], 5.0))),
            phase_correlation=max(-1.0, min(1.0, _jitter(profile["band_phase_correlation"][i], 0.05))),
            mid_energy_db=_jitter(profile["band_energy_profile"][i] - 3.0, 2.0),
            side_energy_db=_jitter(profile["band_energy_profile"][i] - 10.0, 3.0),
            thd_percent=max(0.0, _jitter(profile["band_thd"][i], 0.5)),
            harmonic_ratio=max(0.0, min(1.0, _jitter(profile["band_harmonic_ratio"][i], 0.05))),
            inharmonicity=max(0.0, min(1.0, _jitter(0.3, 0.1))),
            transient_preservation=max(0.0, min(1.0, _jitter(profile["band_transient_preservation"][i], 0.05))),
            attack_time_ms=max(0.5, _jitter(profile["band_attack_time"][i], 2.0)),
        )
        metrics.append(bm)

    return metrics


def _generate_overall_metrics(
    reference_track_id: str,
    genre: str,
) -> ReferenceOverallMetrics:
    """Generate synthetic overall metrics for a reference track."""
    profile = GENRE_PROFILES.get(genre, GENRE_PROFILES["House"])

    return ReferenceOverallMetrics(
        reference_track_id=reference_track_id,
        integrated_lufs=_jitter(*profile["integrated_lufs"]),
        loudness_range_lu=max(0.0, _jitter(*profile["loudness_range_lu"])),
        true_peak_dbfs=_jitter(*profile["true_peak_dbfs"]),
        dynamic_range_db=max(0.0, _jitter(*profile["dynamic_range_db"])),
        crest_factor_db=max(0.0, _jitter(*profile["crest_factor_db"])),
        avg_stereo_width_percent=max(0.0, min(100.0, _jitter(*profile["avg_stereo_width_percent"]))),
        avg_phase_correlation=max(-1.0, min(1.0, _jitter(*profile["avg_phase_correlation"]))),
        spectral_centroid_hz=max(0.0, _jitter(*profile["spectral_centroid_hz"])),
        spectral_bandwidth_hz=max(0.0, _jitter(*profile["spectral_bandwidth_hz"])),
    )


def populate(force: bool = False) -> None:
    """Populate the database with reference tracks from metadata JSON.

    Args:
        force: If True, delete all existing built-in references before populating.
    """
    init_db()

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    logger.info("Loaded %d reference track entries from metadata", len(metadata))

    extractor = FeatureExtractor()
    session = SessionFactory()

    try:
        if force:
            existing = session.query(ReferenceTrack).filter(
                ReferenceTrack.is_builtin.is_(True)
            ).all()
            for track in existing:
                session.delete(track)
            session.flush()
            logger.info("Deleted %d existing built-in references", len(existing))

        inserted = 0
        skipped = 0

        for entry in metadata:
            # Check idempotency
            existing = session.query(ReferenceTrack).filter(
                ReferenceTrack.track_name == entry["track_name"],
                ReferenceTrack.artist == entry["artist"],
            ).first()

            if existing is not None:
                logger.info(
                    "Skipping existing reference: %s - %s",
                    entry["artist"], entry["track_name"],
                )
                skipped += 1
                continue

            # Create reference track
            track = ReferenceTrack(
                track_name=entry["track_name"],
                artist=entry["artist"],
                genre=entry["genre"],
                year=entry.get("year"),
                is_builtin=True,
                file_path=None,
            )
            session.add(track)
            session.flush()

            # Generate and attach band metrics
            band_metrics = _generate_band_metrics(track.id, entry["genre"])
            for bm in band_metrics:
                session.add(bm)

            # Generate and attach overall metrics
            overall_metrics = _generate_overall_metrics(track.id, entry["genre"])
            session.add(overall_metrics)
            session.flush()

            # Extract feature vector and store
            feature_vector = extractor.extract_from_metrics(band_metrics, overall_metrics)
            track.similarity_vector = serialize_vector(feature_vector)
            session.flush()

            logger.info(
                "Inserted reference: %s - %s [%s]",
                entry["artist"], entry["track_name"], entry["genre"],
            )
            inserted += 1

        session.commit()
        logger.info(
            "Population complete: %d inserted, %d skipped", inserted, skipped,
        )

    except Exception:
        session.rollback()
        logger.exception("Failed to populate references")
        raise
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate reference track database")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete all existing built-in references before populating",
    )
    args = parser.parse_args()
    populate(force=args.force)


if __name__ == "__main__":
    main()
