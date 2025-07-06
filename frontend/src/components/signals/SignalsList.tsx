'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Card, CardBody } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Table } from '@/components/ui/Table';
import { Signal } from '@/types';
import { formatDate, formatPrice } from '@/lib/utils';

interface SignalsListProps {
  signals: Signal[];
  isLoading?: boolean;
  onSignalSelect?: (signal: Signal) => void;
  showChannel?: boolean;
}

export const SignalsList: React.FC<SignalsListProps> = ({
  signals,
  isLoading = false,
  onSignalSelect,
  showChannel = true
}) => {
  const [sortBy, setSortBy] = useState<'created_at' | 'asset' | 'entry_price' | 'pnl' | 'status'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const sortedSignals = [...signals].sort((a, b) => {
    let aValue = a[sortBy];
    let bValue = b[sortBy];

    if (sortBy === 'created_at') {
      aValue = new Date(aValue as string).getTime();
      bValue = new Date(bValue as string).getTime();
    }

    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="warning">Активен</Badge>;
      case 'completed':
        return <Badge variant="success">Выполнен</Badge>;
      case 'failed':
        return <Badge variant="danger">Не выполнен</Badge>;
      case 'cancelled':
        return <Badge variant="secondary">Отменен</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getDirectionBadge = (direction: string) => {
    return (
      <Badge
        variant={direction === 'long' ? 'success' : 'danger'}
        size="sm"
      >
        {direction.toUpperCase()}
      </Badge>
    );
  };

  const getPnlColor = (pnl?: number) => {
    if (!pnl) return 'text-gray-500';
    return pnl > 0 ? 'text-green-600' : 'text-red-600';
  };

  if (isLoading) {
    return (
      <Card>
        <CardBody>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gray-200 rounded-full"></div>
                    <div>
                      <div className="w-24 h-4 bg-gray-200 rounded mb-2"></div>
                      <div className="w-32 h-3 bg-gray-200 rounded"></div>
                    </div>
                  </div>
                  <div className="w-16 h-6 bg-gray-200 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    );
  }

  if (signals.length === 0) {
    return (
      <Card>
        <CardBody className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">⚡</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Нет сигналов</h3>
          <p className="text-gray-600">Сигналы появятся здесь после подключения каналов</p>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardBody>
        <div className="overflow-x-auto">
          <Table>
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4">
                  <button
                    onClick={() => handleSort('asset')}
                    className="flex items-center space-x-1 font-medium text-gray-700 hover:text-gray-900"
                  >
                    <span>Актив</span>
                    {sortBy === 'asset' && (
                      <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
                <th className="text-left py-3 px-4">Направление</th>
                <th className="text-left py-3 px-4">
                  <button
                    onClick={() => handleSort('entry_price')}
                    className="flex items-center space-x-1 font-medium text-gray-700 hover:text-gray-900"
                  >
                    <span>Вход</span>
                    {sortBy === 'entry_price' && (
                      <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
                <th className="text-left py-3 px-4">Цель/Стоп</th>
                {showChannel && <th className="text-left py-3 px-4">Канал</th>}
                <th className="text-left py-3 px-4">Статус</th>
                <th className="text-left py-3 px-4">
                  <button
                    onClick={() => handleSort('pnl')}
                    className="flex items-center space-x-1 font-medium text-gray-700 hover:text-gray-900"
                  >
                    <span>P&L</span>
                    {sortBy === 'pnl' && (
                      <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
                <th className="text-left py-3 px-4">
                  <button
                    onClick={() => handleSort('created_at')}
                    className="flex items-center space-x-1 font-medium text-gray-700 hover:text-gray-900"
                  >
                    <span>Дата</span>
                    {sortBy === 'created_at' && (
                      <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
                <th className="text-right py-3 px-4">Действия</th>
              </tr>
            </thead>
            <tbody>
              {sortedSignals.map((signal) => (
                <tr key={signal.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 font-semibold text-xs">
                          {signal.asset.slice(0, 3)}
                        </span>
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">{signal.asset}</div>
                        {signal.confidence && (
                          <div className="text-xs text-gray-500">
                            Уверенность: {(signal.confidence * 100).toFixed(0)}%
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    {getDirectionBadge(signal.direction)}
                  </td>
                  <td className="py-3 px-4">
                    <span className="font-medium text-gray-900">
                      {formatPrice(signal.entry_price)}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="text-sm">
                      {signal.target_price && (
                        <div className="text-green-600">
                          🎯 {formatPrice(signal.target_price)}
                        </div>
                      )}
                      {signal.stop_loss && (
                        <div className="text-red-600">
                          🛑 {formatPrice(signal.stop_loss)}
                        </div>
                      )}
                    </div>
                  </td>
                  {showChannel && (
                    <td className="py-3 px-4">
                      {signal.channel ? (
                        <Link href={`/channels/${signal.channel.id}`}>
                          <span className="text-blue-600 hover:text-blue-800 text-sm">
                            {signal.channel.name}
                          </span>
                        </Link>
                      ) : (
                        <span className="text-gray-500 text-sm">—</span>
                      )}
                    </td>
                  )}
                  <td className="py-3 px-4">
                    {getStatusBadge(signal.status)}
                  </td>
                  <td className="py-3 px-4">
                    {signal.pnl !== undefined ? (
                      <span className={`font-medium ${getPnlColor(signal.pnl)}`}>
                        {signal.pnl > 0 ? '+' : ''}{signal.pnl.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-gray-500">—</span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-gray-600 text-sm">
                      {formatDate(signal.created_at)}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <Link href={`/signals/${signal.id}`}>
                        <Button variant="outline" size="sm">
                          Подробнее
                        </Button>
                      </Link>
                      {onSignalSelect && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => onSignalSelect(signal)}
                        >
                          Выбрать
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      </CardBody>
    </Card>
  );
}; 