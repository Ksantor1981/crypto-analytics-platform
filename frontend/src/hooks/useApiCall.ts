import { useState, useEffect } from 'react';

export function useApiCall<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiCall();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    execute();
  }, dependencies);

  return {
    data,
    loading,
    error,
    refetch: execute
  };
}

// Специализированные хуки для часто используемых API вызовов
export function useChannels(page = 1, limit = 20) {
  const apiCall = async () => {
    const { apiClient } = await import('@/lib/api');
    return apiClient.getChannels();
  };

  return useApiCall(apiCall, [page, limit]);
}

export function useSignals(channelId?: string, page = 1, limit = 20) {
  const apiCall = async () => {
    const { apiClient } = await import('@/lib/api');
    return apiClient.getSignals(channelId, page, limit);
  };

  return useApiCall(apiCall, [channelId, page, limit]);
}

export function useChannel(id: string) {
  const apiCall = async () => {
    const { apiClient } = await import('@/lib/api');
    return apiClient.getChannel(id);
  };

  return useApiCall(apiCall, [id]);
}
