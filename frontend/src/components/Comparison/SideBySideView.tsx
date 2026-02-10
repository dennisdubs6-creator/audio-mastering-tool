import React from 'react';
import { Bar } from 'react-chartjs-2';
import type { ChartOptions } from 'chart.js';
import type { BandData } from '../Dashboard/types';
import { formatBandValue } from '@/utils/metricFormatters';

interface SideBySideViewProps {
  userBands: BandData[];
  referenceBands: BandData[];
  height?: number;
}

const SideBySideView: React.FC<SideBySideViewProps> = ({
  userBands,
  referenceBands,
  height = 200,
}) => {
  const commonOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 600 },
    scales: {
      y: {
        grid: { color: 'rgba(148, 163, 184, 0.1)' },
        ticks: { color: '#94a3b8', font: { size: 10 } },
      },
      x: {
        grid: { display: false },
        ticks: { color: '#94a3b8', font: { size: 10 } },
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1e293b',
        titleColor: '#e2e8f0',
        bodyColor: '#cbd5e1',
        borderColor: '#334155',
        borderWidth: 1,
      },
    },
  };

  const userData = {
    labels: userBands.map((b) => b.bandName),
    datasets: [{
      data: userBands.map((b) => b.value),
      backgroundColor: 'rgba(59, 130, 246, 0.7)',
      borderColor: 'rgba(59, 130, 246, 1)',
      borderWidth: 1,
      borderRadius: 4,
    }],
  };

  const refData = {
    labels: referenceBands.map((b) => b.bandName),
    datasets: [{
      data: referenceBands.map((b) => b.value),
      backgroundColor: 'rgba(34, 197, 94, 0.7)',
      borderColor: 'rgba(34, 197, 94, 1)',
      borderWidth: 1,
      borderRadius: 4,
    }],
  };

  return (
    <div className="grid grid-cols-2 gap-4" style={{ height }}>
      <div>
        <p className="text-xs text-slate-400 text-center mb-1">Your Track</p>
        <div style={{ height: height - 20 }}>
          <Bar data={userData} options={commonOptions} />
        </div>
      </div>
      <div>
        <p className="text-xs text-slate-400 text-center mb-1">Reference</p>
        <div style={{ height: height - 20 }}>
          <Bar data={refData} options={commonOptions} />
        </div>
      </div>
    </div>
  );
};

export default SideBySideView;
