import React from 'react';
import type { RecommendationResponse } from '@/api/types';
import type { RecommendationLevelOption } from '@/store/types';
import SeverityBadge from '@/components/Recommendations/SeverityBadge';

interface InlineRecommendationProps {
  text: string | null;
  recommendations?: RecommendationResponse[];
  level?: RecommendationLevelOption;
}

function getTextForLevel(rec: RecommendationResponse, level: RecommendationLevelOption): string | null {
  if (level === 'analytical' && rec.analytical_text) return rec.analytical_text;
  if (level === 'suggestive' && rec.suggestive_text) return rec.suggestive_text;
  if (level === 'prescriptive' && rec.prescriptive_text) return rec.prescriptive_text;
  return rec.recommendation_text || null;
}

const InlineRecommendation: React.FC<InlineRecommendationProps> = ({
  text,
  recommendations,
  level,
}) => {
  // Comparison-aware mode with multiple recommendations
  if (recommendations && recommendations.length > 0 && level) {
    return (
      <div className="space-y-2 mt-4">
        {recommendations.map((rec) => {
          const recText = getTextForLevel(rec, level);
          if (!recText) return null;
          const severity = (rec.severity as 'info' | 'attention' | 'issue') || 'info';
          return (
            <div key={rec.id} className="bg-slate-700/50 p-3 rounded-md flex items-start gap-2">
              <SeverityBadge severity={severity} />
              <p className="text-sm text-slate-300 leading-relaxed flex-1">{recText}</p>
            </div>
          );
        })}
      </div>
    );
  }

  // Legacy single-text mode
  if (!text) return null;

  return (
    <div className="bg-slate-700/50 p-3 rounded-md mt-4">
      <p className="text-sm text-slate-300 leading-relaxed">{text}</p>
    </div>
  );
};

export default InlineRecommendation;
