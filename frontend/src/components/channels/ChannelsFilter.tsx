'use client';

import React, { useState } from 'react';
import { Card, CardBody } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/Badge';
import { ChannelFilters } from '@/types';

interface ChannelsFilterProps {
  filters: ChannelFilters;
  onFiltersChange: (filters: ChannelFilters) => void;
  onReset: () => void;
}

export const ChannelsFilter: React.FC<ChannelsFilterProps> = ({
  filters,
  onFiltersChange,
  onReset,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleFilterChange = (key: keyof ChannelFilters, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value,
    });
  };

  const statusOptions = [
    { value: 'active', label: 'Активные' },
    { value: 'inactive', label: 'Неактивные' },
    { value: 'error', label: 'С ошибками' },
  ];

  const accuracyRanges = [
    { value: '80-100', label: '80-100%' },
    { value: '60-80', label: '60-80%' },
    { value: '40-60', label: '40-60%' },
    { value: '0-40', label: '0-40%' },
  ];

  const signalRanges = [
    { value: '100+', label: '100+ сигналов' },
    { value: '50-100', label: '50-100 сигналов' },
    { value: '10-50', label: '10-50 сигналов' },
    { value: '0-10', label: '0-10 сигналов' },
  ];

  const activeFiltersCount = Object.values(filters).filter(
    value => value !== undefined && value !== null && value !== ''
  ).length;

  return (
    <Card>
      <CardBody className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <h3 className="font-medium text-gray-900">Фильтры</h3>
            {activeFiltersCount > 0 && (
              <Badge variant="primary" size="sm">
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
            placeholder="Поиск по названию канала..."
            value={filters.search || ''}
            onChange={e => handleFilterChange('search', e.target.value)}
          />
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

            {/* Accuracy filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Точность
              </label>
              <div className="flex flex-wrap gap-2">
                {accuracyRanges.map(range => (
                  <button
                    key={range.value}
                    onClick={() =>
                      handleFilterChange(
                        'accuracy_range',
                        filters.accuracy_range === range.value
                          ? undefined
                          : range.value
                      )
                    }
                    className={`px-3 py-1 rounded-full text-sm border ${
                      filters.accuracy_range === range.value
                        ? 'bg-green-100 border-green-500 text-green-700'
                        : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {range.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Signals count filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Количество сигналов
              </label>
              <div className="flex flex-wrap gap-2">
                {signalRanges.map(range => (
                  <button
                    key={range.value}
                    onClick={() =>
                      handleFilterChange(
                        'signals_range',
                        filters.signals_range === range.value
                          ? undefined
                          : range.value
                      )
                    }
                    className={`px-3 py-1 rounded-full text-sm border ${
                      filters.signals_range === range.value
                        ? 'bg-purple-100 border-purple-500 text-purple-700'
                        : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {range.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Date range */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Добавлен с
                </label>
                <Input
                  type="date"
                  value={filters.created_from || ''}
                  onChange={e =>
                    handleFilterChange('created_from', e.target.value)
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Добавлен до
                </label>
                <Input
                  type="date"
                  value={filters.created_to || ''}
                  onChange={e =>
                    handleFilterChange('created_to', e.target.value)
                  }
                />
              </div>
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
};



