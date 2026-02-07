from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    genre = Column(String(100), nullable=True)
    recommendation_level = Column(
        String(50), default="suggestive", nullable=False
    )  # analytical | suggestive | prescriptive

    per_band_metrics = relationship(
        "PerBandMetric", back_populates="analysis", cascade="all, delete-orphan"
    )
    detailed_metrics = relationship(
        "DetailedMetric", back_populates="analysis", cascade="all, delete-orphan"
    )
    reference_matches = relationship(
        "ReferenceMatch", back_populates="analysis", cascade="all, delete-orphan"
    )
    recommendations = relationship(
        "Recommendation", back_populates="analysis", cascade="all, delete-orphan"
    )
    history_entries = relationship(
        "AnalysisHistory", back_populates="analysis", cascade="all, delete-orphan"
    )


class PerBandMetric(Base):
    __tablename__ = "per_band_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    frequency_band = Column(
        String(50), nullable=False
    )  # Low | Low Mid | Mid | High Mid | High
    loudness = Column(Float, nullable=True)
    dynamic_range = Column(Float, nullable=True)
    frequency_balance = Column(Float, nullable=True)
    stereo_width = Column(Float, nullable=True)
    harmonics = Column(Float, nullable=True)
    transient_response = Column(Float, nullable=True)

    analysis = relationship("Analysis", back_populates="per_band_metrics")


class DetailedMetric(Base):
    __tablename__ = "detailed_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    metric_type = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    analysis = relationship("Analysis", back_populates="detailed_metrics")


class ReferenceTrack(Base):
    __tablename__ = "reference_tracks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_name = Column(String(255), nullable=False)
    genre = Column(String(100), nullable=True)
    artist = Column(String(255), nullable=True)
    file_path = Column(String(1024), nullable=True)
    features_hash = Column(String(64), nullable=True)
    precomputed_features = Column(Text, nullable=True)  # JSON blob

    matches = relationship(
        "ReferenceMatch", back_populates="reference_track", cascade="all, delete-orphan"
    )


class ReferenceMatch(Base):
    __tablename__ = "reference_matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    reference_track_id = Column(
        Integer, ForeignKey("reference_tracks.id"), nullable=False
    )
    similarity_score = Column(Float, nullable=False)
    match_type = Column(String(50), nullable=True)

    analysis = relationship("Analysis", back_populates="reference_matches")
    reference_track = relationship("ReferenceTrack", back_populates="matches")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    band_id = Column(String(50), nullable=True)  # frequency band name or 'overall'
    metric_type = Column(String(100), nullable=False)
    recommendation_text = Column(Text, nullable=False)
    guidance_level = Column(
        String(50), nullable=False
    )  # analytical | suggestive | prescriptive

    analysis = relationship("Analysis", back_populates="recommendations")


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    action = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    analysis = relationship("Analysis", back_populates="history_entries")
