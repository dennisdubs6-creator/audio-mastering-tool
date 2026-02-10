"""
Tests for database initialisation and schema integrity.
"""

from sqlalchemy import inspect

from api.models import Base


EXPECTED_TABLES = [
    "analysis",
    "band_metrics",
    "overall_metrics",
    "reference_tracks",
    "reference_band_metrics",
    "reference_overall_metrics",
    "recommendations",
    "user_settings",
]

EXPECTED_INDEXES = [
    "idx_band_metrics_analysis",
    "idx_band_metrics_band",
    "idx_overall_metrics_analysis",
    "idx_reference_genre",
    "idx_reference_builtin",
    "idx_ref_band_metrics_reference",
    "idx_ref_band_metrics_band",
    "idx_recommendations_analysis",
    "idx_recommendations_severity",
]


def test_all_tables_created(engine):
    """All 7 expected tables should exist in the database."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    for table in EXPECTED_TABLES:
        assert table in tables, f"Table '{table}' not found in database"


def test_table_count(engine):
    """Exactly 8 tables should exist."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert len(tables) == 8


def test_analysis_columns(engine):
    """The analysis table should have the expected columns."""
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("analysis")}
    expected = {
        "id", "file_path", "file_name", "file_size", "sample_rate",
        "bit_depth", "duration_seconds", "status", "genre", "genre_confidence",
        "recommendation_level", "analysis_engine_version",
        "analysis_parameters_json", "created_at", "updated_at",
    }
    assert expected.issubset(columns)


def test_overall_metrics_columns(engine):
    """The overall_metrics table should include warning text storage."""
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("overall_metrics")}
    assert "warnings" in columns


def test_band_metrics_foreign_key(engine):
    """band_metrics should have a foreign key to analysis."""
    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("band_metrics")
    assert len(fks) >= 1
    fk_tables = {fk["referred_table"] for fk in fks}
    assert "analysis" in fk_tables


def test_overall_metrics_foreign_key(engine):
    """overall_metrics should have a foreign key to analysis."""
    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("overall_metrics")
    assert len(fks) >= 1
    fk_tables = {fk["referred_table"] for fk in fks}
    assert "analysis" in fk_tables


def test_reference_band_metrics_foreign_key(engine):
    """reference_band_metrics should have a foreign key to reference_tracks."""
    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("reference_band_metrics")
    assert len(fks) >= 1
    fk_tables = {fk["referred_table"] for fk in fks}
    assert "reference_tracks" in fk_tables


def test_recommendations_foreign_key(engine):
    """recommendations should have a foreign key to analysis."""
    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("recommendations")
    assert len(fks) >= 1
    fk_tables = {fk["referred_table"] for fk in fks}
    assert "analysis" in fk_tables


def test_indexes_exist(engine):
    """All expected indexes should be present in the database."""
    inspector = inspect(engine)
    all_indexes: set[str] = set()
    for table in EXPECTED_TABLES:
        for idx in inspector.get_indexes(table):
            all_indexes.add(idx["name"])
    for idx_name in EXPECTED_INDEXES:
        assert idx_name in all_indexes, f"Index '{idx_name}' not found"
