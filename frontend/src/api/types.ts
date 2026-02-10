/**
 * Frontend types aligned to the backend Pydantic schemas
 * (backend/api/schemas.py).
 */

export interface BandMetricResponse {
  id: string;
  band_name: string;
  freq_min: number;
  freq_max: number;
  band_rms_dbfs: number | null;
  band_true_peak_dbfs: number | null;
  band_level_range_db: number | null;
  dynamic_range_db: number | null;
  crest_factor_db: number | null;
  rms_db: number | null;
  spectral_centroid_hz: number | null;
  spectral_rolloff_hz: number | null;
  spectral_flatness: number | null;
  energy_db: number | null;
  stereo_width_percent: number | null;
  phase_correlation: number | null;
  mid_energy_db: number | null;
  side_energy_db: number | null;
  thd_percent: number | null;
  harmonic_ratio: number | null;
  inharmonicity: number | null;
  transient_preservation: number | null;
  attack_time_ms: number | null;
}

export interface OverallMetricResponse {
  id: string;
  integrated_lufs: number | null;
  loudness_range_lu: number | null;
  true_peak_dbfs: number | null;
  dynamic_range_db: number | null;
  crest_factor_db: number | null;
  avg_stereo_width_percent: number | null;
  avg_phase_correlation: number | null;
  spectral_centroid_hz: number | null;
  spectral_bandwidth_hz: number | null;
  warnings: string | null;
}

export interface RecommendationResponse {
  id: string;
  band_name: string | null;
  metric_category: string | null;
  severity: string | null;
  recommendation_text: string | null;
  analytical_text: string | null;
  suggestive_text: string | null;
  prescriptive_text: string | null;
  created_at: string;
}

export interface AnalysisResponse {
  id: string;
  file_path: string;
  file_name: string;
  file_size: number | null;
  sample_rate: number | null;
  bit_depth: number | null;
  duration_seconds: number | null;
  genre: string | null;
  genre_confidence: number | null;
  recommendation_level: string;
  analysis_engine_version: string | null;
  created_at: string;
  updated_at: string;
  band_metrics: BandMetricResponse[];
  overall_metrics: OverallMetricResponse | null;
  recommendations: RecommendationResponse[];
  warnings: string[] | null;
}

export interface ReferenceTrackResponse {
  id: string;
  track_name: string;
  artist: string | null;
  genre: string | null;
  year: number | null;
  is_builtin: boolean;
  created_at: string;
}

export interface SimilarityMatchResponse {
  reference_id: string;
  track_name: string;
  artist: string | null;
  genre: string | null;
  year: number | null;
  similarity_score: number;
}

export interface SimilaritySearchResponse {
  matches: SimilarityMatchResponse[];
}

export interface ComparisonResponse {
  user_analysis: AnalysisResponse;
  reference_track: ReferenceTrackResponse;
  reference_band_metrics: BandMetricResponse[];
  reference_overall_metrics: OverallMetricResponse | null;
  recommendations: RecommendationResponse[];
  comparison_mode: string;
}
