'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatDate } from '@/lib/utils';
import { Channel } from '@/types';

interface ChannelCardProps {
  channel: Channel;
  onSubscribe?: (channel: Channel) => void;
}

const ChannelCard: React.FC<ChannelCardProps> = ({ channel, onSubscribe }) => {
  const avgProfit = channel.avg_profit ?? channel.avg_roi ?? 0;
  const subscribersCount = channel.subscribers_count ?? 0;

  const getStatusBadge = () => {
    switch (channel.status) {
      case 'active':
        return <Badge variant="default">Активен</Badge>;
      case 'inactive':
        return <Badge variant="secondary">Неактивен</Badge>;
      case 'error':
        return <Badge variant="destructive">Ошибка</Badge>;
      default:
        return <Badge variant="outline">Неизвестен</Badge>;
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-blue-600 font-semibold text-xl">
                {channel.name.slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div>
              <h3 className="text-lg font-semibold">{channel.name}</h3>
              <p className="text-sm text-gray-500">
                Создан: {formatDate(channel.created_at)}
              </p>
            </div>
          </div>
          {getStatusBadge()}
        </div>

        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className="text-lg font-semibold text-blue-600">
              {channel.accuracy?.toFixed(1) || 0}%
            </div>
            <div className="text-xs text-gray-600">Точность</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-green-600">
              {avgProfit.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-600">Доход</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-purple-600">
              {subscribersCount}
            </div>
            <div className="text-xs text-gray-600">Подписчиков</div>
          </div>
        </div>

        <div className="flex space-x-2">
          <Button 
            variant="outline" 
            className="w-full"
            onClick={() => onSubscribe?.(channel)}
          >
            Подписаться
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export { ChannelCard };
