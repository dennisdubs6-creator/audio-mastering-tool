import React from 'react';
import type { RecommendationResponse } from '@/api/types';
import type { ComparisonMode, RecommendationLevelOption } from '@/store/types';
import type { MetricCardData, MetricCategory, BandData } from './types';
import MetricCard from './MetricCard/MetricCard';

interface ComparisonCardData {
  referenceBands: BandData[];
  recommendations: RecommendationResponse[];
}

interface MetricCardsGridProps {
  cards: MetricCardData[];
  onToggleExpand: (category: MetricCategory) => void;
  comparisonMode?: ComparisonMode | null;
  comparisonDataByCategory?: Record<string, ComparisonCardData>;
  recommendationLevel?: RecommendationLevelOption;
}

const MetricCardsGrid: React.FC<MetricCardsGridProps> = ({
  cards,
  onToggleExpand,
  comparisonMode,
  comparisonDataByCategory,
  recommendationLevel,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {cards.map((card) => {
        const compData = comparisonDataByCategory?.[card.category];
        return (
          <MetricCard
            key={card.category}
            card={card}
            onToggleExpand={() => onToggleExpand(card.category)}
            comparisonMode={comparisonMode}
            referenceBands={compData?.referenceBands}
            comparisonRecommendations={compData?.recommendations}
            recommendationLevel={recommendationLevel}
          />
        );
      })}
    </div>
  );
};

export default MetricCardsGrid;
