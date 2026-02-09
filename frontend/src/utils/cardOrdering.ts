import type { MetricCardData, SeverityLevel } from '@/components/Dashboard/types';

const SEVERITY_ORDER: Record<SeverityLevel, number> = {
  issue: 0,
  attention: 1,
  good: 2,
};

export function orderCardsBySeverity(cards: MetricCardData[]): MetricCardData[] {
  return [...cards].sort((a, b) => {
    const severityDiff = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity];
    if (severityDiff !== 0) return severityDiff;
    return 0; // maintain original category order within same severity
  });
}
