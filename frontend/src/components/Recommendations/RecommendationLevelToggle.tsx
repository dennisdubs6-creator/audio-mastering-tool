import React from 'react';
import type { RecommendationLevelOption } from '@/store/types';

interface RecommendationLevelToggleProps {
  level: RecommendationLevelOption;
  onChange: (level: RecommendationLevelOption) => void;
}

const levels: { value: RecommendationLevelOption; label: string; title: string }[] = [
  { value: 'analytical', label: 'Analytical', title: 'Raw metric deltas and measurements' },
  { value: 'suggestive', label: 'Suggestive', title: 'Gentle suggestions for improvement' },
  { value: 'prescriptive', label: 'Prescriptive', title: 'Specific actions with tools and values' },
];

const RecommendationLevelToggle: React.FC<RecommendationLevelToggleProps> = ({
  level,
  onChange,
}) => {
  return (
    <div className="flex items-center bg-slate-800 rounded-lg p-1">
      {levels.map((l) => (
        <button
          key={l.value}
          onClick={() => onChange(l.value)}
          title={l.title}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            level === l.value
              ? 'bg-blue-600 text-white'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
};

export default RecommendationLevelToggle;
