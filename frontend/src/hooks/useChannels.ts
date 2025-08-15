import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Channel } from '@/types';

interface UseChannelsFilters {
  status?: string;
  type?: string;
  search?: string;
}

interface UseChannelsResult {
  channels: Channel[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
  createChannel: (data: Omit<Channel, 'id'>) => Promise<Channel>;
  updateChannel: (id: string, data: Partial<Omit<Channel, 'id'>>) => Promise<Channel>;
  deleteChannel: (id: string) => Promise<void>;
}

export const useChannels = (filters: UseChannelsFilters = {}): UseChannelsResult => {
  const queryClient = useQueryClient();

  const {
    data: channels = [],
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['channels', filters],
    queryFn: async () => {
      const response = await apiClient.getChannels();
      return response || [];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  const createChannelMutation = useMutation<Channel, Error, Omit<Channel, 'id'>>({
    mutationFn: (data) => apiClient.createChannel(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
  });

  const updateChannelMutation = useMutation<Channel, Error, { id: string; data: Partial<Omit<Channel, 'id'>> }>({
    mutationFn: ({ id, data }) => apiClient.updateChannel(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
  });

  const deleteChannelMutation = useMutation<void, Error, string>({
    mutationFn: (id) => apiClient.deleteChannel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
  });

  return {
    channels,
    isLoading,
    error,
    refetch,
    createChannel: createChannelMutation.mutateAsync,
    updateChannel: (id: string, data: Partial<Omit<Channel, 'id'>>) => updateChannelMutation.mutateAsync({ id, data }),
    deleteChannel: deleteChannelMutation.mutateAsync,
  };
};

export const useChannel = (id: string) => {
  const queryClient = useQueryClient();

  const {
    data: channel,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['channel', id],
    queryFn: async () => {
      const response = await apiClient.getChannel(id);
      return response;
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });

  const updateChannelMutation = useMutation<Channel, Error, Partial<Omit<Channel, 'id'>>>({
    mutationFn: (data) => apiClient.updateChannel(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channel', id] });
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
  });

  return {
    channel,
    isLoading,
    error,
    refetch,
    updateChannel: updateChannelMutation.mutateAsync,
  };
};
