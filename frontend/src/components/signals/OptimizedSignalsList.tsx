'use client';

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Signal } from '@/types';
import { formatDate, formatPrice } from '@/lib/utils';
import { useDebounced } from '@/lib/performance';

interface OptimizedSignalsListProps {
  signals: Signal[];
  isLoading?: boolean;
  onSignalSelect?: (signal: Signal) => void;
  showChannel?: boolean;
  searchTerm?: string;
  // height удален - не используется
}

// Константа удалена - не используется

const SignalItem = React.memo<{
  signal: Signal;
  onSignalSelect?: (signal: Signal) => void;
  showChannel: boolean;
}>(({ signal, onSignalSelect, showChannel }) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return (
          <Badge variant="outline" size="sm">
            Активен
          </Badge>
        );
      case 'completed':
        return (
          <Badge variant="default" size="sm">
            Выполнен
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive" size="sm">
            Не выполнен
          </Badge>
        );
      case 'cancelled':
        return (
          <Badge variant="secondary" size="sm">
            Отменен
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary" size="sm">
            {status}
          </Badge>
        );
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

  return (
    <div className="flex items-center justify-between p-4 border-b border-gray-100 hover:bg-gray-50">
      <div className="flex items-center space-x-4 flex-1">
        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
          <span className="text-blue-600 font-semibold text-xs">
            {signal.asset.slice(0, 3)}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <span className="font-medium text-gray-900">{signal.asset}</span>
            {getDirectionBadge(signal.direction)}
            {getStatusBadge(signal.status)}
          </div>

          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span>Вход: {formatPrice(signal.entry_price)}</span>
            {signal.target_price && (
              <span className="text-green-600">
                Цель: {formatPrice(signal.target_price)}
              </span>
            )}
            {signal.pnl !== undefined && (
              <span className={`font-medium ${getPnlColor(signal.pnl)}`}>
                P&L: {signal.pnl > 0 ? '+' : ''}
                {signal.pnl.toFixed(2)}%
              </span>
            )}
          </div>
        </div>

        {showChannel && signal.channel && (
          <div className="hidden md:block text-sm text-gray-600">
            <Link href={`/channels/${signal.channel.id}`}>
              <span className="text-blue-600 hover:text-blue-800">
                {signal.channel.name}
              </span>
            </Link>
          </div>
        )}

        <div className="text-sm text-gray-500">
          {formatDate(signal.created_at)}
        </div>
      </div>

      <div className="flex items-center space-x-2 ml-4">
        <Link href={`/signals/${signal.id}`}>
          <Button variant="outline" size="sm">
            Подробнее
          </Button>
        </Link>
        {onSignalSelect && (
          <Button
            variant="default"
            size="sm"
            onClick={() => onSignalSelect(signal)}
          >
            Выбрать
          </Button>
        )}
      </div>
    </div>
  );
});

export const OptimizedSignalsList: React.FC<OptimizedSignalsListProps> = ({
  signals,
  isLoading = false,
  onSignalSelect,
  showChannel = true,
  searchTerm = '',
}) => {
  const [sortBy, setSortBy] = useState<
    'created_at' | 'asset' | 'entry_price' | 'pnl' | 'status'
  >('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Оптимизированный поиск с дебаунсом
  const debouncedSearchTerm = useDebounced(searchTerm, 300);
  const searchedSignals = React.useMemo(() => {
    if (!debouncedSearchTerm) return signals;
    return signals.filter(signal => 
      signal.asset.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
      signal.status.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
      signal.direction.toLowerCase().includes(debouncedSearchTerm.toLowerCase())
    );
  }, [signals, debouncedSearchTerm]);

  // Мемоизированная сортировка
  const sortedSignals = useMemo(() => {
    return [...searchedSignals].sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];

      if (sortBy === 'created_at') {
        aValue = new Date(aValue as string).getTime();
        bValue = new Date(bValue as string).getTime();
      }

      if (sortOrder === 'asc') {
        return (aValue || 0) > (bValue || 0) ? 1 : -1;
      } else {
        return (aValue || 0) < (bValue || 0) ? 1 : -1;
      }
    });
  }, [searchedSignals, sortBy, sortOrder]);

  // Функция сортировки удалена - не используется в интерфейсе

  // Мемоизированный рендер элемента
  const renderItem = useMemo(() => {
    return (signal: Signal) => (
      <SignalItem
        key={signal.id}
        signal={signal}
        onSignalSelect={onSignalSelect}
        showChannel={showChannel}
      />
    );
  }, [onSignalSelect, showChannel]);

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="animate-pulse">
                <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
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
        </CardContent>
      </Card>
    );
  }

  if (sortedSignals.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">⚡</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchTerm ? 'Сигналы не найдены' : 'Нет сигналов'}
          </h3>
          <p className="text-gray-600">
            {searchTerm
              ? 'Попробуйте изменить поисковый запрос'
              : 'Сигналы появятся здесь после подключения каналов'}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-0">
        {/* Header with sorting */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-gray-700">
                Найдено: {sortedSignals.length} сигналов
              </span>
              {searchTerm && (
                <span className="text-xs text-blue-600">Поиск...</span>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Сортировка:</span>
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={e => {
                  const [field, order] = e.target.value.split('-');
                  setSortBy(field as typeof sortBy);
                  setSortOrder(order as 'asc' | 'desc');
                }}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="created_at-desc">Дата (новые)</option>
                <option value="created_at-asc">Дата (старые)</option>
                <option value="asset-asc">Актив (А-Я)</option>
                <option value="asset-desc">Актив (Я-А)</option>
                <option value="pnl-desc">P&L (убыв.)</option>
                <option value="pnl-asc">P&L (возр.)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Signals list */}
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {sortedSignals.map(signal => renderItem(signal))}
        </div>
      </CardContent>
    </Card>
  );
};


