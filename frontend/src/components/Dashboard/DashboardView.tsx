import React, { useState, useCallback, useMemo } from 'react';
import { useAppSelector, useAppDispatch } from '@/store';
import { toggleCardExpansion } from '@/store/slices/uiSlice';
import {
  setSelectedReference,
  setComparisonMode,
  setComparisonData,
  clearReference,
  setSettings,
} from '@/store/slices/analysisSlice';
import type { ReferenceTrackResponse } from '@/api/types';
import type { AudioAnalysisAPI } from '@/api/client';
import type { MetricCategory } from './types';
import type { ComparisonMode, RecommendationLevelOption } from '@/store/types';
import { mapAnalysisToCards, mapComparisonToCardData } from './dataMapper';
import { orderCardsBySeverity } from '@/utils/cardOrdering';
import DashboardHeader from './DashboardHeader';
import MetricCardsGrid from './MetricCardsGrid';
import ReferenceSelectionModal from '@/components/Reference/ReferenceSelectionModal';

interface DashboardViewProps {
  analysisId: string | null;
  fileName?: string;
  onAnalyzeAnother: () => void;
  apiClient?: AudioAnalysisAPI | null;
  isBatchFile?: boolean;
}

const DashboardView: React.FC<DashboardViewProps> = ({
  analysisId,
  fileName,
  onAnalyzeAnother,
  apiClient,
  isBatchFile = false,
}) => {
  const results = useAppSelector((state) => state.analysis.results);
  const expandedCards = useAppSelector((state) => state.ui.expandedCards);
  const selectedReference = useAppSelector((state) => state.analysis.selectedReference);
  const comparisonMode = useAppSelector((state) => state.analysis.comparisonMode);
  const comparisonData = useAppSelector((state) => state.analysis.comparisonData);
  const settings = useAppSelector((state) => state.analysis.settings);
  const batchFiles = useAppSelector((state) => state.analysis.batchFiles);
  const dispatch = useAppDispatch();

  const [showReferenceModal, setShowReferenceModal] = useState(false);

  const recommendationLevel: RecommendationLevelOption =
    settings?.recommendationLevel || 'suggestive';

  if (!results) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        No analysis results available
      </div>
    );
  }

  const cards = mapAnalysisToCards(results, expandedCards);
  const sortedCards = orderCardsBySeverity(cards);
  const comparisonDataByCategory = mapComparisonToCardData(comparisonData);

  const handleToggleExpand = (category: MetricCategory) => {
    dispatch(toggleCardExpansion(category));
  };

  const handleFindSimilar = () => {
    setShowReferenceModal(true);
  };

  const handleSelectReference = async (ref: ReferenceTrackResponse) => {
    dispatch(setSelectedReference(ref));

    if (apiClient && analysisId) {
      try {
        const comparison = await apiClient.compareWithReference(
          analysisId,
          ref.id,
          recommendationLevel,
        );
        dispatch(setComparisonData(comparison));
      } catch (err) {
        console.error('Failed to fetch comparison data:', err);
      }
    }
  };

  const handleClearReference = () => {
    dispatch(clearReference());
  };

  const handleComparisonModeChange = (mode: ComparisonMode) => {
    dispatch(setComparisonMode(mode));
  };

  const handleRecommendationLevelChange = async (level: RecommendationLevelOption) => {
    const nextSettings = settings
      ? { ...settings, recommendationLevel: level }
      : {
          genre: results.genre ?? '',
          recommendationLevel: level,
        };

    dispatch(setSettings(nextSettings));

    if (apiClient && analysisId && selectedReference) {
      try {
        const comparison = await apiClient.compareWithReference(
          analysisId,
          selectedReference.id,
          level,
        );
        dispatch(setComparisonData(comparison));
      } catch (err) {
        console.error('Failed to fetch comparison data:', err);
      }
    }
  };

  return (
    <div className="flex flex-col h-full p-8 overflow-y-auto">
      <div className="max-w-6xl w-full mx-auto flex flex-col gap-8">
        {isBatchFile && batchFiles.length > 1 && (
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13" />
            </svg>
            <span>Viewing: {fileName || results.file_name}</span>
            <span className="text-slate-600">|</span>
            <span>Part of batch ({batchFiles.length} files)</span>
          </div>
        )}
        <DashboardHeader
          results={results}
          onAnalyzeAnother={onAnalyzeAnother}
          onFindSimilar={apiClient ? handleFindSimilar : undefined}
          selectedReference={selectedReference}
          onClearReference={handleClearReference}
          comparisonMode={comparisonMode}
          onComparisonModeChange={handleComparisonModeChange}
          recommendationLevel={recommendationLevel}
          onRecommendationLevelChange={handleRecommendationLevelChange}
        />
        <MetricCardsGrid
          cards={sortedCards}
          onToggleExpand={handleToggleExpand}
          comparisonMode={selectedReference ? comparisonMode : null}
          comparisonDataByCategory={comparisonDataByCategory}
          recommendationLevel={recommendationLevel}
        />
      </div>

      {apiClient && analysisId && (
        <ReferenceSelectionModal
          isOpen={showReferenceModal}
          onClose={() => setShowReferenceModal(false)}
          analysisId={analysisId}
          onSelectReference={handleSelectReference}
          apiClient={apiClient}
        />
      )}
    </div>
  );
};

export default DashboardView;
