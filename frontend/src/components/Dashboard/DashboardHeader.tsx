import React from 'react';
import type { AnalysisResponse } from '@/api/types';
import Button from '@/components/common/Button';
import { formatDuration, formatHz } from '@/utils/metricFormatters';

interface DashboardHeaderProps {
  results: AnalysisResponse;
  onAnalyzeAnother: () => void;
}

const DashboardHeader: React.FC<DashboardHeaderProps> = ({ results, onAnalyzeAnother }) => {
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
          <Button variant="primary" onClick={onAnalyzeAnother}>
            New Analysis
          </Button>
        </div>
      </div>
    </div>
  );
};

export default DashboardHeader;
