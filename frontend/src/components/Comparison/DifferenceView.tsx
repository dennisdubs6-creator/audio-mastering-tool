import React from 'react';
import { Bar } from 'react-chartjs-2';
import type { ChartOptions } from 'chart.js';
import type { BandData } from '../Dashboard/types';

interface DifferenceViewProps {
  userBands: BandData[];
  referenceBands: BandData[];
  height?: number;
}

const DifferenceView: React.FC<DifferenceViewProps> = ({
  userBands,
  referenceBands,
  height = 200,
}) => {
  const labels = userBands.map((b) => b.bandName);
  const deltas = userBands.map((b, i) => {
    const refVal = referenceBands[i]?.value ?? 0;
    return +(b.value - refVal).toFixed(2);
  });

  const data = {
    labels,
    datasets: [
      {
        label: 'Difference (User - Reference)',
        data: deltas,
        backgroundColor: deltas.map((d) =>
          d >= 0 ? 'rgba(239, 68, 68, 0.7)' : 'rgba(59, 130, 246, 0.7)'
        ),
        borderColor: deltas.map((d) =>
          d >= 0 ? 'rgba(239, 68, 68, 1)' : 'rgba(59, 130, 246, 1)'
        ),
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const options: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 600 },
    scales: {
      y: {
        grid: { color: 'rgba(148, 163, 184, 0.1)' },
        ticks: { color: '#94a3b8', font: { size: 11 } },
      },
      x: {
        grid: { display: false },
        ticks: { color: '#94a3b8', font: { size: 11 } },
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
        callbacks: {
          label: (context) => {
            const val = context.parsed.y;
            const direction = val >= 0 ? 'louder' : 'quieter';
            return `${Math.abs(val).toFixed(1)} ${userBands[0]?.unit || 'dB'} ${direction}`;
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

export default DifferenceView;
