import React from 'react';
import type { SimilarityMatchResponse } from '@/api/types';
import SimilarityScore from './SimilarityScore';

interface ReferenceCardProps {
  reference: SimilarityMatchResponse;
  isSelected: boolean;
  onSelect: () => void;
}

const ReferenceCard: React.FC<ReferenceCardProps> = ({
  reference,
  isSelected,
  onSelect,
}) => {
  return (
    <button
      onClick={onSelect}
      className={`w-full text-left p-3 rounded-lg transition-colors ${
        isSelected
          ? 'bg-blue-900/50 border border-blue-500'
          : 'bg-slate-800 border border-slate-700 hover:border-slate-600'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-200 truncate">
            {reference.track_name}
          </p>
          <p className="text-xs text-slate-400 truncate">
            {reference.artist || 'Unknown Artist'}
          </p>
          {reference.genre && (
            <span className="inline-block mt-1 px-2 py-0.5 text-xs rounded-full bg-slate-700 text-slate-300">
              {reference.genre}
            </span>
          )}
        </div>
        <div className="ml-3 flex-shrink-0">
          <SimilarityScore score={reference.similarity_score} />
        </div>
      </div>
    </button>
  );
};

export default ReferenceCard;
