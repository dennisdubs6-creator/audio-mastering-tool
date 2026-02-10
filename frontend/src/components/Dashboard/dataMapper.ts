import type { AnalysisResponse, BandMetricResponse, ComparisonResponse, RecommendationResponse } from '@/api/types';
import type { MetricCardData, SeverityLevel, BandData } from './types';
import { getBandColor, getBandDisplayName } from '@/utils/bandColors';
import {
  formatLufs,
  formatLu,
  formatDb,
  formatHz,
  formatPercent,
  formatDecimal,
  formatMs,
} from '@/utils/metricFormatters';

const BAND_ORDER = ['low', 'low_mid', 'mid', 'high_mid', 'high'];

function sortBands(bands: BandMetricResponse[]): BandMetricResponse[] {
  return [...bands].sort((a, b) => {
    const aIdx = BAND_ORDER.indexOf(a.band_name.toLowerCase().replace(/[\s-]/g, '_'));
    const bIdx = BAND_ORDER.indexOf(b.band_name.toLowerCase().replace(/[\s-]/g, '_'));
    return aIdx - bIdx;
  });
}

function findRecommendation(
  recommendations: RecommendationResponse[],
  category: string
): RecommendationResponse | undefined {
  return recommendations.find(
    (r) => r.metric_category?.toLowerCase() === category.toLowerCase()
  );
}

function getRecommendationText(
  rec: RecommendationResponse | undefined,
  level: string
): string | null {
  if (!rec) return null;
  const normalized = level.toLowerCase();
  if (normalized === 'prescriptive' && rec.prescriptive_text) return rec.prescriptive_text;
  if (normalized === 'suggestive' && rec.suggestive_text) return rec.suggestive_text;
  if (normalized === 'analytical' && rec.analytical_text) return rec.analytical_text;
  return rec.recommendation_text || null;
}

function recSeverityToLevel(severity: string | null): SeverityLevel {
  if (!severity) return 'good';
  const s = severity.toLowerCase();
  if (s === 'issue' || s === 'critical' || s === 'high') return 'issue';
  if (s === 'attention' || s === 'warning' || s === 'medium') return 'attention';
  return 'good';
}

function mapLoudness(
  results: AnalysisResponse,
  expanded: boolean
): MetricCardData {
  const overall = results.overall_metrics;
  const sorted = sortBands(results.band_metrics);
  const rec = findRecommendation(results.recommendations, 'loudness');

  let severity: SeverityLevel = 'good';
  if (rec) {
    severity = recSeverityToLevel(rec.severity);
  } else if (overall?.integrated_lufs !== null && overall?.integrated_lufs !== undefined) {
    const lufs = overall.integrated_lufs;
    if (lufs > -6 || lufs < -16) severity = 'issue';
    else if (lufs > -8 || lufs < -14) severity = 'attention';
  }

  return {
    category: 'loudness',
    title: 'Loudness',
    severity,
    primaryValue: formatLufs(overall?.integrated_lufs ?? null),
    primaryLabel: 'Integrated Loudness',
    secondaryValue: formatLu(overall?.loudness_range_lu ?? null),
    secondaryLabel: 'Loudness Range',
    bands: sorted.map((b) => ({
      bandName: getBandDisplayName(b.band_name),
      value: b.band_rms_dbfs ?? 0,
      unit: 'dBFS',
      color: getBandColor(b.band_name),
    })),
    recommendation: getRecommendationText(rec, results.recommendation_level),
    expanded,
  };
}

function mapDynamics(
  results: AnalysisResponse,
  expanded: boolean
): MetricCardData {
  const overall = results.overall_metrics;
  const sorted = sortBands(results.band_metrics);
  const rec = findRecommendation(results.recommendations, 'dynamics');

  let severity: SeverityLevel = 'good';
  if (rec) {
    severity = recSeverityToLevel(rec.severity);
  } else if (overall?.dynamic_range_db !== null && overall?.dynamic_range_db !== undefined) {
    const dr = overall.dynamic_range_db;
    if (dr < 4 || dr > 20) severity = 'issue';
    else if (dr < 6 || dr > 16) severity = 'attention';
  }

  return {
    category: 'dynamics',
    title: 'Dynamics',
    severity,
    primaryValue: overall?.dynamic_range_db !== null && overall?.dynamic_range_db !== undefined
      ? `${overall.dynamic_range_db.toFixed(1)} DR`
      : 'N/A',
    primaryLabel: 'Dynamic Range',
    secondaryValue: formatDb(overall?.crest_factor_db ?? null),
    secondaryLabel: 'Crest Factor',
    bands: sorted.map((b) => ({
      bandName: getBandDisplayName(b.band_name),
      value: b.dynamic_range_db ?? 0,
      unit: 'dB',
      color: getBandColor(b.band_name),
    })),
    recommendation: getRecommendationText(rec, results.recommendation_level),
    expanded,
  };
}

