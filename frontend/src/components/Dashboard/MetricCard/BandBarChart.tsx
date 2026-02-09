import React from 'react';
import { Bar } from 'react-chartjs-2';
import type { ChartOptions } from 'chart.js';
import type { BandData } from '../types';

interface BandBarChartProps {
  bands: BandData[];
  height?: number;
}

const BandBarChart: React.FC<BandBarChartProps> = ({ bands, height = 200 }) => {
  if (bands.length === 0) {
    return (
      <div className="flex items-center justify-center text-sm text-slate-500" style={{ height }}>
        No data available
      </div>
    );
  }

  const data = {
    labels: bands.map((b) => b.bandName),
    datasets: [
      {
        data: bands.map((b) => b.value),
        backgroundColor: bands.map((b) => b.color),
        borderColor: bands.map((b) => b.color),
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const options: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 600,
    },
    scales: {
      y: {
        grid: {
          color: 'rgba(148, 163, 184, 0.1)',
        },
        ticks: {
          color: '#94a3b8',
          font: { size: 11 },
        },
      },
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: '#94a3b8',
          font: { size: 11 },
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: true,
        backgroundColor: '#1e293b',
        titleColor: '#e2e8f0',
        bodyColor: '#cbd5e1',
        borderColor: '#334155',
        borderWidth: 1,
        callbacks: {
          label: (context) => {
            const band = bands[context.dataIndex];
            const yVal = context.parsed.y ?? 0;
            return `${yVal.toFixed(2)} ${band.unit}`;
          },
        },
      },
    },
  };

  return (
    <div style={{ height }}>
      <Bar data={data} options={options} />
    </div>
  );
};

export default BandBarChart;
