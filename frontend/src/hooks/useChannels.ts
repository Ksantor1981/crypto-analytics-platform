import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from 'react-query';
import { Channel, ChannelFilters } from '@/types';
import { channelsApi } from '@/lib/api/channels';
// Импорты хуков убраны - не используются

interface UseChannelsResult {
  channels: Channel[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
  filteredChannels: Channel[];
  applyFilters: (filters: ChannelFilters) => void;
  createChannel: (data: Omit<Channel, 'id'>) => Promise<Channel>;
  updateChannel: (id: string, data: Partial<Omit<Channel, 'id'>>) => Promise<Channel>;
  deleteChannel: (id: string) => Promise<void>;
}

export function useChannels(
  initialFilters: ChannelFilters = {},
  queryOptions: UseQueryOptions<Channel[], Error> = {}
): UseChannelsResult {
  const [filters, setFilters] = useState<ChannelFilters>(initialFilters);
  const queryClient = useQueryClient();

  const { 
    data: channels = [], 
    isLoading, 
    error, 
    refetch 
  } = useQuery<Channel[], Error>(
    ['channels', filters],
    () => channelsApi.getChannels(filters),
    {
      ...queryOptions,
      onError: (error: Error) => {
        console.error('Failed to fetch channels:', error);
      }
    }
  );

  const createChannelMutation = useMutation({
    mutationFn: (data: Omit<Channel, 'id'>) => channelsApi.createChannel(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
    onError: (error: Error) => {
      console.error('Failed to create channel:', error);
    },
  });

  const updateChannelMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Omit<Channel, 'id'>> }) => 
      channelsApi.updateChannel(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
    onError: (error: Error) => {
      console.error('Failed to update channel:', error);
    },
  });

  const deleteChannelMutation = useMutation({
    mutationFn: (id: string) => channelsApi.deleteChannel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
    onError: (error: Error) => {
      console.error('Failed to delete channel:', error);
    },
  });

  const applyFilters = useCallback((newFilters: ChannelFilters) => {
    setFilters(prevFilters => ({ ...prevFilters, ...newFilters }));
  }, []);

  const filteredChannels = channels.filter(channel => {
    if (filters.type && channel.type !== filters.type) return false;
    if (filters.status && channel.status !== filters.status) return false;
    if (filters.search && !channel.name.toLowerCase().includes(filters.search.toLowerCase())) return false;
    
    if (filters.accuracy_range) {
      const accuracy = channel.accuracy ?? 0;
      if (typeof filters.accuracy_range === 'string') {
        const [min, max] = filters.accuracy_range.split('-').map(Number);
        if (min !== undefined && accuracy < min) return false;
        if (max !== undefined && accuracy > max) return false;
      } else if (Array.isArray(filters.accuracy_range)) {
        const [min, max] = filters.accuracy_range;
        if (min !== undefined && accuracy < min) return false;
        if (max !== undefined && accuracy > max) return false;
      }
    }

    if (filters.created_from) {
      const createdFrom = new Date(filters.created_from);
      const channelCreatedAt = new Date(channel.created_at);
      if (channelCreatedAt < createdFrom) return false;
    }

    if (filters.created_to) {
      const createdTo = new Date(filters.created_to);
      const channelCreatedAt = new Date(channel.created_at);
      if (channelCreatedAt > createdTo) return false;
    }

    return true;
  });

  return {
    channels,
    isLoading,
    error,
    refetch,
    filteredChannels,
    applyFilters,
    createChannel: createChannelMutation.mutateAsync,
    updateChannel: (id: string, data: Partial<Omit<Channel, 'id'>>) => updateChannelMutation.mutateAsync({ id, data }),
    deleteChannel: deleteChannelMutation.mutateAsync,
  };
}

export const useChannel = (id: string) => {
  const queryClient = useQueryClient();
  // Хуки убраны - заглушки

  const {
    data: channel,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['channel', id],
    queryFn: () => channelsApi.getChannelById(id),
    // select убрано - данные уже правильные
    enabled: !!id,
    onError: error => {
      console.error(error, 'Не удалось загрузить информацию о канале');
    },
  });

  const updateChannelMutation = useMutation({
    mutationFn: (data: Partial<Channel>) => channelsApi.updateChannel(id, data),
    onSuccess: data => {
      queryClient.invalidateQueries({ queryKey: ['channel', id] });
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      console.log('Канал обновлен', `Канал "${data.name}" успешно обновлен`);
    },
    onError: error => {
      console.error(error, 'Не удалось обновить канал');
    },
  });

  const subscribeToChannelMutation = useMutation({
    mutationFn: () => channelsApi.subscribeToChannel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channel', id] });
      console.log('Подписка оформлена', 'Вы успешно подписались на канал');
    },
    onError: error => {
      console.error(error, 'Не удалось оформить подписку');
    },
  });

  const unsubscribeFromChannelMutation = useMutation({
    mutationFn: () => channelsApi.unsubscribeFromChannel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channel', id] });
      console.log('Подписка отменена', 'Вы успешно отписались от канала');
    },
    onError: error => {
      console.error(error, 'Не удалось отменить подписку');
    },
  });

  return {
    channel,
    isLoading,
    error,
    updateChannel: updateChannelMutation.mutateAsync,
    subscribeToChannel: subscribeToChannelMutation.mutateAsync,
    unsubscribeFromChannel: unsubscribeFromChannelMutation.mutateAsync,
    isUpdating: updateChannelMutation.isLoading,
    isSubscribing: subscribeToChannelMutation.isLoading,
    isUnsubscribing: unsubscribeFromChannelMutation.isLoading,
  };
};
