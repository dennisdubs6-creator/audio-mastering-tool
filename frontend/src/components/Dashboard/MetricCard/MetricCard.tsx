import React from 'react';
import type { RecommendationResponse } from '@/api/types';
import type { ComparisonMode, RecommendationLevelOption } from '@/store/types';
import type { MetricCardData, SeverityLevel, BandData } from '../types';
import CardHeader from './CardHeader';
import BandBarChart from './BandBarChart';
import InlineRecommendation from './InlineRecommendation';
import ExpandedView from './ExpandedView';
import SideBySideView from '@/components/Comparison/SideBySideView';
import OverlayView from '@/components/Comparison/OverlayView';
import DifferenceView from '@/components/Comparison/DifferenceView';

interface MetricCardProps {
  card: MetricCardData;
  onToggleExpand: () => void;
  comparisonMode?: ComparisonMode | null;
  referenceBands?: BandData[] | null;
  comparisonRecommendations?: RecommendationResponse[];
  recommendationLevel?: RecommendationLevelOption;
}

const SEVERITY_BORDER: Record<SeverityLevel, string> = {
  good: 'border-l-4 border-l-green-500',
  attention: 'border-l-4 border-l-orange-500',
  issue: 'border-l-4 border-l-red-500',
};

const MetricCard: React.FC<MetricCardProps> = ({
  card,
  onToggleExpand,
  comparisonMode,
  referenceBands,
  comparisonRecommendations,
  recommendationLevel,
}) => {
  const isComparing = comparisonMode && referenceBands && referenceBands.length > 0;

  const renderChart = () => {
    if (!isComparing) {
      return <BandBarChart bands={card.bands} height={180} />;
    }

    switch (comparisonMode) {
      case 'side-by-side':
        return (
          <SideBySideView
            userBands={card.bands}
            referenceBands={referenceBands!}
            height={180}
          />
        );
      case 'overlay':
        return (
          <OverlayView
            userBands={card.bands}
            referenceBands={referenceBands!}
            height={180}
          />
        );
      case 'difference':
        return (
          <DifferenceView
            userBands={card.bands}
            referenceBands={referenceBands!}
            height={180}
          />
        );
      default:
        return <BandBarChart bands={card.bands} height={180} />;
    }
  };

  return (
    <div
      role="region"
      aria-labelledby={`card-title-${card.category}`}
      className={`bg-slate-800 rounded-lg shadow-md hover:shadow-lg transition-shadow p-6 ${SEVERITY_BORDER[card.severity]} ${card.expanded ? 'lg:col-span-3 md:col-span-2' : ''}`}
    >
      <CardHeader title={card.title} severity={card.severity} />

      <div className="mb-4">
        <p className="text-3xl font-bold text-slate-100">{card.primaryValue}</p>
        <p className="text-sm text-slate-400 mt-1">{card.primaryLabel}</p>
      </div>

      {card.secondaryValue && (
        <div className="mb-4">
          <p className="text-lg text-slate-300">{card.secondaryValue}</p>
          <p className="text-xs text-slate-500">{card.secondaryLabel}</p>
        </div>
      )}

      {!card.expanded && renderChart()}

      <InlineRecommendation
        text={card.recommendation}
        recommendations={comparisonRecommendations}
        level={recommendationLevel}
      />

      <button
        onClick={onToggleExpand}
        aria-expanded={card.expanded}
        className="mt-4 w-full text-sm text-blue-400 hover:text-blue-300 transition-colors py-2 rounded-md hover:bg-slate-700/50"
      >
        {card.expanded ? 'Show Less' : 'Show Details'}
      </button>

      {card.expanded && <ExpandedView card={card} />}
    </div>
  );
};

export default MetricCard;
