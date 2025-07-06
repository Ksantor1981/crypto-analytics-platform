'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Card, CardBody } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Table } from '@/components/ui/Table';
import { Channel } from '@/types';
import { formatDate } from '@/lib/utils';

interface ChannelsListProps {
  channels: Channel[];
  isLoading?: boolean;
  onChannelSelect?: (channel: Channel) => void;
}

export const ChannelsList: React.FC<ChannelsListProps> = ({
  channels,
  isLoading = false,
  onChannelSelect
}) => {
  const [sortBy, setSortBy] = useState<'name' | 'accuracy' | 'signals_count' | 'created_at'>('accuracy');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const sortedChannels = [...channels].sort((a, b) => {
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
        return <Badge variant="success">Активен</Badge>;
      case 'inactive':
        return <Badge variant="secondary">Неактивен</Badge>;
      case 'error':
        return <Badge variant="danger">Ошибка</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 80) return 'text-green-600';
    if (accuracy >= 60) return 'text-yellow-600';
    return 'text-red-600';
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
                      <div className="w-32 h-4 bg-gray-200 rounded mb-2"></div>
                      <div className="w-24 h-3 bg-gray-200 rounded"></div>
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

  if (channels.length === 0) {
    return (
      <Card>
        <CardBody className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">📡</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Нет каналов</h3>
          <p className="text-gray-600 mb-6">Добавьте первый канал для начала анализа</p>
          <Button variant="primary">
            Добавить канал
          </Button>
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
                    onClick={() => handleSort('name')}
                    className="flex items-center space-x-1 font-medium text-gray-700 hover:text-gray-900"
                  >
                    <span>Канал</span>
                    {sortBy === 'name' && (
                      <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
                <th className="text-left py-3 px-4">Статус</th>
                <th className="text-left py-3 px-4">
                  <button
                    onClick={() => handleSort('accuracy')}
                    className="flex items-center space-x-1 font-medium text-gray-700 hover:text-gray-900"
                  >
                    <span>Точность</span>
                    {sortBy === 'accuracy' && (
                      <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
                <th className="text-left py-3 px-4">
                  <button
                    onClick={() => handleSort('signals_count')}
                    className="flex items-center space-x-1 font-medium text-gray-700 hover:text-gray-900"
                  >
                    <span>Сигналы</span>
                    {sortBy === 'signals_count' && (
                      <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
                <th className="text-left py-3 px-4">
                  <button
                    onClick={() => handleSort('created_at')}
                    className="flex items-center space-x-1 font-medium text-gray-700 hover:text-gray-900"
                  >
                    <span>Добавлен</span>
                    {sortBy === 'created_at' && (
                      <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </button>
                </th>
                <th className="text-right py-3 px-4">Действия</th>
              </tr>
            </thead>
            <tbody>
              {sortedChannels.map((channel) => (
                <tr key={channel.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4">
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
                  </td>
                  <td className="py-3 px-4">
                    {getStatusBadge(channel.status)}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`font-medium ${getAccuracyColor(channel.accuracy)}`}>
                      {channel.accuracy.toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-gray-900">{channel.signals_count}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-gray-600">{formatDate(channel.created_at)}</span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <Link href={`/channels/${channel.id}`}>
                        <Button variant="outline" size="sm">
                          Подробнее
                        </Button>
                      </Link>
                      {onChannelSelect && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => onChannelSelect(channel)}
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