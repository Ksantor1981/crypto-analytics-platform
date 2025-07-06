'use client';

import React from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

interface DoughnutChartProps {
  data: {
    labels: string[];
    datasets: {
      label?: string;
      data: number[];
      backgroundColor?: string[];
      borderColor?: string[];
      borderWidth?: number;
    }[];
  };
  options?: any;
  height?: number;
  width?: number;
}

export const DoughnutChart: React.FC<DoughnutChartProps> = ({
  data,
  options = {},
  height = 400,
  width
}) => {
  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
      title: {
        display: false,
      },
    },
    cutout: '60%',
    ...options,
  };

  return (
    <div style={{ height, width }}>
      <Doughnut data={data} options={defaultOptions} />
    </div>
  );
}; 