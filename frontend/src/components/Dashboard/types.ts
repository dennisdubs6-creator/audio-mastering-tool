export type MetricCategory = 'loudness' | 'dynamics' | 'frequency' | 'stereo' | 'harmonics' | 'transients';
export type SeverityLevel = 'good' | 'attention' | 'issue';

export interface BandData {
  bandName: string;
  value: number;
  unit: string;
  color: string;
}

export interface MetricCardData {
  category: MetricCategory;
  title: string;
  severity: SeverityLevel;
  primaryValue: string;
  primaryLabel: string;
  secondaryValue?: string;
  secondaryLabel?: string;
  bands: BandData[];
  recommendation: string | null;
  expanded: boolean;
}
