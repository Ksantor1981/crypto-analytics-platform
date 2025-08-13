'use client';

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SignalFilters } from '@/types';

interface SignalsFilterProps {
  filters: SignalFilters;
  onFiltersChange: (filters: SignalFilters) => void;
  onReset: () => void;
}

export const SignalsFilter: React.FC<SignalsFilterProps> = ({
  filters,
  onFiltersChange,
  onReset,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleFilterChange = (key: keyof SignalFilters, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value,
    });
  };

  const statusOptions = [
    { value: 'active', label: 'Активные' },
    { value: 'completed', label: 'Выполненные' },
    { value: 'failed', label: 'Не выполненные' },
    { value: 'cancelled', label: 'Отмененные' },
  ];

  const directionOptions = [
    { value: 'long', label: 'Long' },
    { value: 'short', label: 'Short' },
  ];

  const pnlRanges = [
    { value: 'positive', label: 'Прибыльные' },
    { value: 'negative', label: 'Убыточные' },
    { value: 'breakeven', label: 'В ноле' },
  ];

  const timeRanges = [
    { value: 'today', label: 'Сегодня' },
    { value: 'week', label: 'Неделя' },
    { value: 'month', label: 'Месяц' },
    { value: 'quarter', label: 'Квартал' },
  ];

  const activeFiltersCount = Object.values(filters).filter(
    value => value !== undefined && value !== null && value !== ''
  ).length;

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <h3 className="font-medium text-gray-900">Фильтры</h3>
            {activeFiltersCount > 0 && (
              <Badge variant="default" size="sm">
                {activeFiltersCount}
              </Badge>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onReset}
              disabled={activeFiltersCount === 0}
            >
              Сбросить
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Свернуть' : 'Развернуть'}
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="mb-4">
          <Input
            placeholder="Поиск по активу (BTC, ETH, ADA...)"
            value={filters.search || ''}
            onChange={e => handleFilterChange('search', e.target.value)}
          />
        </div>

        {/* Quick filters */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
          {statusOptions.slice(0, 2).map(option => (
            <button
              key={option.value}
              onClick={() =>
                handleFilterChange(
                  'status',
                  filters.status === option.value ? undefined : option.value
                )
              }
              className={`px-3 py-2 rounded-md text-sm border ${
                filters.status === option.value
                  ? 'bg-blue-100 border-blue-500 text-blue-700'
                  : 'border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {option.label}
            </button>
          ))}

          {directionOptions.map(option => (
            <button
              key={option.value}
              onClick={() =>
                handleFilterChange(
                  'direction',
                  filters.direction === option.value ? undefined : option.value
                )
              }
              className={`px-3 py-2 rounded-md text-sm border ${
                filters.direction === option.value
                  ? 'bg-green-100 border-green-500 text-green-700'
                  : 'border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>

        {/* Expanded filters */}
        {isExpanded && (
          <div className="space-y-4">
            {/* Status filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Статус
              </label>
              <div className="flex flex-wrap gap-2">
                {statusOptions.map(option => (
                  <button
                    key={option.value}
                    onClick={() =>
                      handleFilterChange(
                        'status',
                        filters.status === option.value
                          ? undefined
                          : option.value
                      )
                    }
                    className={`px-3 py-1 rounded-full text-sm border ${
                      filters.status === option.value
                        ? 'bg-blue-100 border-blue-500 text-blue-700'
                        : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {/* P&L filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Результат
              </label>
              <div className="flex flex-wrap gap-2">
                {pnlRanges.map(range => (
                  <button
                    key={range.value}
                    onClick={() =>
                      handleFilterChange(
                        'pnl_range',
                        filters.pnl_range === range.value
                          ? undefined
                          : range.value
                      )
                    }
                    className={`px-3 py-1 rounded-full text-sm border ${
                      filters.pnl_range === range.value
                        ? 'bg-purple-100 border-purple-500 text-purple-700'
                        : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {range.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Time range filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Период
              </label>
              <div className="flex flex-wrap gap-2">
                {timeRanges.map(range => (
                  <button
                    key={range.value}
                    onClick={() =>
                      handleFilterChange(
                        'time_range',
                        filters.time_range === range.value
                          ? undefined
                          : range.value
                      )
                    }
                    className={`px-3 py-1 rounded-full text-sm border ${
                      filters.time_range === range.value
                        ? 'bg-yellow-100 border-yellow-500 text-yellow-700'
                        : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {range.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Price range */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Цена от
                </label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={filters.price_from || ''}
                  onChange={e =>
                    handleFilterChange('price_from', e.target.value)
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Цена до
                </label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={filters.price_to || ''}
                  onChange={e => handleFilterChange('price_to', e.target.value)}
                />
              </div>
            </div>

            {/* Date range */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Дата с
                </label>
                <Input
                  type="date"
                  value={filters.date_from || ''}
                  onChange={e =>
                    handleFilterChange('date_from', e.target.value)
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Дата до
                </label>
                <Input
                  type="date"
                  value={filters.date_to || ''}
                  onChange={e => handleFilterChange('date_to', e.target.value)}
                />
              </div>
            </div>

            {/* Channel filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Канал
              </label>
              <Input
                placeholder="Введите ID канала или название"
                value={filters.channel_id || ''}
                onChange={e => handleFilterChange('channel_id', e.target.value)}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};



