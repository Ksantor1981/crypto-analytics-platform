'use client';

import React, { useState } from 'react';

import { SimpleTable, SimpleColumn } from '@/components/ui/simple-table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Channel, ChannelSortField, SortOrder } from '@/types';

interface ChannelsListProps {
  channels: Channel[];
  onChannelSelect?: (channel: Channel) => void;
}

const ChannelsList: React.FC<ChannelsListProps> = ({
  channels,
  onChannelSelect,
}) => {
  const [sortBy, setSortBy] = useState<ChannelSortField>('accuracy');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const sortedChannels = [...channels].sort((a, b) => {
    let aValue = a[sortBy];
    let bValue = b[sortBy];

    // Обработка undefined значений
    if (aValue === undefined) return 1;
    if (bValue === undefined) return -1;

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

  const handleSort = (field: ChannelSortField) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const columns: SimpleColumn<Channel>[] = [
    {
      header: (
        <button
          onClick={() => handleSort('name')}
          className="flex items-center space-x-1 hover:text-blue-600"
        >
          <span>Название</span>
          {sortBy === 'name' && <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>}
        </button>
      ),
      accessorKey: 'name',
      cell: channel => (
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-blue-600 font-semibold text-sm">
              {channel.name.slice(0, 2).toUpperCase()}
            </span>
          </div>
          <div>
            <div className="font-medium text-gray-900">{channel.name}</div>
            <div className="text-sm text-gray-600">@{channel.username}</div>
          </div>
        </div>
      ),
    },
    {
      header: (
        <button
          onClick={() => handleSort('accuracy')}
          className="flex items-center space-x-1 hover:text-blue-600"
        >
          <span>Точность</span>
          {sortBy === 'accuracy' && (
            <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
          )}
        </button>
      ),
      accessorKey: 'accuracy',
      cell: channel => `${channel.accuracy?.toFixed(1) || 0}%`,
    },
    {
      header: 'Статус',
      accessorKey: 'status',
      cell: channel => {
        const status = channel.status;
        switch (status) {
          case 'active':
            return <Badge variant="default">Активен</Badge>;
          case 'inactive':
            return <Badge variant="secondary">Неактивен</Badge>;
          case 'error':
            return <Badge variant="destructive">Ошибка</Badge>;
          case 'pending':
            return <Badge variant="outline">В ожидании</Badge>;
          default:
            return <Badge variant="outline">Неизвестен</Badge>;
        }
      },
    },
    {
      header: 'Действия',
      accessorKey: 'id', // Для таблицы нужен accessorKey
      cell: channel => (
        <div className="flex items-center space-x-2">
          {onChannelSelect && (
            <Button
              variant="default"
              size="sm"
              onClick={() => onChannelSelect(channel)}
            >
              Выбрать
            </Button>
          )}
        </div>
      ),
    },
  ];

  if (channels.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 text-6xl mb-4">📡</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Нет каналов</h3>
        <p className="text-gray-600 mb-6">
          Добавьте первый канал для начала анализа
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <SimpleTable data={sortedChannels} columns={columns} />
    </div>
  );
};

export { ChannelsList };
