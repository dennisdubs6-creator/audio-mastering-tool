-- Migration: Add reference_overall_metrics table
-- Stores overall metrics for reference tracks, mirroring the overall_metrics structure.

CREATE TABLE IF NOT EXISTS reference_overall_metrics (
    id              TEXT PRIMARY KEY,
    reference_track_id TEXT NOT NULL,
    integrated_lufs      FLOAT,
    loudness_range_lu    FLOAT,
    true_peak_dbfs       FLOAT,
    dynamic_range_db     FLOAT,
    crest_factor_db      FLOAT,
    avg_stereo_width_percent FLOAT,
    avg_phase_correlation    FLOAT,
    spectral_centroid_hz     FLOAT,
    spectral_bandwidth_hz    FLOAT,
    FOREIGN KEY (reference_track_id) REFERENCES reference_tracks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ref_overall_metrics_reference
    ON reference_overall_metrics(reference_track_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_ref_overall_metrics_reference
    ON reference_overall_metrics(reference_track_id);
