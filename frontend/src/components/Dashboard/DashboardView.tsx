import React from 'react';
import { useAppSelector, useAppDispatch } from '@/store';
import { toggleCardExpansion } from '@/store/slices/uiSlice';
import type { MetricCategory } from './types';
import { mapAnalysisToCards } from './dataMapper';
import { orderCardsBySeverity } from '@/utils/cardOrdering';
import DashboardHeader from './DashboardHeader';
import MetricCardsGrid from './MetricCardsGrid';

interface DashboardViewProps {
  analysisId: string | null;
  fileName?: string;
  onAnalyzeAnother: () => void;
}

const DashboardView: React.FC<DashboardViewProps> = ({
  onAnalyzeAnother,
}) => {
  const results = useAppSelector((state) => state.analysis.results);
  const expandedCards = useAppSelector((state) => state.ui.expandedCards);
  const dispatch = useAppDispatch();

  if (!results) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        No analysis results available
      </div>
    );
  }

  const cards = mapAnalysisToCards(results, expandedCards);
  const sortedCards = orderCardsBySeverity(cards);

  const handleToggleExpand = (category: MetricCategory) => {
    dispatch(toggleCardExpansion(category));
  };

  return (
    <div className="flex flex-col h-full p-8 overflow-y-auto">
      <div className="max-w-6xl w-full mx-auto flex flex-col gap-8">
        <DashboardHeader results={results} onAnalyzeAnother={onAnalyzeAnother} />
        <MetricCardsGrid cards={sortedCards} onToggleExpand={handleToggleExpand} />
      </div>
    </div>
  );
};

export default DashboardView;
