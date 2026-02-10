import React from 'react';

const BAND_LABELS: Record<string, string> = {
  low: 'Low',
  low_mid: 'Low Mid',
  mid: 'Mid',
  high_mid: 'High Mid',
  high: 'High',
};

interface StatusTextProps {
  currentBand: string | null;
  percent: number;
}

const StatusText: React.FC<StatusTextProps> = ({ currentBand, percent }) => {
  let text = 'Starting analysis...';
  if (percent >= 100) {
    text = 'Analysis complete';
  } else if (currentBand) {
    const label = BAND_LABELS[currentBand] || currentBand;
    text = `Analyzing ${label} (${Math.round(percent)}%)...`;
  }

  return (
    <div className="flex items-center gap-2 transition-opacity duration-300">
      {percent < 100 && (
        <div className="w-4 h-4 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin" />
      )}
      <span className="text-sm text-slate-300">{text}</span>
    </div>
  );
};

export default StatusText;
