"""
Pydantic v2 request / response models for the Audio Mastering Tool API.

These schemas define the shape of data exchanged over HTTP and are used
for automatic validation and OpenAPI documentation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Band Metrics
# ---------------------------------------------------------------------------

class BandMetricResponse(BaseModel):
    """Single frequency-band metric set returned inside an analysis response."""

    id: str
    band_name: str
    freq_min: int
    freq_max: int
    band_rms_dbfs: Optional[float] = None
    band_true_peak_dbfs: Optional[float] = None
    band_level_range_db: Optional[float] = None
    dynamic_range_db: Optional[float] = None
    crest_factor_db: Optional[float] = None
    rms_db: Optional[float] = None
    spectral_centroid_hz: Optional[float] = None
    spectral_rolloff_hz: Optional[float] = None
    spectral_flatness: Optional[float] = None
    energy_db: Optional[float] = None
    stereo_width_percent: Optional[float] = None
    phase_correlation: Optional[float] = None
    mid_energy_db: Optional[float] = None
    side_energy_db: Optional[float] = None
    thd_percent: Optional[float] = None
    harmonic_ratio: Optional[float] = None
    inharmonicity: Optional[float] = None
    transient_preservation: Optional[float] = None
    attack_time_ms: Optional[float] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Overall Metrics
# ---------------------------------------------------------------------------

class OverallMetricResponse(BaseModel):
    """Aggregate metrics for the entire audio file."""

    id: str
    integrated_lufs: Optional[float] = None
    loudness_range_lu: Optional[float] = None
    true_peak_dbfs: Optional[float] = None
    dynamic_range_db: Optional[float] = None
    crest_factor_db: Optional[float] = None
    avg_stereo_width_percent: Optional[float] = None
    avg_phase_correlation: Optional[float] = None
    spectral_centroid_hz: Optional[float] = None
    spectral_bandwidth_hz: Optional[float] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

class RecommendationResponse(BaseModel):
    """A single mastering recommendation."""

    id: str
    band_name: Optional[str] = None
    metric_category: Optional[str] = None
    severity: Optional[str] = None
    recommendation_text: Optional[str] = None
    analytical_text: Optional[str] = None
    suggestive_text: Optional[str] = None
    prescriptive_text: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

class AnalysisCreate(BaseModel):
    """Request body fields accepted alongside the uploaded file.

    Most fields are supplied via multipart form data; the file itself is
    handled separately by FastAPI's ``UploadFile``.
    """

    genre: Optional[str] = Field(None, max_length=100, description="Audio genre tag")
    recommendation_level: str = Field(
        "suggestive",
        description="One of: analytical, suggestive, prescriptive",
    )


class AnalysisResponse(BaseModel):
    """Full analysis result returned by ``GET /api/analysis/{id}``."""

    id: str
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    sample_rate: Optional[int] = None
    bit_depth: Optional[int] = None
    duration_seconds: Optional[float] = None
    genre: Optional[str] = None
    genre_confidence: Optional[float] = None
    recommendation_level: str
    analysis_engine_version: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    band_metrics: list[BandMetricResponse] = []
    overall_metrics: Optional[OverallMetricResponse] = None
    recommendations: list[RecommendationResponse] = []

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Reference Tracks
# ---------------------------------------------------------------------------

class ReferenceTrackResponse(BaseModel):
    """Summary of a reference track returned by ``GET /api/references``."""

    id: str
    track_name: str
    artist: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    is_builtin: bool
    created_at: datetime

    model_config = {"from_attributes": True}
