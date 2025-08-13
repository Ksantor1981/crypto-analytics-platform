'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease';
  };
  icon?: string;
  className?: string;
}

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  change,
  icon,
  className = '',
}) => {
  return (
    <Card className={`${className}`}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
            {change && (
              <div className="flex items-center mt-2">
                <span
                  className={`text-sm font-medium ${
                    change.type === 'increase'
                      ? 'text-green-600'
                      : 'text-red-600'
                  }`}
                >
                  {change.type === 'increase' ? '↗' : '↘'}{' '}
                  {Math.abs(change.value)}%
                </span>
                <span className="text-xs text-gray-500 ml-2">за месяц</span>
              </div>
            )}
          </div>
          {icon && <div className="text-3xl opacity-60">{icon}</div>}
        </div>
      </CardContent>
    </Card>
  );
};

