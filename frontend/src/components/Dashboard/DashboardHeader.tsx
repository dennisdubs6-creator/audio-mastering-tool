import React from 'react';
import type { AnalysisResponse, ReferenceTrackResponse } from '@/api/types';
import type { ComparisonMode, RecommendationLevelOption } from '@/store/types';
import Button from '@/components/common/Button';
import ComparisonModeSwitch from '@/components/Comparison/ComparisonModeSwitch';
import RecommendationLevelToggle from '@/components/Recommendations/RecommendationLevelToggle';
import { formatDuration, formatHz } from '@/utils/metricFormatters';

interface DashboardHeaderProps {
  results: AnalysisResponse;
  onAnalyzeAnother: () => void;
  onFindSimilar?: () => void;
  selectedReference?: ReferenceTrackResponse | null;
  onClearReference?: () => void;
  comparisonMode?: ComparisonMode;
  onComparisonModeChange?: (mode: ComparisonMode) => void;
  recommendationLevel?: RecommendationLevelOption;
  onRecommendationLevelChange?: (level: RecommendationLevelOption) => void;
}

const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  results,
  onAnalyzeAnother,
  onFindSimilar,
  selectedReference,
  onClearReference,
  comparisonMode,
  onComparisonModeChange,
  recommendationLevel,
  onRecommendationLevelChange,
}) => {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-200">
            {results.file_name}
          </h1>
          <div className="flex items-center gap-4 mt-2 text-sm text-slate-400">
            {results.sample_rate && (
              <span>{formatHz(results.sample_rate)}</span>
            )}
            {results.bit_depth && (
              <span>{results.bit_depth}-bit</span>
            )}
            {results.duration_seconds !== null && (
              <span>{formatDuration(results.duration_seconds)}</span>
            )}
            {results.genre && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-900/50 text-blue-300 border border-blue-700/50">
                {results.genre}
                {results.genre_confidence !== null && (
                  <span className="ml-1 text-blue-400/70">
                    ({(results.genre_confidence * 100).toFixed(0)}%)
                  </span>
                )}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {onFindSimilar && (
            <Button variant="secondary" onClick={onFindSimilar}>
              Find Similar Tracks
            </Button>
          )}
          <Button variant="primary" onClick={onAnalyzeAnother}>
            New Analysis
          </Button>
        </div>
      </div>

      {selectedReference && (
        <div className="flex items-center justify-between bg-slate-800/60 rounded-lg px-4 py-3 border border-slate-700">
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500 uppercase tracking-wider">Comparing with</span>
            <span className="text-sm font-medium text-green-400">
              {selectedReference.track_name}
            </span>
            {selectedReference.artist && (
              <span className="text-sm text-slate-400">
                by {selectedReference.artist}
              </span>
            )}
            <button
              onClick={onClearReference}
              className="ml-2 text-slate-500 hover:text-slate-300 transition-colors"
              title="Clear reference"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="flex items-center gap-3">
            {recommendationLevel && onRecommendationLevelChange && (
              <RecommendationLevelToggle
                level={recommendationLevel}
                onChange={onRecommendationLevelChange}
              />
            )}
            {comparisonMode && onComparisonModeChange && (
              <ComparisonModeSwitch
                mode={comparisonMode}
                onChange={onComparisonModeChange}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardHeader;
