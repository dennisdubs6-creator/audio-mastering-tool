import React from 'react';
import type { RecommendationLevelOption } from '@/store/types';

const LEVELS: { value: RecommendationLevelOption; label: string; description: string }[] = [
  {
    value: 'analytical',
    label: 'Analytical',
    description: 'Data-driven observations and metrics only.',
  },
  {
    value: 'suggestive',
    label: 'Suggestive',
    description: 'Highlights differences with gentle recommendations.',
  },
  {
    value: 'prescriptive',
    label: 'Prescriptive',
    description: 'Specific, actionable mastering instructions.',
  },
];

interface RecommendationLevelProps {
  value: RecommendationLevelOption;
  onChange: (level: RecommendationLevelOption) => void;
}

const RecommendationLevel: React.FC<RecommendationLevelProps> = ({ value, onChange }) => {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-slate-300">Recommendation Level</label>
      <div className="flex flex-col gap-2">
        {LEVELS.map((level) => (
          <label
            key={level.value}
            className={`flex items-start gap-3 p-3 rounded-md border cursor-pointer transition-colors ${
              value === level.value
                ? 'border-blue-500 bg-blue-500/10'
                : 'border-slate-700 hover:border-slate-500'
            }`}
          >
            <input
              type="radio"
              name="recommendationLevel"
              value={level.value}
              checked={value === level.value}
              onChange={() => onChange(level.value)}
              className="mt-0.5 accent-blue-500"
            />
            <div>
              <span className="text-sm font-medium text-slate-200">{level.label}</span>
              <p className="text-xs text-slate-400 mt-0.5">{level.description}</p>
            </div>
          </label>
        ))}
      </div>
    </div>
  );
};

export default RecommendationLevel;
