'use client';

import React from 'react';
import { LineChart } from './LineChart';
import { Signal } from '@/types';

interface PerformanceChartProps {
  signals: Signal[];
  timeRange?: 'week' | 'month' | 'quarter' | 'year';
  height?: number;
}

export const PerformanceChart: React.FC<PerformanceChartProps> = ({
  signals,
  timeRange = 'month',
  height = 400,
}) => {
  const getTimeRangeData = () => {
    const now = new Date();
    let startDate: Date;
    let groupBy: 'day' | 'week' | 'month';

    switch (timeRange) {
      case 'week':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        groupBy = 'day';
        break;
      case 'month':
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        groupBy = 'day';
        break;
      case 'quarter':
        startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        groupBy = 'week';
        break;
      case 'year':
        startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
        groupBy = 'month';
        break;
    }

    // Фильтруем сигналы по временному диапазону
    const filteredSignals = signals.filter(signal => {
      const signalDate = new Date(signal.created_at);
      return signalDate >= startDate && signalDate <= now;
    });

    // Группируем данные по периодам
    const groupedData = new Map<string, { pnl: number; count: number }>();

    filteredSignals.forEach(signal => {
      if (signal.pnl === undefined) return;

      const date = new Date(signal.created_at);
      let key: string;

      switch (groupBy) {
        case 'day':
          key = date.toISOString().split('T')[0];
          break;
        case 'week':
          const weekStart = new Date(date);
          weekStart.setDate(date.getDate() - date.getDay());
          key = weekStart.toISOString().split('T')[0];
          break;
        case 'month':
          key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          break;
      }

      if (!groupedData.has(key)) {
        groupedData.set(key, { pnl: 0, count: 0 });
      }

      const current = groupedData.get(key)!;
      current.pnl += signal.pnl;
      current.count += 1;
    });

    // Создаем массивы для графика
    const sortedKeys = Array.from(groupedData.keys()).sort();
    const labels = sortedKeys.map(key => {
      const date = new Date(key);
      switch (groupBy) {
        case 'day':
          return date.toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
          });
        case 'week':
          return `${date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })}`;
        case 'month':
          return date.toLocaleDateString('ru-RU', {
            month: 'short',
            year: 'numeric',
          });
        default:
          return key;
      }
    });

    const pnlData = sortedKeys.map(key => groupedData.get(key)!.pnl);
    const countData = sortedKeys.map(key => groupedData.get(key)!.count);

    // Накопительная прибыль
    const cumulativePnl = pnlData.reduce((acc, current, index) => {
      acc.push((acc[index - 1] || 0) + current);
      return acc;
    }, [] as number[]);

    return { labels, pnlData, countData, cumulativePnl };
  };

  const { labels, pnlData, countData, cumulativePnl } = getTimeRangeData();

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Накопительная прибыль (%)',
        data: cumulativePnl,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'P&L за период (%)',
        data: pnlData,
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: false,
        tension: 0.4,
      },
    ],
  };

  const options = {
    plugins: {
      title: {
        display: true,
        text: 'Производительность сигналов',
      },
      legend: {
        display: true,
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        title: {
          display: true,
          text: 'Прибыль (%)',
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
      },
      x: {
        title: {
          display: true,
          text: 'Период',
        },
        grid: {
          display: false,
        },
      },
    },
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <LineChart data={chartData} options={options} height={height} />
    </div>
  );
};