function mapFrequency(
  results: AnalysisResponse,
  expanded: boolean
): MetricCardData {
  const overall = results.overall_metrics;
  const sorted = sortBands(results.band_metrics);
  const rec = findRecommendation(results.recommendations, 'frequency');

  const energyValues = sorted
    .map((b) => b.energy_db)
    .filter((v): v is number => v !== null);

  let balanceLabel = 'N/A';
  let severity: SeverityLevel = 'good';

  if (rec) {
    severity = recSeverityToLevel(rec.severity);
  }

  if (energyValues.length > 0) {
    const mean = energyValues.reduce((a, b) => a + b, 0) / energyValues.length;
    const variance = energyValues.reduce((a, b) => a + (b - mean) ** 2, 0) / energyValues.length;
    const stdDev = Math.sqrt(variance);
    if (stdDev < 3) balanceLabel = 'Balanced';
    else if (stdDev < 6) {
      balanceLabel = 'Slightly Imbalanced';
      if (!rec) severity = 'attention';
    } else {
      balanceLabel = 'Imbalanced';
      if (!rec) severity = 'issue';
    }
  }

  return {
    category: 'frequency',
    title: 'Frequency Balance',
    severity,
    primaryValue: balanceLabel,
    primaryLabel: 'Spectral Balance',
    secondaryValue: formatHz(overall?.spectral_centroid_hz ?? null),
    secondaryLabel: 'Spectral Centroid',
    bands: sorted.map((b) => ({
      bandName: getBandDisplayName(b.band_name),
      value: b.energy_db ?? 0,
      unit: 'dB',
      color: getBandColor(b.band_name),
    })),
    recommendation: getRecommendationText(rec, results.recommendation_level),
    expanded,
  };
}

function mapStereo(
  results: AnalysisResponse,
  expanded: boolean
): MetricCardData {
  const overall = results.overall_metrics;
  const sorted = sortBands(results.band_metrics);
  const rec = findRecommendation(results.recommendations, 'stereo');

  let severity: SeverityLevel = 'good';
  if (rec) {
    severity = recSeverityToLevel(rec.severity);
  } else if (overall?.avg_stereo_width_percent !== null && overall?.avg_stereo_width_percent !== undefined) {
    const width = overall.avg_stereo_width_percent;
    if (width < 20 || width > 95) severity = 'issue';
    else if (width < 40 || width > 90) severity = 'attention';
  }

  return {
    category: 'stereo',
    title: 'Stereo Image',
    severity,
    primaryValue: formatPercent(overall?.avg_stereo_width_percent ?? null),
    primaryLabel: 'Stereo Width',
    secondaryValue: formatDecimal(overall?.avg_phase_correlation ?? null),
    secondaryLabel: 'Phase Correlation',
    bands: sorted.map((b) => ({
      bandName: getBandDisplayName(b.band_name),
      value: b.stereo_width_percent ?? 0,
      unit: '%',
      color: getBandColor(b.band_name),
    })),
    recommendation: getRecommendationText(rec, results.recommendation_level),
    expanded,
  };
}

function mapHarmonics(
  results: AnalysisResponse,
  expanded: boolean
): MetricCardData {
  const sorted = sortBands(results.band_metrics);
  const rec = findRecommendation(results.recommendations, 'harmonics');

  const thdValues = sorted
    .map((b) => b.thd_percent)
    .filter((v): v is number => v !== null);
  const avgThd = thdValues.length > 0
    ? thdValues.reduce((a, b) => a + b, 0) / thdValues.length
    : null;

  const ratioValues = sorted
    .map((b) => b.harmonic_ratio)
    .filter((v): v is number => v !== null);
  const avgRatio = ratioValues.length > 0
    ? ratioValues.reduce((a, b) => a + b, 0) / ratioValues.length
    : null;

  let severity: SeverityLevel = 'good';
  if (rec) {
    severity = recSeverityToLevel(rec.severity);
  } else if (avgThd !== null) {
    if (avgThd > 5) severity = 'issue';
    else if (avgThd > 3) severity = 'attention';
  }

  return {
    category: 'harmonics',
    title: 'Harmonics',
    severity,
    primaryValue: formatPercent(avgThd),
    primaryLabel: 'Average THD',
    secondaryValue: formatDecimal(avgRatio),
    secondaryLabel: 'Harmonic Ratio',
    bands: sorted.map((b) => ({
      bandName: getBandDisplayName(b.band_name),
      value: b.thd_percent ?? 0,
      unit: '%',
      color: getBandColor(b.band_name),
    })),
    recommendation: getRecommendationText(rec, results.recommendation_level),
    expanded,
  };
}

