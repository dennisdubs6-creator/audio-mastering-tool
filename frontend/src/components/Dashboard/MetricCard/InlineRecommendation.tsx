import React from 'react';

interface InlineRecommendationProps {
  text: string | null;
}

const InlineRecommendation: React.FC<InlineRecommendationProps> = ({ text }) => {
  if (!text) return null;

  return (
    <div className="bg-slate-700/50 p-3 rounded-md mt-4">
      <p className="text-sm text-slate-300 leading-relaxed">{text}</p>
    </div>
  );
};

export default InlineRecommendation;
