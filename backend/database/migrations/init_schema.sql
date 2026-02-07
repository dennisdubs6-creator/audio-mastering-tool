-- Audio Mastering Tool - Initial Schema
-- Creates all 7 tables, indexes, and default data.
-- This script is provided as a reference; the ORM creates tables via
-- SQLAlchemy's Base.metadata.create_all() at startup.

-- ============================================================
-- Table 1: analysis
-- Core record for each uploaded audio file analysis.
-- ============================================================
CREATE TABLE IF NOT EXISTS analysis (
    id              TEXT PRIMARY KEY,
    file_path       VARCHAR(1024) NOT NULL,
    file_name       VARCHAR(255)  NOT NULL,
    file_size       INTEGER,
    sample_rate     INTEGER,
    bit_depth       INTEGER,
    duration_seconds REAL,
    genre           VARCHAR(100),
    genre_confidence REAL,
    recommendation_level VARCHAR(50) NOT NULL DEFAULT 'suggestive',
    analysis_engine_version VARCHAR(50),
    analysis_parameters_json TEXT,
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME NOT NULL
);

-- ============================================================
-- Table 2: band_metrics
-- Per-frequency-band measurements linked to an analysis.
-- ============================================================
CREATE TABLE IF NOT EXISTS band_metrics (
    id                   TEXT PRIMARY KEY,
    analysis_id          TEXT NOT NULL REFERENCES analysis(id) ON DELETE CASCADE,
    band_name            VARCHAR(50) NOT NULL,
    freq_min             INTEGER NOT NULL,
    freq_max             INTEGER NOT NULL,
    band_rms_dbfs        REAL,
    band_true_peak_dbfs  REAL,
    band_level_range_db  REAL,
    dynamic_range_db     REAL,
    crest_factor_db      REAL,
    rms_db               REAL,
    spectral_centroid_hz REAL,
    spectral_rolloff_hz  REAL,
    spectral_flatness    REAL,
    energy_db            REAL,
    stereo_width_percent REAL,
    phase_correlation    REAL,
    mid_energy_db        REAL,
    side_energy_db       REAL,
    thd_percent          REAL,
    harmonic_ratio       REAL,
    inharmonicity        REAL,
    transient_preservation REAL,
    attack_time_ms       REAL
);

CREATE INDEX IF NOT EXISTS idx_band_metrics_analysis ON band_metrics(analysis_id);
CREATE INDEX IF NOT EXISTS idx_band_metrics_band     ON band_metrics(band_name);

-- ============================================================
-- Table 3: overall_metrics
-- Aggregate metrics for the full audio file (one per analysis).
-- ============================================================
CREATE TABLE IF NOT EXISTS overall_metrics (
    id                       TEXT PRIMARY KEY,
    analysis_id              TEXT NOT NULL REFERENCES analysis(id) ON DELETE CASCADE,
    integrated_lufs          REAL,
    loudness_range_lu        REAL,
    true_peak_dbfs           REAL,
    dynamic_range_db         REAL,
    crest_factor_db          REAL,
    avg_stereo_width_percent REAL,
    avg_phase_correlation    REAL,
    spectral_centroid_hz     REAL,
    spectral_bandwidth_hz    REAL,
    CONSTRAINT uq_overall_metrics_analysis UNIQUE (analysis_id)
);

CREATE INDEX IF NOT EXISTS idx_overall_metrics_analysis ON overall_metrics(analysis_id);

-- ============================================================
-- Table 4: reference_tracks
-- Built-in and user-added reference tracks for comparison.
-- ============================================================
CREATE TABLE IF NOT EXISTS reference_tracks (
    id                TEXT PRIMARY KEY,
    track_name        VARCHAR(255) NOT NULL,
    artist            VARCHAR(255),
    genre             VARCHAR(100),
    year              INTEGER,
    is_builtin        BOOLEAN NOT NULL DEFAULT 0,
    file_path         VARCHAR(1024),
    similarity_vector BLOB,
    created_at        DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reference_genre   ON reference_tracks(genre);
CREATE INDEX IF NOT EXISTS idx_reference_builtin ON reference_tracks(is_builtin);

-- ============================================================
-- Table 5: reference_band_metrics
-- Per-band metrics for reference tracks (mirrors band_metrics).
-- ============================================================
CREATE TABLE IF NOT EXISTS reference_band_metrics (
    id                   TEXT PRIMARY KEY,
    reference_track_id   TEXT NOT NULL REFERENCES reference_tracks(id) ON DELETE CASCADE,
    band_name            VARCHAR(50) NOT NULL,
    freq_min             INTEGER NOT NULL,
    freq_max             INTEGER NOT NULL,
    band_rms_dbfs        REAL,
    band_true_peak_dbfs  REAL,
    band_level_range_db  REAL,
    dynamic_range_db     REAL,
    crest_factor_db      REAL,
    rms_db               REAL,
    spectral_centroid_hz REAL,
    spectral_rolloff_hz  REAL,
    spectral_flatness    REAL,
    energy_db            REAL,
    stereo_width_percent REAL,
    phase_correlation    REAL,
    mid_energy_db        REAL,
    side_energy_db       REAL,
    thd_percent          REAL,
    harmonic_ratio       REAL,
    inharmonicity        REAL,
    transient_preservation REAL,
    attack_time_ms       REAL
);

CREATE INDEX IF NOT EXISTS idx_ref_band_metrics_reference ON reference_band_metrics(reference_track_id);
CREATE INDEX IF NOT EXISTS idx_ref_band_metrics_band      ON reference_band_metrics(band_name);

-- ============================================================
-- Table 6: recommendations
-- Mastering recommendations tied to an analysis.
-- ============================================================
CREATE TABLE IF NOT EXISTS recommendations (
    id                  TEXT PRIMARY KEY,
    analysis_id         TEXT NOT NULL REFERENCES analysis(id) ON DELETE CASCADE,
    band_name           VARCHAR(50),
    metric_category     VARCHAR(100),
    severity            VARCHAR(50),
    recommendation_text TEXT,
    analytical_text     TEXT,
    suggestive_text     TEXT,
    prescriptive_text   TEXT,
    created_at          DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_recommendations_analysis ON recommendations(analysis_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_severity ON recommendations(severity);

-- ============================================================
-- Table 7: user_settings
-- Key-value store for application settings.
-- ============================================================
CREATE TABLE IF NOT EXISTS user_settings (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at DATETIME NOT NULL
);

-- Default settings
INSERT OR IGNORE INTO user_settings (key, value, updated_at)
VALUES
    ('recommendation_level', 'suggestive', datetime('now')),
    ('default_genre',        '',           datetime('now')),
    ('theme',                'dark',       datetime('now'));
