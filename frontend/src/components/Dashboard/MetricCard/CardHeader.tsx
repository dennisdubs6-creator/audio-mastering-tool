import React from 'react';
import type { SeverityLevel } from '../types';

interface CardHeaderProps {
  title: string;
  severity: SeverityLevel;
}

const SEVERITY_CONFIG: Record<SeverityLevel, { icon: string; colorClass: string; label: string }> = {
  good: { icon: '✓', colorClass: 'text-green-500', label: 'Good' },
  attention: { icon: '⚠', colorClass: 'text-orange-500', label: 'Needs Attention' },
  issue: { icon: '✗', colorClass: 'text-red-500', label: 'Issue Detected' },
};

const CardHeader: React.FC<CardHeaderProps> = ({ title, severity }) => {
  const config = SEVERITY_CONFIG[severity];

  return (
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-semibold text-slate-200">{title}</h3>
      <span
        className={`${config.colorClass} text-lg font-bold`}
        aria-label={config.label}
        role="img"
      >
        {config.icon}
      </span>
    </div>
  );
};

export default CardHeader;
