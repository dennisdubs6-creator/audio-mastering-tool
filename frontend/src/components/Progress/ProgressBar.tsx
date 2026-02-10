import React from 'react';

interface ProgressBarProps {
  percent: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ percent }) => {
  const clamped = Math.min(100, Math.max(0, percent));
  const isComplete = clamped >= 100;

  return (
    <div className="w-full">
      <div className="relative w-full h-3 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${
            isComplete ? 'bg-green-500' : 'bg-blue-500'
          }`}
          style={{ width: `${clamped}%` }}
        />
      </div>
      <div className="text-right mt-1">
        <span className="text-xs text-slate-400">{Math.round(clamped)}%</span>
      </div>
    </div>
  );
};

export default ProgressBar;
