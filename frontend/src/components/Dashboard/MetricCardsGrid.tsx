import React from 'react';
import type { MetricCardData, MetricCategory } from './types';
import MetricCard from './MetricCard/MetricCard';

interface MetricCardsGridProps {
  cards: MetricCardData[];
  onToggleExpand: (category: MetricCategory) => void;
}

const MetricCardsGrid: React.FC<MetricCardsGridProps> = ({ cards, onToggleExpand }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {cards.map((card) => (
        <MetricCard
          key={card.category}
          card={card}
          onToggleExpand={() => onToggleExpand(card.category)}
        />
      ))}
    </div>
  );
};

export default MetricCardsGrid;
