export const BAND_COLORS: Record<string, string> = {
  low: '#3b82f6',
  low_mid: '#10b981',
  mid: '#f59e0b',
  high_mid: '#ef4444',
  high: '#8b5cf6',
};

export const BAND_DISPLAY_NAMES: Record<string, string> = {
  low: 'Low',
  low_mid: 'Low Mid',
  mid: 'Mid',
  high_mid: 'High Mid',
  high: 'High',
};

export function getBandColor(bandName: string): string {
  const normalized = bandName.toLowerCase().replace(/[\s-]/g, '_');
  return BAND_COLORS[normalized] || '#6b7280';
}

export function getBandDisplayName(bandName: string): string {
  const normalized = bandName.toLowerCase().replace(/[\s-]/g, '_');
  return BAND_DISPLAY_NAMES[normalized] || bandName;
}
