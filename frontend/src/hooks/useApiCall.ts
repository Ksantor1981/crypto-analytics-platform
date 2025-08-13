import { useState, useEffect } from 'react';
import { ApiResponse } from '@/lib/api';

export function useApiCall<T>(
  apiCall: () => Promise<ApiResponse<T>>,
  deps: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiCall();
      if (response.data) {
        setData(response.data);
      } else if (response.error) {
        setError(response.error);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;

    fetchData().then(() => {
      if (!mounted) {
        // Component unmounted, ignore
      }
    });

    return () => {
      mounted = false;
    };
  }, deps);

  return { data, loading, error, refetch: fetchData };
}

// Специализированные хуки для часто используемых API вызовов
export function useChannels(page = 1, limit = 20) {
  const apiCall = async () => {
    const { default: apiClient } = await import('@/lib/api');
    return apiClient.getChannels(page, limit);
  };

  return useApiCall(apiCall, [page, limit]);
}

export function useSignals(channelId?: number, page = 1, limit = 20) {
  const apiCall = async () => {
    const { default: apiClient } = await import('@/lib/api');
    return apiClient.getSignals(channelId, page, limit);
  };

  return useApiCall(apiCall, [channelId, page, limit]);
}

export function useChannel(id: number) {
  const apiCall = async () => {
    const { default: apiClient } = await import('@/lib/api');
    return apiClient.getChannel(id);
  };

  return useApiCall(apiCall, [id]);
}
