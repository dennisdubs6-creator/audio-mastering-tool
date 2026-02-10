import React, { useState } from 'react';
import Button from '@/components/common/Button';
import GenreSelector from './GenreSelector';
import RecommendationLevel from './RecommendationLevel';
import type { RecommendationLevelOption, AnalysisSettings } from '@/store/types';

interface SettingsScreenProps {
  fileName: string;
  fileSize: number;
  onAnalyze: (settings: AnalysisSettings) => void;
  onCancel: () => void;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const SettingsScreen: React.FC<SettingsScreenProps> = ({
  fileName,
  fileSize,
  onAnalyze,
  onCancel,
}) => {
  const [genre, setGenre] = useState('');
  const [recLevel, setRecLevel] = useState<RecommendationLevelOption>('suggestive');

  const canAnalyze = genre !== '';

  const handleAnalyze = () => {
    if (!canAnalyze) return;
    onAnalyze({ genre, recommendationLevel: recLevel });
  };

  return (
    <div className="flex flex-col items-center justify-center h-full p-8">
      <div className="w-full max-w-md bg-slate-900 rounded-xl border border-slate-700 p-6">
        <h2 className="text-lg font-semibold text-slate-200 mb-1">Analysis Settings</h2>

        <div className="flex items-center gap-2 mb-6">
          <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13" />
          </svg>
          <span className="text-sm text-slate-400 truncate">{fileName}</span>
          <span className="text-xs text-slate-500">({formatFileSize(fileSize)})</span>
        </div>

        <div className="flex flex-col gap-5">
          <GenreSelector value={genre} onChange={setGenre} />
          <RecommendationLevel value={recLevel} onChange={setRecLevel} />
        </div>

        <div className="flex gap-3 mt-6">
          <Button variant="primary" onClick={handleAnalyze} disabled={!canAnalyze}>
            Analyze
          </Button>
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SettingsScreen;
