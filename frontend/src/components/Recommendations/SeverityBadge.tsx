import React from 'react';

interface SeverityBadgeProps {
  severity: 'info' | 'attention' | 'issue';
}

const SEVERITY_CONFIG: Record<string, { color: string; icon: string; title: string }> = {
  info: {
    color: 'text-blue-400 bg-blue-900/40',
    icon: '\u24D8',
    title: 'Minor difference from reference',
  },
  attention: {
    color: 'text-orange-400 bg-orange-900/40',
    icon: '\u26A0',
    title: 'Notable difference from reference',
  },
  issue: {
    color: 'text-red-400 bg-red-900/40',
    icon: '\u2757',
    title: 'Significant difference from reference',
  },
};

const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity }) => {
  const config = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.info;

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium ${config.color}`}
      title={config.title}
    >
      <span>{config.icon}</span>
      {severity}
    </span>
  );
};

export default SeverityBadge;
