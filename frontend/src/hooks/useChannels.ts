import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { channelsApi } from '@/lib/api/channels';
import { Channel, ChannelFilters } from '@/types';
import { useToast } from '@/contexts/ToastContext';

export const useChannels = () => {
  const queryClient = useQueryClient();
  const { showSuccess, showError } = useToast();
  const [filters, setFilters] = useState<ChannelFilters>({});

  const { data: channels, isLoading } = useQuery({
    queryKey: ['channels', filters],
    queryFn: () => channelsApi.getChannels(filters),
  });

  const createChannelMutation = useMutation({
    mutationFn: channelsApi.createChannel,
    onSuccess: data => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      showSuccess('Канал создан', `Канал "${data.name}" успешно добавлен`);
    },
    onError: error => {
      showError('Ошибка', 'Не удалось создать канал');
    },
  });

  const updateChannelMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Channel> }) =>
      channelsApi.updateChannel(id, data),
    onSuccess: data => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      showSuccess('Канал обновлен', `Канал "${data.name}" успешно обновлен`);
    },
    onError: error => {
      showError('Ошибка', 'Не удалось обновить канал');
    },
  });

  const deleteChannelMutation = useMutation({
    mutationFn: channelsApi.deleteChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      showSuccess('Канал удален', 'Канал успешно удален');
    },
    onError: error => {
      showError('Ошибка', 'Не удалось удалить канал');
    },
  });

  return {
    channels,
    isLoading,
    filters,
    setFilters,
    createChannel: createChannelMutation.mutate,
    updateChannel: updateChannelMutation.mutate,
    deleteChannel: deleteChannelMutation.mutate,
    isCreating: createChannelMutation.isPending,
    isUpdating: updateChannelMutation.isPending,
    isDeleting: deleteChannelMutation.isPending,
  };
};

export const useChannel = (id: string) => {
  const queryClient = useQueryClient();
  const { showSuccess, showError } = useToast();
  const { handleError } = useErrorHandler();

  const {
    data: channel,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['channel', id],
    queryFn: () => channelsApi.getChannel(id),
    select: data => data.data,
    enabled: !!id,
    onError: error => {
      handleError(error, 'Не удалось загрузить информацию о канале');
    },
  });

  const updateChannelMutation = useMutation({
    mutationFn: (data: Partial<Channel>) => channelsApi.updateChannel(id, data),
    onSuccess: data => {
      queryClient.invalidateQueries({ queryKey: ['channel', id] });
      queryClient.invalidateQueries({ queryKey: ['channels'] });
      showSuccess('Канал обновлен', `Канал "${data.name}" успешно обновлен`);
    },
    onError: error => {
      handleError(error, 'Не удалось обновить канал');
    },
  });

  const subscribeToChannelMutation = useMutation({
    mutationFn: () => channelsApi.subscribeToChannel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channel', id] });
      showSuccess('Подписка оформлена', 'Вы успешно подписались на канал');
    },
    onError: error => {
      handleError(error, 'Не удалось оформить подписку');
    },
  });

  const unsubscribeFromChannelMutation = useMutation({
    mutationFn: () => channelsApi.unsubscribeFromChannel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channel', id] });
      showSuccess('Подписка отменена', 'Вы успешно отписались от канала');
    },
    onError: error => {
      handleError(error, 'Не удалось отменить подписку');
    },
  });

  return {
    channel,
    isLoading,
    error,
    updateChannel: updateChannelMutation.mutateAsync,
    subscribeToChannel: subscribeToChannelMutation.mutateAsync,
    unsubscribeFromChannel: unsubscribeFromChannelMutation.mutateAsync,
    isUpdating: updateChannelMutation.isPending,
    isSubscribing: subscribeToChannelMutation.isPending,
    isUnsubscribing: unsubscribeFromChannelMutation.isPending,
  };
};
