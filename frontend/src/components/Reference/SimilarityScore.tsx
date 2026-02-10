import React from 'react';

interface SimilarityScoreProps {
  score: number;
}

const SimilarityScore: React.FC<SimilarityScoreProps> = ({ score }) => {
  const percent = Math.round(score * 100);

  let colorClass: string;
  let bgClass: string;
  if (percent >= 90) {
    colorClass = 'text-green-400';
    bgClass = 'bg-green-500';
  } else if (percent >= 70) {
    colorClass = 'text-blue-400';
    bgClass = 'bg-blue-500';
  } else if (percent >= 50) {
    colorClass = 'text-yellow-400';
    bgClass = 'bg-yellow-500';
  } else {
    colorClass = 'text-slate-400';
    bgClass = 'bg-slate-500';
  }

  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${bgClass}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className={`text-xs font-medium ${colorClass}`}>{percent}%</span>
    </div>
  );
};

export default SimilarityScore;
