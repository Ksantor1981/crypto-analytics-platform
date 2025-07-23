'use client';

import React from 'react';
import { Card, CardBody } from '@/components/ui/card';
import { Badge } from '@/components/ui/Badge';
import { Signal } from '@/types';

interface SignalsStatsProps {
  signals: Signal[];
}

export const SignalsStats: React.FC<SignalsStatsProps> = ({ signals }) => {
  const stats = React.useMemo(() => {
    const total = signals.length;
    const active = signals.filter(s => s.status === 'active').length;
    const completed = signals.filter(s => s.status === 'completed').length;
    const failed = signals.filter(s => s.status === 'failed').length;

    const signalsWithPnl = signals.filter(s => s.pnl !== undefined);
    const profitable = signalsWithPnl.filter(s => s.pnl! > 0).length;
    const unprofitable = signalsWithPnl.filter(s => s.pnl! < 0).length;

    const totalPnl = signalsWithPnl.reduce((sum, s) => sum + s.pnl!, 0);
    const avgPnl =
      signalsWithPnl.length > 0 ? totalPnl / signalsWithPnl.length : 0;

    const winRate =
      signalsWithPnl.length > 0
        ? (profitable / signalsWithPnl.length) * 100
        : 0;

    // Best and worst signals
    const bestSignal = signalsWithPnl.reduce(
      (best, current) =>
        current.pnl! > (best?.pnl || -Infinity) ? current : best,
      null as Signal | null
    );

    const worstSignal = signalsWithPnl.reduce(
      (worst, current) =>
        current.pnl! < (worst?.pnl || Infinity) ? current : worst,
      null as Signal | null
    );

    // Direction stats
    const longSignals = signals.filter(s => s.direction === 'long').length;
    const shortSignals = signals.filter(s => s.direction === 'short').length;

    return {
      total,
      active,
      completed,
      failed,
      profitable,
      unprofitable,
      totalPnl,
      avgPnl,
      winRate,
      bestSignal,
      worstSignal,
      longSignals,
      shortSignals,
    };
  }, [signals]);

  const getStatCard = (
    title: string,
    value: string | number,
    subtitle?: string,
    color?: string
  ) => (
    <div className="text-center">
      <div className={`text-2xl font-bold ${color || 'text-gray-900'}`}>
        {value}
      </div>
      <div className="text-sm text-gray-600">{title}</div>
      {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
    </div>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total signals */}
      <Card>
        <CardBody className="p-4">
          {getStatCard('Всего сигналов', stats.total)}
        </CardBody>
      </Card>

      {/* Active signals */}
      <Card>
        <CardBody className="p-4">
          {getStatCard(
            'Активные',
            stats.active,
            'в процессе',
            'text-yellow-600'
          )}
        </CardBody>
      </Card>

      {/* Win rate */}
      <Card>
        <CardBody className="p-4">
          {getStatCard(
            'Процент успеха',
            `${stats.winRate.toFixed(1)}%`,
            `${stats.profitable}/${stats.profitable + stats.unprofitable}`,
            stats.winRate >= 50 ? 'text-green-600' : 'text-red-600'
          )}
        </CardBody>
      </Card>

      {/* Average P&L */}
      <Card>
        <CardBody className="p-4">
          {getStatCard(
            'Средний P&L',
            `${stats.avgPnl > 0 ? '+' : ''}${stats.avgPnl.toFixed(2)}%`,
            undefined,
            stats.avgPnl >= 0 ? 'text-green-600' : 'text-red-600'
          )}
        </CardBody>
      </Card>

      {/* Status breakdown */}
      <Card>
        <CardBody className="p-4">
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900 mb-2">
              Статусы
            </div>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Badge variant="success" size="sm">
                  Выполнено
                </Badge>
                <span className="text-sm">{stats.completed}</span>
              </div>
              <div className="flex justify-between items-center">
                <Badge variant="warning" size="sm">
                  Активно
                </Badge>
                <span className="text-sm">{stats.active}</span>
              </div>
              <div className="flex justify-between items-center">
                <Badge variant="danger" size="sm">
                  Не выполнено
                </Badge>
                <span className="text-sm">{stats.failed}</span>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Direction breakdown */}
      <Card>
        <CardBody className="p-4">
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900 mb-2">
              Направления
            </div>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Badge variant="success" size="sm">
                  Long
                </Badge>
                <span className="text-sm">{stats.longSignals}</span>
              </div>
              <div className="flex justify-between items-center">
                <Badge variant="danger" size="sm">
                  Short
                </Badge>
                <span className="text-sm">{stats.shortSignals}</span>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Best signal */}
      {stats.bestSignal && (
        <Card>
          <CardBody className="p-4">
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-900 mb-2">
                Лучший сигнал
              </div>
              <div className="text-2xl font-bold text-green-600">
                +{stats.bestSignal.pnl!.toFixed(2)}%
              </div>
              <div className="text-sm text-gray-600">
                {stats.bestSignal.asset}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {stats.bestSignal.direction.toUpperCase()}
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Worst signal */}
      {stats.worstSignal && (
        <Card>
          <CardBody className="p-4">
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-900 mb-2">
                Худший сигнал
              </div>
              <div className="text-2xl font-bold text-red-600">
                {stats.worstSignal.pnl!.toFixed(2)}%
              </div>
              <div className="text-sm text-gray-600">
                {stats.worstSignal.asset}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {stats.worstSignal.direction.toUpperCase()}
              </div>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
};

