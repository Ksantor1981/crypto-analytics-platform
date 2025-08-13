'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Signal } from '@/types';
import { formatDate, formatPrice } from '@/lib/utils';

interface RecentSignalsProps {
  signals: Signal[];
  isLoading?: boolean;
}

export const RecentSignals: React.FC<RecentSignalsProps> = ({
  signals,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">Последние сигналы</h3>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="animate-pulse">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                    <div>
                      <div className="w-16 h-4 bg-gray-200 rounded mb-1"></div>
                      <div className="w-24 h-3 bg-gray-200 rounded"></div>
                    </div>
                  </div>
                  <div className="w-16 h-6 bg-gray-200 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Последние сигналы</h3>
          <Link href="/signals">
            <Button variant="outline" size="sm">
              Все сигналы
            </Button>
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        {signals.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">Нет доступных сигналов</p>
          </div>
        ) : (
          <div className="space-y-4">
            {signals.map(signal => (
              <div
                key={signal.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 font-semibold text-sm">
                      {signal.asset.slice(0, 2)}
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-gray-900">
                        {signal.asset}
                      </span>
                      <Badge
                        variant={
                          signal.direction === 'long' ? 'default' : 'destructive'
                        }
                        size="sm"
                      >
                        {signal.direction.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                      <span>Вход: {formatPrice(signal.entry_price)}</span>
                      {signal.target_price && (
                        <span>Цель: {formatPrice(signal.target_price)}</span>
                      )}
                      <span>{formatDate(signal.created_at)}</span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <Badge
                    variant={
                      signal.status === 'active'
                        ? 'outline'
                        : signal.status === 'completed'
                          ? 'default'
                          : signal.status === 'failed'
                            ? 'destructive'
                            : 'secondary'
                    }
                  >
                    {signal.status === 'active'
                      ? 'Активен'
                      : signal.status === 'completed'
                        ? 'Выполнен'
                        : signal.status === 'failed'
                          ? 'Не выполнен'
                          : 'Отменен'}
                  </Badge>
                  {signal.pnl && (
                    <div
                      className={`text-sm font-medium mt-1 ${
                        signal.pnl > 0 ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {signal.pnl > 0 ? '+' : ''}
                      {signal.pnl.toFixed(2)}%
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};


