"""
SQLAlchemy ORM models for all 8 database tables.

Tables:
    - analysis: Core analysis records for uploaded audio files.
    - band_metrics: Per-frequency-band metrics linked to an analysis.
    - overall_metrics: Aggregate metrics for a complete analysis.
    - reference_tracks: Built-in and user-added reference tracks.
    - reference_band_metrics: Per-band metrics for reference tracks.
    - reference_overall_metrics: Aggregate metrics for reference tracks.
    - recommendations: Band-level mastering recommendations.
    - user_settings: Key-value application settings.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BLOB,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def _generate_uuid() -> str:
    """Generate a new UUID4 string for use as a primary key."""
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Analysis(Base):
    """Core analysis record for an uploaded audio file.

    Stores metadata about the analysed file and links to per-band metrics,
    overall metrics, and recommendations via relationships.
    """

    __tablename__ = "analysis"

    id = Column(Text, primary_key=True, default=_generate_uuid)
    file_path = Column(String(1024), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    sample_rate = Column(Integer, nullable=True)
    bit_depth = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    genre = Column(String(100), nullable=True)
    genre_confidence = Column(Float, nullable=True)
    recommendation_level = Column(String(50), default="suggestive", nullable=False)
    analysis_engine_version = Column(String(50), nullable=True)
    analysis_parameters_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    band_metrics = relationship(
        "BandMetrics", back_populates="analysis", cascade="all, delete-orphan"
    )
    overall_metrics = relationship(
        "OverallMetrics", back_populates="analysis", cascade="all, delete-orphan", uselist=False
    )
    recommendations = relationship(
        "Recommendation", back_populates="analysis", cascade="all, delete-orphan"
    )


class BandMetrics(Base):
    """Per-frequency-band metrics for an analysis.

    Each row captures a full set of audio measurements for one frequency band
    (e.g. low, low_mid, mid, high_mid, high) within a single analysis.
    """

    __tablename__ = "band_metrics"

    id = Column(Text, primary_key=True, default=_generate_uuid)
    analysis_id = Column(
        Text, ForeignKey("analysis.id", ondelete="CASCADE"), nullable=False
    )
    band_name = Column(String(50), nullable=False)
    freq_min = Column(Integer, nullable=False)
    freq_max = Column(Integer, nullable=False)
    band_rms_dbfs = Column(Float, nullable=True)
    band_true_peak_dbfs = Column(Float, nullable=True)
    band_level_range_db = Column(Float, nullable=True)
    dynamic_range_db = Column(Float, nullable=True)
    crest_factor_db = Column(Float, nullable=True)
    rms_db = Column(Float, nullable=True)
    spectral_centroid_hz = Column(Float, nullable=True)
    spectral_rolloff_hz = Column(Float, nullable=True)
    spectral_flatness = Column(Float, nullable=True)
    energy_db = Column(Float, nullable=True)
    stereo_width_percent = Column(Float, nullable=True)
    phase_correlation = Column(Float, nullable=True)
    mid_energy_db = Column(Float, nullable=True)
    side_energy_db = Column(Float, nullable=True)
    thd_percent = Column(Float, nullable=True)
    harmonic_ratio = Column(Float, nullable=True)
    inharmonicity = Column(Float, nullable=True)
    transient_preservation = Column(Float, nullable=True)
    attack_time_ms = Column(Float, nullable=True)

    analysis = relationship("Analysis", back_populates="band_metrics")

    __table_args__ = (
        Index("idx_band_metrics_analysis", "analysis_id"),
        Index("idx_band_metrics_band", "band_name"),
    )


class OverallMetrics(Base):
    """Aggregate audio metrics for an entire analysis.

    One-to-one relationship with Analysis. Captures loudness, dynamics,
    stereo imaging, and spectral characteristics across the full frequency
    range.
    """

    __tablename__ = "overall_metrics"

    id = Column(Text, primary_key=True, default=_generate_uuid)
    analysis_id = Column(
        Text, ForeignKey("analysis.id", ondelete="CASCADE"), nullable=False
    )
    integrated_lufs = Column(Float, nullable=True)
    loudness_range_lu = Column(Float, nullable=True)
    true_peak_dbfs = Column(Float, nullable=True)
    dynamic_range_db = Column(Float, nullable=True)
    crest_factor_db = Column(Float, nullable=True)
    avg_stereo_width_percent = Column(Float, nullable=True)
    avg_phase_correlation = Column(Float, nullable=True)
    spectral_centroid_hz = Column(Float, nullable=True)
    spectral_bandwidth_hz = Column(Float, nullable=True)
    warnings = Column(Text, nullable=True)

    analysis = relationship("Analysis", back_populates="overall_metrics")

    __table_args__ = (
        Index("idx_overall_metrics_analysis", "analysis_id"),
        UniqueConstraint("analysis_id", name="uq_overall_metrics_analysis"),
    )


class ReferenceTrack(Base):
    """A reference audio track for comparison during analysis.

    Can be a built-in (pre-shipped) track or a user-added track. Stores
    optional similarity vector for future ML-based matching.
    """

    __tablename__ = "reference_tracks"

    id = Column(Text, primary_key=True, default=_generate_uuid)
    track_name = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=True)
    genre = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    is_builtin = Column(Boolean, default=False, nullable=False)
    file_path = Column(String(1024), nullable=True)
    similarity_vector = Column(BLOB, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    reference_band_metrics = relationship(
        "ReferenceBandMetrics",
        back_populates="reference_track",
        cascade="all, delete-orphan",
    )
    reference_overall_metrics = relationship(
        "ReferenceOverallMetrics",
        back_populates="reference_track",
        cascade="all, delete-orphan",
        uselist=False,
    )

    __table_args__ = (
        Index("idx_reference_genre", "genre"),
        Index("idx_reference_builtin", "is_builtin"),
    )


class ReferenceBandMetrics(Base):
    """Per-frequency-band metrics for a reference track.

    Mirrors the BandMetrics schema but is linked to a ReferenceTrack
    instead of an Analysis.
    """

    __tablename__ = "reference_band_metrics"

    id = Column(Text, primary_key=True, default=_generate_uuid)
    reference_track_id = Column(
        Text, ForeignKey("reference_tracks.id", ondelete="CASCADE"), nullable=False
    )
    band_name = Column(String(50), nullable=False)
    freq_min = Column(Integer, nullable=False)
    freq_max = Column(Integer, nullable=False)
    band_rms_dbfs = Column(Float, nullable=True)
    band_true_peak_dbfs = Column(Float, nullable=True)
    band_level_range_db = Column(Float, nullable=True)
    dynamic_range_db = Column(Float, nullable=True)
    crest_factor_db = Column(Float, nullable=True)
    rms_db = Column(Float, nullable=True)
    spectral_centroid_hz = Column(Float, nullable=True)
    spectral_rolloff_hz = Column(Float, nullable=True)
    spectral_flatness = Column(Float, nullable=True)
    energy_db = Column(Float, nullable=True)
    stereo_width_percent = Column(Float, nullable=True)
    phase_correlation = Column(Float, nullable=True)
    mid_energy_db = Column(Float, nullable=True)
    side_energy_db = Column(Float, nullable=True)
    thd_percent = Column(Float, nullable=True)
    harmonic_ratio = Column(Float, nullable=True)
    inharmonicity = Column(Float, nullable=True)
    transient_preservation = Column(Float, nullable=True)
    attack_time_ms = Column(Float, nullable=True)

    reference_track = relationship("ReferenceTrack", back_populates="reference_band_metrics")

    __table_args__ = (
        Index("idx_ref_band_metrics_reference", "reference_track_id"),
        Index("idx_ref_band_metrics_band", "band_name"),
    )


class ReferenceOverallMetrics(Base):
    """Aggregate audio metrics for a reference track.

    One-to-one relationship with ReferenceTrack. Mirrors the OverallMetrics
    structure but is linked to a reference track instead of an analysis.
    """

    __tablename__ = "reference_overall_metrics"

    id = Column(Text, primary_key=True, default=_generate_uuid)
    reference_track_id = Column(
        Text, ForeignKey("reference_tracks.id", ondelete="CASCADE"), nullable=False
    )
    integrated_lufs = Column(Float, nullable=True)
    loudness_range_lu = Column(Float, nullable=True)
    true_peak_dbfs = Column(Float, nullable=True)
    dynamic_range_db = Column(Float, nullable=True)
    crest_factor_db = Column(Float, nullable=True)
    avg_stereo_width_percent = Column(Float, nullable=True)
    avg_phase_correlation = Column(Float, nullable=True)
    spectral_centroid_hz = Column(Float, nullable=True)
    spectral_bandwidth_hz = Column(Float, nullable=True)

    reference_track = relationship("ReferenceTrack", back_populates="reference_overall_metrics")

    __table_args__ = (
        Index("idx_ref_overall_metrics_reference", "reference_track_id"),
        UniqueConstraint("reference_track_id", name="uq_ref_overall_metrics_reference"),
    )


class Recommendation(Base):
    """A mastering recommendation for a specific frequency band.

    Contains three verbosity levels of the same recommendation:
    analytical, suggestive, and prescriptive. The active level is
    determined by the parent Analysis.recommendation_level setting.
    """

    __tablename__ = "recommendations"

    id = Column(Text, primary_key=True, default=_generate_uuid)
    analysis_id = Column(
        Text, ForeignKey("analysis.id", ondelete="CASCADE"), nullable=False
    )
    band_name = Column(String(50), nullable=True)
    metric_category = Column(String(100), nullable=True)
    severity = Column(String(50), nullable=True)
    recommendation_text = Column(Text, nullable=True)
    analytical_text = Column(Text, nullable=True)
    suggestive_text = Column(Text, nullable=True)
    prescriptive_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    analysis = relationship("Analysis", back_populates="recommendations")

    __table_args__ = (
        Index("idx_recommendations_analysis", "analysis_id"),
        Index("idx_recommendations_severity", "severity"),
    )


class UserSettings(Base):
    """Key-value store for application-level user settings.

    The primary key is the setting name (e.g. 'default_genre',
    'recommendation_level'). Values are stored as text strings.
    """

    __tablename__ = "user_settings"

    key = Column(Text, primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
