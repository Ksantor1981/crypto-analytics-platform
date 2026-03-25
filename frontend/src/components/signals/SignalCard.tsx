'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Signal } from '@/types';
import { formatDate, formatPrice } from '@/lib/utils';

interface SignalCardProps {
  signal: Signal;
  showChannel?: boolean;
  onAnalyze?: (signal: Signal) => void;
}

export const SignalCard: React.FC<SignalCardProps> = ({
  signal,
  showChannel = true,
  onAnalyze,
}) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="outline">Активен</Badge>;
      case 'completed':
        return <Badge variant="default">Выполнен</Badge>;
      case 'failed':
        return <Badge variant="destructive">Не выполнен</Badge>;
      case 'cancelled':
        return <Badge variant="secondary">Отменен</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getDirectionBadge = (direction: string) => {
    return (
      <Badge variant={direction === 'long' ? 'default' : 'destructive'} size="sm">
        {direction.toUpperCase()}
      </Badge>
    );
  };

  const getPnlColor = (pnl?: number) => {
    if (!pnl) return 'text-gray-500';
    return pnl > 0 ? 'text-green-600' : 'text-red-600';
  };

  const calculatePotentialProfit = () => {
    if (!signal.target_price || signal.entry_price == null) return null;

    const entryPrice = signal.entry_price;
    const targetPrice = signal.target_price;

    if (signal.direction === 'long') {
      return ((targetPrice - entryPrice) / entryPrice) * 100;
    }
    return ((entryPrice - targetPrice) / entryPrice) * 100;
  };

  const calculateRiskReward = () => {
    if (!signal.target_price || !signal.stop_loss || signal.entry_price == null)
      return null;

    const entryPrice = signal.entry_price;
    const targetPrice = signal.target_price;
    const stopLoss = signal.stop_loss;

    let reward, risk;

    if (signal.direction === 'long') {
      reward = targetPrice - entryPrice;
      risk = entryPrice - stopLoss;
    } else {
      reward = entryPrice - targetPrice;
      risk = stopLoss - entryPrice;
    }

    return risk > 0 ? reward / risk : null;
  };

  const potentialProfit = calculatePotentialProfit();
  const riskReward = calculateRiskReward();
  const displaySymbol = (signal.asset ?? signal.pair ?? '—').toString();
  const label3 = displaySymbol.slice(0, 3).toUpperCase();

  return (
    <Card className="h-full">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-blue-600 font-semibold">
                {label3}
              </span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{displaySymbol}</h3>
              <div className="flex items-center space-x-2 mt-1">
                {getDirectionBadge(signal.direction)}
                {getStatusBadge(signal.status)}
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-600">
              {formatDate(signal.created_at)}
            </div>
            {signal.confidence && (
              <div className="text-xs text-gray-500 mt-1">
                Уверенность: {(signal.confidence * 100).toFixed(0)}%
              </div>
            )}
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Цена входа:</span>
            <span className="font-medium text-gray-900">
              {signal.entry_price != null
                ? formatPrice(signal.entry_price)
                : '—'}
            </span>
          </div>

          {signal.target_price && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Цель:</span>
              <span className="font-medium text-green-600">
                {formatPrice(signal.target_price)}
              </span>
            </div>
          )}

          {signal.stop_loss && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Стоп-лосс:</span>
              <span className="font-medium text-red-600">
                {formatPrice(signal.stop_loss)}
              </span>
            </div>
          )}

          {showChannel && signal.channel && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Канал:</span>
              <Link href={`/channels/${signal.channel.id}`}>
                <span className="text-sm text-blue-600 hover:text-blue-800">
                  {signal.channel.name}
                </span>
              </Link>
            </div>
          )}
        </div>

        {/* Performance indicators */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-4">
            {signal.pnl !== undefined ? (
              <div className="text-center">
                <div
                  className={`text-lg font-semibold ${getPnlColor(signal.pnl)}`}
                >
                  {signal.pnl > 0 ? '+' : ''}
                  {signal.pnl.toFixed(1)}%
                </div>
                <div className="text-xs text-gray-600">Текущий P&L</div>
              </div>
            ) : (
              potentialProfit && (
                <div className="text-center">
                  <div className="text-lg font-semibold text-blue-600">
                    +{potentialProfit.toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-600">Потенциал</div>
                </div>
              )
            )}

            {riskReward && (
              <div className="text-center">
                <div className="text-lg font-semibold text-purple-600">
                  1:{riskReward.toFixed(1)}
                </div>
                <div className="text-xs text-gray-600">Risk/Reward</div>
              </div>
            )}
          </div>
        </div>

        {/* Additional info */}
        {signal.description && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600 line-clamp-3">
              {signal.description}
            </p>
          </div>
        )}
      </CardContent>

      <CardFooter className="p-6 pt-0">
        <div className="flex items-center space-x-2 w-full">
          <Link href={`/signals/${signal.id}`} className="flex-1">
            <Button variant="outline" className="w-full">
              Подробнее
            </Button>
          </Link>

          {onAnalyze && (
            <Button
              variant="default"
              className="flex-1"
              onClick={() => onAnalyze(signal)}
            >
              🤖 Анализ ML
            </Button>
          )}
        </div>
      </CardFooter>
    </Card>
  );
};


