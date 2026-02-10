"""
Analyze a real audio file and store it as a reference track.

Uses the existing AnalysisEngine to compute metrics from an actual audio
file, then stores the results as a reference track with pre-computed
feature vector.

Usage:
    python -m scripts.analyze_reference path/to/track.wav \
        --name "Track Name" --artist "Artist" --genre "Psytrance" --year 2020
"""

import argparse
import logging
import sys

from api.database import SessionFactory, init_db
from api.models import (
    ReferenceBandMetrics,
    ReferenceOverallMetrics,
    ReferenceTrack,
)
from analysis.engine import AnalysisEngine
from config.constants import FREQUENCY_BANDS
from dsp.audio_loader import AudioLoader
from dsp.band_integrator import BandIntegrator
from dsp.stft_processor import STFTProcessor
from ml.feature_extraction import FeatureExtractor
from ml.similarity import serialize_vector

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def analyze_and_store(
    file_path: str,
    track_name: str,
    artist: str,
    genre: str,
    year: int | None = None,
) -> str:
    """Analyze an audio file and store results as a reference track.

    Args:
        file_path: Path to the WAV audio file.
        track_name: Name of the track.
        artist: Artist name.
        genre: Genre classification.
        year: Release year (optional).

    Returns:
        UUID of the created reference track.
    """
    init_db()

    # Build analysis engine
    engine = AnalysisEngine(
        stft_processor=STFTProcessor(),
        band_integrator=BandIntegrator(FREQUENCY_BANDS),
        audio_loader=AudioLoader(),
    )

    # Create a temporary analysis ID for the engine
    import uuid
    temp_analysis_id = str(uuid.uuid4())

    logger.info("Analyzing audio file: %s", file_path)
    band_metrics_list, overall_metrics = engine.analyze_audio(file_path, temp_analysis_id)

    session = SessionFactory()
    try:
        # Create reference track
        track = ReferenceTrack(
            track_name=track_name,
            artist=artist,
            genre=genre,
            year=year,
            is_builtin=False,
            file_path=file_path,
        )
        session.add(track)
        session.flush()

        # Convert BandMetrics to ReferenceBandMetrics
        ref_band_metrics = []
        for bm in band_metrics_list:
            rbm = ReferenceBandMetrics(
                reference_track_id=track.id,
                band_name=bm.band_name,
                freq_min=bm.freq_min,
                freq_max=bm.freq_max,
                band_rms_dbfs=bm.band_rms_dbfs,
                band_true_peak_dbfs=bm.band_true_peak_dbfs,
                band_level_range_db=bm.band_level_range_db,
                dynamic_range_db=bm.dynamic_range_db,
                crest_factor_db=bm.crest_factor_db,
                rms_db=bm.rms_db,
                spectral_centroid_hz=bm.spectral_centroid_hz,
                spectral_rolloff_hz=bm.spectral_rolloff_hz,
                spectral_flatness=bm.spectral_flatness,
                energy_db=bm.energy_db,
                stereo_width_percent=bm.stereo_width_percent,
                phase_correlation=bm.phase_correlation,
                mid_energy_db=bm.mid_energy_db,
                side_energy_db=bm.side_energy_db,
                thd_percent=bm.thd_percent,
                harmonic_ratio=bm.harmonic_ratio,
                inharmonicity=bm.inharmonicity,
                transient_preservation=bm.transient_preservation,
                attack_time_ms=bm.attack_time_ms,
            )
            session.add(rbm)
            ref_band_metrics.append(rbm)

        # Convert OverallMetrics to ReferenceOverallMetrics
        ref_overall = ReferenceOverallMetrics(
            reference_track_id=track.id,
            integrated_lufs=overall_metrics.integrated_lufs,
            loudness_range_lu=overall_metrics.loudness_range_lu,
            true_peak_dbfs=overall_metrics.true_peak_dbfs,
            dynamic_range_db=overall_metrics.dynamic_range_db,
            crest_factor_db=overall_metrics.crest_factor_db,
            avg_stereo_width_percent=overall_metrics.avg_stereo_width_percent,
            avg_phase_correlation=overall_metrics.avg_phase_correlation,
            spectral_centroid_hz=overall_metrics.spectral_centroid_hz,
            spectral_bandwidth_hz=overall_metrics.spectral_bandwidth_hz,
        )
        session.add(ref_overall)
        session.flush()

        # Extract and store feature vector
        extractor = FeatureExtractor()
        feature_vector = extractor.extract_from_metrics(ref_band_metrics, ref_overall)
        track.similarity_vector = serialize_vector(feature_vector)

        session.commit()
        logger.info("Reference track created: id=%s", track.id)
        return track.id

    except Exception:
        session.rollback()
        logger.exception("Failed to create reference track")
        raise
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze an audio file and store as reference track"
    )
    parser.add_argument("file_path", help="Path to WAV audio file")
    parser.add_argument("--name", required=True, help="Track name")
    parser.add_argument("--artist", required=True, help="Artist name")
    parser.add_argument("--genre", required=True, help="Genre classification")
    parser.add_argument("--year", type=int, default=None, help="Release year")

    args = parser.parse_args()
    track_id = analyze_and_store(
        file_path=args.file_path,
        track_name=args.name,
        artist=args.artist,
        genre=args.genre,
        year=args.year,
    )
    print(f"Reference track ID: {track_id}")


if __name__ == "__main__":
    main()
