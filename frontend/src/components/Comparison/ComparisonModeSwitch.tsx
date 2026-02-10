import React from 'react';
import type { ComparisonMode } from '@/store/types';

interface ComparisonModeSwitchProps {
  mode: ComparisonMode;
  onChange: (mode: ComparisonMode) => void;
}

const modes: { value: ComparisonMode; label: string }[] = [
  { value: 'side-by-side', label: 'Side-by-Side' },
  { value: 'overlay', label: 'Overlay' },
  { value: 'difference', label: 'Difference' },
];

const ComparisonModeSwitch: React.FC<ComparisonModeSwitchProps> = ({
  mode,
  onChange,
}) => {
  return (
    <div className="flex items-center bg-slate-800 rounded-lg p-1">
      {modes.map((m) => (
        <button
          key={m.value}
          onClick={() => onChange(m.value)}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            mode === m.value
              ? 'bg-blue-600 text-white'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
};

export default ComparisonModeSwitch;
