"""
Comparison API endpoint.

- ``GET /api/compare/{analysis_id}/{reference_id}`` – Compare user analysis
  against a reference track and generate recommendations.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_session_dependency
from api.repositories.analysis_repo import AnalysisRepository
from api.repositories.reference_repo import ReferenceRepository
from api.schemas import (
    AnalysisResponse,
    BandMetricResponse,
    ComparisonResponse,
    OverallMetricResponse,
    RecommendationResponse,
    ReferenceTrackResponse,
)
from recommendations.engine import RecommendationEngine

router = APIRouter(prefix="/api", tags=["comparison"])


@router.get(
    "/compare/{analysis_id}/{reference_id}",
    response_model=ComparisonResponse,
)
def compare_with_reference(
    analysis_id: str,
    reference_id: str,
    recommendation_level: str = Query(
        "suggestive",
        description="One of: analytical, suggestive, prescriptive",
    ),
    session: Session = Depends(get_session_dependency),
) -> ComparisonResponse:
    """Compare a user analysis against a reference track.

    Fetches both sets of metrics, generates comparison-aware recommendations,
    and returns a unified response.

    Args:
        analysis_id: UUID of the user analysis.
        reference_id: UUID of the reference track.
        recommendation_level: Verbosity level for recommendation text.

    Raises:
        404: Analysis or reference track not found.
        400: Analysis or reference track has incomplete metrics.
    """
    analysis_repo = AnalysisRepository(session)
    analysis = analysis_repo.get_with_metrics(analysis_id)

    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if not analysis.band_metrics or analysis.overall_metrics is None:
        raise HTTPException(
            status_code=400,
            detail="Analysis is incomplete: missing band metrics or overall metrics",
        )

    ref_repo = ReferenceRepository(session)
    reference = ref_repo.get_with_all_metrics(reference_id)

    if reference is None:
        raise HTTPException(status_code=404, detail="Reference track not found")

    if not reference.reference_band_metrics:
        raise HTTPException(
            status_code=400,
            detail="Reference track has incomplete metrics",
        )

    # Generate recommendations
    engine = RecommendationEngine()
    rec_dicts = engine.generate(
        user_band_metrics=analysis.band_metrics,
        user_overall_metrics=analysis.overall_metrics,
        reference_band_metrics=reference.reference_band_metrics,
        reference_overall_metrics=reference.reference_overall_metrics,
        genre=analysis.genre,
        recommendation_level=recommendation_level,
    )

    # Convert recommendation dicts to response objects
    now = datetime.now(timezone.utc)
    rec_responses = [
        RecommendationResponse(
            id=str(uuid.uuid4()),
            band_name=r.get("band_name"),
            metric_category=r.get("metric_category"),
            severity=r.get("severity"),
            recommendation_text=r.get("recommendation_text"),
            analytical_text=r.get("analytical_text"),
            suggestive_text=r.get("suggestive_text"),
            prescriptive_text=r.get("prescriptive_text"),
            created_at=now,
        )
        for r in rec_dicts
    ]

    # Map reference band metrics to BandMetricResponse format
    ref_band_responses = [
        BandMetricResponse(
            id=rbm.id,
            band_name=rbm.band_name,
            freq_min=rbm.freq_min,
            freq_max=rbm.freq_max,
            band_rms_dbfs=rbm.band_rms_dbfs,
            band_true_peak_dbfs=rbm.band_true_peak_dbfs,
            band_level_range_db=rbm.band_level_range_db,
            dynamic_range_db=rbm.dynamic_range_db,
            crest_factor_db=rbm.crest_factor_db,
            rms_db=rbm.rms_db,
            spectral_centroid_hz=rbm.spectral_centroid_hz,
            spectral_rolloff_hz=rbm.spectral_rolloff_hz,
            spectral_flatness=rbm.spectral_flatness,
            energy_db=rbm.energy_db,
            stereo_width_percent=rbm.stereo_width_percent,
            phase_correlation=rbm.phase_correlation,
            mid_energy_db=rbm.mid_energy_db,
            side_energy_db=rbm.side_energy_db,
            thd_percent=rbm.thd_percent,
            harmonic_ratio=rbm.harmonic_ratio,
            inharmonicity=rbm.inharmonicity,
            transient_preservation=rbm.transient_preservation,
            attack_time_ms=rbm.attack_time_ms,
        )
        for rbm in reference.reference_band_metrics
    ]

    # Map reference overall metrics
    ref_overall_response = None
    if reference.reference_overall_metrics:
        rom = reference.reference_overall_metrics
        ref_overall_response = OverallMetricResponse(
            id=rom.id,
            integrated_lufs=rom.integrated_lufs,
            loudness_range_lu=rom.loudness_range_lu,
            true_peak_dbfs=rom.true_peak_dbfs,
            dynamic_range_db=rom.dynamic_range_db,
            crest_factor_db=rom.crest_factor_db,
            avg_stereo_width_percent=rom.avg_stereo_width_percent,
            avg_phase_correlation=rom.avg_phase_correlation,
            spectral_centroid_hz=rom.spectral_centroid_hz,
            spectral_bandwidth_hz=rom.spectral_bandwidth_hz,
        )

    return ComparisonResponse(
        user_analysis=AnalysisResponse.model_validate(analysis),
        reference_track=ReferenceTrackResponse.model_validate(reference),
        reference_band_metrics=ref_band_responses,
        reference_overall_metrics=ref_overall_response,
        recommendations=rec_responses,
        comparison_mode="side-by-side",
    )
