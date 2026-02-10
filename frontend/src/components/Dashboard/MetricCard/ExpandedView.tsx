import React from 'react';
import type { MetricCardData } from '../types';
import BandBarChart from './BandBarChart';
import { formatBandNumeric } from '@/utils/metricFormatters';

interface ExpandedViewProps {
  card: MetricCardData;
}

const ExpandedView: React.FC<ExpandedViewProps> = ({ card }) => {
  return (
    <div className="mt-4 pt-4 border-t border-slate-700">
      <BandBarChart bands={card.bands} height={300} />

      {card.bands.length > 0 && (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="py-2 pr-4 text-slate-400 font-medium">Band</th>
                <th className="py-2 pr-4 text-slate-400 font-medium text-right">Value</th>
                <th className="py-2 text-slate-400 font-medium text-right">Unit</th>
              </tr>
            </thead>
            <tbody>
              {card.bands.map((band) => (
                <tr key={band.bandName} className="border-b border-slate-700/50">
                  <td className="py-2 pr-4">
                    <span className="flex items-center gap-2">
                      <span
                        className="w-3 h-3 rounded-sm inline-block"
                        style={{ backgroundColor: band.color }}
                      />
                      <span className="text-slate-300">{band.bandName}</span>
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-right text-slate-200 font-mono">
                    {formatBandNumeric(band.value, band.unit)}
                  </td>
                  <td className="py-2 text-right text-slate-400">
                    {band.unit}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ExpandedView;
