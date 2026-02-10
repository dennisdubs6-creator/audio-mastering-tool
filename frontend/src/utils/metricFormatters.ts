export function formatDb(value: number | null): string {
  if (value === null || value === undefined) return 'N/A';
  return `${value.toFixed(1)} dB`;
}

export function formatLufs(value: number | null): string {
  if (value === null || value === undefined) return 'N/A';
  return `${value.toFixed(1)} LUFS`;
}

export function formatLu(value: number | null): string {
  if (value === null || value === undefined) return 'N/A';
  return `${value.toFixed(1)} LU`;
}

export function formatHz(value: number | null): string {
  if (value === null || value === undefined) return 'N/A';
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)} kHz`;
  }
  return `${value.toFixed(0)} Hz`;
}

export function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return 'N/A';
  return `${value.toFixed(1)}%`;
}

export function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return 'N/A';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function formatDecimal(value: number | null, places: number = 2): string {
  if (value === null || value === undefined) return 'N/A';
  return value.toFixed(places);
}

export function formatMs(value: number | null): string {
  if (value === null || value === undefined) return 'N/A';
  return `${value.toFixed(1)} ms`;
}

export function formatBandValue(value: number, unit: string): string {
  switch (unit) {
    case 'dBFS':
      return formatDb(value).replace('dB', 'dBFS');
    case 'dB':
      return formatDb(value);
    case '%':
      return formatPercent(value);
    case 'Hz':
      return formatHz(value);
    case 'ms':
      return formatMs(value);
    case '':
      return value.toFixed(1);
    default:
      return value.toFixed(2);
  }
}

export function formatBandNumeric(value: number, unit: string): string {
  switch (unit) {
    case 'dBFS':
    case 'dB':
    case '%':
    case '':
    case 'ms':
      return value.toFixed(1);
    case 'Hz':
      return Math.round(value).toString();
    default:
      return value.toFixed(2);
  }
}
