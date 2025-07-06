'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardBody, CardFooter } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Channel } from '@/types';
import { formatDate } from '@/lib/utils';

interface ChannelCardProps {
  channel: Channel;
  onSubscribe?: (channel: Channel) => void;
  onUnsubscribe?: (channel: Channel) => void;
  isSubscribed?: boolean;
}

export const ChannelCard: React.FC<ChannelCardProps> = ({
  channel,
  onSubscribe,
  onUnsubscribe,
  isSubscribed = false
}) => {
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

  return (
    <Card className="h-full">
      <CardBody className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-blue-600 font-semibold">
                {channel.name.slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{channel.name}</h3>
              <p className="text-sm text-gray-600">@{channel.username}</p>
            </div>
          </div>
          {getStatusBadge(channel.status)}
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Точность:</span>
            <span className={`font-medium ${getAccuracyColor(channel.accuracy)}`}>
              {channel.accuracy.toFixed(1)}%
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Сигналов:</span>
            <span className="font-medium text-gray-900">{channel.signals_count}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Подписчики:</span>
            <span className="font-medium text-gray-900">{channel.subscribers_count}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Добавлен:</span>
            <span className="text-sm text-gray-900">{formatDate(channel.created_at)}</span>
          </div>
        </div>

        {channel.description && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600 line-clamp-3">{channel.description}</p>
          </div>
        )}

        {/* Performance indicators */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-lg font-semibold text-green-600">
                +{channel.avg_profit?.toFixed(1) || 0}%
              </div>
              <div className="text-xs text-gray-600">Средняя прибыль</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-blue-600">
                {channel.win_rate?.toFixed(1) || 0}%
              </div>
              <div className="text-xs text-gray-600">Винрейт</div>
            </div>
          </div>
        </div>
      </CardBody>

      <CardFooter className="p-6 pt-0">
        <div className="flex items-center space-x-2 w-full">
          <Link href={`/channels/${channel.id}`} className="flex-1">
            <Button variant="outline" className="w-full">
              Подробнее
            </Button>
          </Link>
          
          {isSubscribed ? (
            <Button
              variant="danger"
              className="flex-1"
              onClick={() => onUnsubscribe?.(channel)}
            >
              Отписаться
            </Button>
          ) : (
            <Button
              variant="primary"
              className="flex-1"
              onClick={() => onSubscribe?.(channel)}
            >
              Подписаться
            </Button>
          )}
        </div>
      </CardFooter>
    </Card>
  );
}; 