import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from 'react-query';
import { Signal, SignalFilters } from '@/types';
import { signalsApi } from '@/lib/api/signals';

interface UseSignalsResult {
  signals: Signal[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
  filteredSignals: Signal[];
  applyFilters: (filters: SignalFilters) => void;
  analyzeSignal: (id: string) => Promise<Signal>;
  isAnalyzing: boolean;
  stats: {
    total: number;
    active: number;
    completed: number;
    cancelled: number;
    failed: number;
    longSignals: number;
    shortSignals: number;
    profitable: number;
    unprofitable: number;
    totalPnl: number;
    bestSignal?: Signal;
    worstSignal?: Signal;
  };
}

export function useSignals(
  initialFilters: SignalFilters = {},
  queryOptions: UseQueryOptions<Signal[], Error> = {}
): UseSignalsResult {
  const [filters, setFilters] = useState<SignalFilters>(initialFilters);
  const queryClient = useQueryClient();
  // Состояние сортировки убрано - не используется

  const {
    data: signals = [],
    isLoading,
    error,
    refetch 
  } = useQuery<Signal[], Error>(
    ['signals', filters],
    () => signalsApi.getSignals(filters),
    {
      ...queryOptions,
      onError: (error: Error) => {
        console.error('Failed to fetch signals:', error);
      }
    }
  );

  const analyzeSignalMutation = useMutation({
    mutationFn: (id: string) => signalsApi.analyzeSignal(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signals'] });
    },
    onError: (error: Error) => {
      console.error('Failed to analyze signal:', error);
    },
  });

  const applyFilters = (newFilters: SignalFilters) => {
    setFilters(prevFilters => ({ ...prevFilters, ...newFilters }));
  };

  const filteredSignals = useMemo(() => {
    return signals.filter(signal => {
      if (filters.status && signal.status !== filters.status) return false;
      if (filters.direction && signal.direction !== filters.direction) return false;
      if (filters.pair && signal.pair !== filters.pair) return false;
      
      if (filters.date_from) {
        const dateFrom = new Date(filters.date_from);
        const signalDate = new Date(signal.created_at);
        if (signalDate < dateFrom) return false;
      }

      if (filters.date_to) {
        const dateTo = new Date(filters.date_to);
        const signalDate = new Date(signal.created_at);
        if (signalDate > dateTo) return false;
      }

      return true;
    }); // Сортировка удалена - не используется
  }, [signals, filters]);

  const stats = useMemo(() => {
    const total = signals.length;
    const active = signals.filter(s => s.status === 'active').length;
    const completed = signals.filter(s => s.status === 'completed').length;
    const cancelled = signals.filter(s => s.status === 'cancelled').length;
    const failed = signals.filter(s => s.status === 'failed').length;

    const signalsWithPnl = signals.filter(s => s.pnl !== undefined);
    const profitable = signalsWithPnl.filter(s => (s.pnl ?? 0) > 0).length;
    const unprofitable = signalsWithPnl.filter(s => (s.pnl ?? 0) < 0).length;
    const totalPnl = signalsWithPnl.reduce((sum, s) => sum + (s.pnl ?? 0), 0);

    const longSignals = signals.filter(s => s.direction === 'long').length;
    const shortSignals = signals.filter(s => s.direction === 'short').length;

    const bestSignal = signalsWithPnl.reduce((best, current) => 
      (current.pnl ?? 0) > (best?.pnl ?? -Infinity) ? current : best, 
      undefined as Signal | undefined
    );

    const worstSignal = signalsWithPnl.reduce((worst, current) => 
      (current.pnl ?? 0) < (worst?.pnl ?? Infinity) ? current : worst, 
      undefined as Signal | undefined
    );

    return {
      total,
      active,
      completed,
      cancelled,
      failed,
      longSignals,
      shortSignals,
      profitable,
      unprofitable,
      totalPnl,
      bestSignal,
      worstSignal
    };
  }, [signals]);

  return {
    signals,
    isLoading,
    error,
    refetch,
    filteredSignals,
    applyFilters,
    analyzeSignal: analyzeSignalMutation.mutateAsync,
    isAnalyzing: analyzeSignalMutation.isLoading,
    stats
  };
}

export const useSignal = (id: string) => {
  const queryClient = useQueryClient();

  const {
    data: signal,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['signal', id],
    queryFn: () => signalsApi.getSignalById(id),
    // select убрано
    enabled: !!id,
  });

  const analyzeSignalMutation = useMutation({
    mutationFn: () => signalsApi.analyzeSignal(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signal', id] });
    },
  });

  const updateSignalMutation = useMutation({
    mutationFn: (data: Partial<Signal>) => signalsApi.updateSignal(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signal', id] });
      queryClient.invalidateQueries({ queryKey: ['signals'] });
    },
  });

  return {
    signal,
    isLoading,
    error,
    analyzeSignal: analyzeSignalMutation.mutateAsync,
    updateSignal: updateSignalMutation.mutateAsync,
    isAnalyzing: analyzeSignalMutation.isLoading,
    isUpdating: updateSignalMutation.isLoading,
  };
};

export const useSignalStats = (signals: Signal[]) => {
  const stats = useMemo(() => {
    const total = signals.length;
    const active = signals.filter(s => s.status === 'active').length;
    const completed = signals.filter(s => s.status === 'completed').length;
    const failed = signals.filter(s => s.status === 'failed').length;

    const signalsWithPnl = signals.filter(s => s.pnl !== undefined);
    const profitable = signalsWithPnl.filter(s => s.pnl! > 0).length;
    const unprofitable = signalsWithPnl.filter(s => s.pnl! < 0).length;

    const totalPnl = signalsWithPnl.reduce((sum, s) => sum + s.pnl!, 0);
    const avgPnl =
      signalsWithPnl.length > 0 ? totalPnl / signalsWithPnl.length : 0;

    const winRate =
      signalsWithPnl.length > 0
        ? (profitable / signalsWithPnl.length) * 100
        : 0;

    const bestSignal = signalsWithPnl.reduce(
      (best, current) =>
        current.pnl! > (best?.pnl || -Infinity) ? current : best,
      null as Signal | null
    );

    const worstSignal = signalsWithPnl.reduce(
      (worst, current) =>
        current.pnl! < (worst?.pnl || Infinity) ? current : worst,
      null as Signal | null
    );

    const longSignals = signals.filter(s => s.direction === 'long').length;
    const shortSignals = signals.filter(s => s.direction === 'short').length;

    return {
      total,
      active,
      completed,
      failed,
      profitable,
      unprofitable,
      totalPnl,
      avgPnl,
      winRate,
      bestSignal,
      worstSignal,
      longSignals,
      shortSignals,
    };
  }, [signals]);

  return stats;
};