function mapTransients(
  results: AnalysisResponse,
  expanded: boolean
): MetricCardData {
  const sorted = sortBands(results.band_metrics);
  const rec = findRecommendation(results.recommendations, 'transients');

  const presValues = sorted
    .map((b) => b.transient_preservation)
    .filter((v): v is number => v !== null);
  const avgPres = presValues.length > 0
    ? presValues.reduce((a, b) => a + b, 0) / presValues.length
    : null;

  const attackValues = sorted
    .map((b) => b.attack_time_ms)
    .filter((v): v is number => v !== null);
  const avgAttack = attackValues.length > 0
    ? attackValues.reduce((a, b) => a + b, 0) / attackValues.length
    : null;

  let severity: SeverityLevel = 'good';
  if (rec) {
    severity = recSeverityToLevel(rec.severity);
  } else if (avgPres !== null) {
    if (avgPres < 0.5) severity = 'issue';
    else if (avgPres < 0.7) severity = 'attention';
  }

  return {
    category: 'transients',
    title: 'Transients',
    severity,
    primaryValue: formatDecimal(avgPres),
    primaryLabel: 'Transient Preservation',
    secondaryValue: formatMs(avgAttack),
    secondaryLabel: 'Avg Attack Time',
    bands: sorted.map((b) => ({
      bandName: getBandDisplayName(b.band_name),
      value: b.transient_preservation ?? 0,
      unit: '',
      color: getBandColor(b.band_name),
    })),
    recommendation: getRecommendationText(rec, results.recommendation_level),
    expanded,
  };
}

export function mapAnalysisToCards(
  results: AnalysisResponse,
  expandedCards: string[]
): MetricCardData[] {
  return [
    mapLoudness(results, expandedCards.includes('loudness')),
    mapDynamics(results, expandedCards.includes('dynamics')),
    mapFrequency(results, expandedCards.includes('frequency')),
    mapStereo(results, expandedCards.includes('stereo')),
    mapHarmonics(results, expandedCards.includes('harmonics')),
    mapTransients(results, expandedCards.includes('transients')),
  ];
}

interface ComparisonCardData {
  referenceBands: BandData[];
  recommendations: RecommendationResponse[];
}

export function mapComparisonToCardData(
  comparisonData: ComparisonResponse | null
): Record<string, ComparisonCardData> | undefined {
  if (!comparisonData) return undefined;

  const refBands = sortBands(comparisonData.reference_band_metrics);
  const recommendations = comparisonData.recommendations;

  const categoryMetricMap: Record<string, (b: BandMetricResponse) => number> = {
    loudness: (b) => b.band_rms_dbfs ?? 0,
    dynamics: (b) => b.dynamic_range_db ?? 0,
    frequency: (b) => b.energy_db ?? 0,
    stereo: (b) => b.stereo_width_percent ?? 0,
    harmonics: (b) => b.thd_percent ?? 0,
    transients: (b) => b.transient_preservation ?? 0,
  };

  const categoryUnits: Record<string, string> = {
    loudness: 'dBFS',
    dynamics: 'dB',
    frequency: 'dB',
    stereo: '%',
    harmonics: '%',
    transients: '',
  };

  // Map metric_category from recommendations to card categories
  const recCategoryMap: Record<string, string> = {
    loudness: 'loudness',
    frequency: 'frequency',
    dynamic_range: 'dynamics',
    stereo_width: 'stereo',
    integrated_lufs: 'loudness',
    dynamic_range_db: 'dynamics',
    true_peak_dbfs: 'loudness',
    avg_stereo_width_percent: 'stereo',
  };

  const result: Record<string, ComparisonCardData> = {};

  for (const category of Object.keys(categoryMetricMap)) {
    const metricFn = categoryMetricMap[category];
    const unit = categoryUnits[category];

    const bands: BandData[] = refBands.map((b) => ({
      bandName: getBandDisplayName(b.band_name),
      value: metricFn(b),
      unit,
      color: getBandColor(b.band_name),
    }));

    const categoryRecs = recommendations.filter((r) => {
      const mapped = recCategoryMap[r.metric_category || ''];
      return mapped === category;
    });

    result[category] = { referenceBands: bands, recommendations: categoryRecs };
  }

  return result;
}
