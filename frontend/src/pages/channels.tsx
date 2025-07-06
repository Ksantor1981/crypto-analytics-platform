import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { DashboardLayout } from '@/components/dashboard';
import { ChannelsList, ChannelCard, ChannelsFilter } from '@/components/channels';
import { ProtectedRoute } from '@/components/auth';
import { Button } from '@/components/ui/Button';
import { channelsApi } from '@/lib/api';
import { Channel, ChannelFilters } from '@/types';

const ChannelsPage: React.FC = () => {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [filters, setFilters] = useState<ChannelFilters>({});
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0
  });

  const fetchChannels = async () => {
    try {
      setIsLoading(true);
      const response = await channelsApi.getChannels({
        limit: pagination.limit,
        offset: (pagination.page - 1) * pagination.limit,
        ...filters
      });
      
      setChannels(response.data.items);
      setPagination(prev => ({
        ...prev,
        total: response.data.total
      }));
    } catch (error) {
      console.error('Error fetching channels:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchChannels();
  }, [pagination.page, filters]);

  const handleFiltersChange = (newFilters: ChannelFilters) => {
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleResetFilters = () => {
    setFilters({});
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleSubscribe = async (channel: Channel) => {
    try {
      await channelsApi.subscribeToChannel(channel.id);
      // Refresh channels list
      fetchChannels();
    } catch (error) {
      console.error('Error subscribing to channel:', error);
    }
  };

  const handleUnsubscribe = async (channel: Channel) => {
    try {
      await channelsApi.unsubscribeFromChannel(channel.id);
      // Refresh channels list
      fetchChannels();
    } catch (error) {
      console.error('Error unsubscribing from channel:', error);
    }
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Каналы - Crypto Analytics Platform</title>
        <meta name="description" content="Список и рейтинг криптовалютных каналов" />
      </Head>
      
      <DashboardLayout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Каналы</h1>
              <p className="text-gray-600 mt-1">
                Обзор и рейтинг криптовалютных каналов
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Button
                  variant={viewMode === 'list' ? 'primary' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                >
                  📋 Список
                </Button>
                <Button
                  variant={viewMode === 'grid' ? 'primary' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                >
                  ⊞ Сетка
                </Button>
              </div>
              <Button variant="primary">
                ➕ Добавить канал
              </Button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-2xl font-bold text-gray-900">{pagination.total}</div>
              <div className="text-sm text-gray-600">Всего каналов</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-2xl font-bold text-green-600">
                {channels.filter(c => c.status === 'active').length}
              </div>
              <div className="text-sm text-gray-600">Активных</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-2xl font-bold text-blue-600">
                {channels.length > 0 ? (channels.reduce((sum, c) => sum + c.accuracy, 0) / channels.length).toFixed(1) : 0}%
              </div>
              <div className="text-sm text-gray-600">Средняя точность</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-2xl font-bold text-purple-600">
                {channels.reduce((sum, c) => sum + c.signals_count, 0)}
              </div>
              <div className="text-sm text-gray-600">Всего сигналов</div>
            </div>
          </div>

          {/* Filters */}
          <ChannelsFilter
            filters={filters}
            onFiltersChange={handleFiltersChange}
            onReset={handleResetFilters}
          />

          {/* Channels List/Grid */}
          {viewMode === 'list' ? (
            <ChannelsList
              channels={channels}
              isLoading={isLoading}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {isLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="bg-white rounded-lg shadow p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <div className="w-12 h-12 bg-gray-200 rounded-full"></div>
                        <div>
                          <div className="w-24 h-4 bg-gray-200 rounded mb-2"></div>
                          <div className="w-16 h-3 bg-gray-200 rounded"></div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="w-full h-3 bg-gray-200 rounded"></div>
                        <div className="w-3/4 h-3 bg-gray-200 rounded"></div>
                        <div className="w-1/2 h-3 bg-gray-200 rounded"></div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                channels.map((channel) => (
                  <ChannelCard
                    key={channel.id}
                    channel={channel}
                    onSubscribe={handleSubscribe}
                    onUnsubscribe={handleUnsubscribe}
                    isSubscribed={channel.is_subscribed}
                  />
                ))
              )}
            </div>
          )}

          {/* Pagination */}
          {pagination.total > pagination.limit && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Показано {Math.min(pagination.page * pagination.limit, pagination.total)} из {pagination.total} каналов
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                  disabled={pagination.page === 1}
                >
                  Назад
                </Button>
                <span className="text-sm text-gray-600">
                  Страница {pagination.page} из {Math.ceil(pagination.total / pagination.limit)}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                  disabled={pagination.page >= Math.ceil(pagination.total / pagination.limit)}
                >
                  Вперед
                </Button>
              </div>
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
};

export default ChannelsPage; 