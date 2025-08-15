import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Signal, SignalFilters } from '@/types';
import { apiClient } from '@/lib/api';

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
  initialFilters: SignalFilters = {}
): UseSignalsResult {
  const [filters, setFilters] = useState<SignalFilters>(initialFilters);
  const queryClient = useQueryClient();

  const {
    data: signals = [],
    isLoading,
    error,
    refetch 
  } = useQuery({
    queryKey: ['signals', filters],
    queryFn: async () => {
      const response = await apiClient.getSignals();
      return response || [];
    },
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });

  const analyzeSignalMutation = useMutation<Signal, Error, string>({
    mutationFn: async (id: string) => {
      // Временно возвращаем сигнал как есть, так как analyzeSignal не реализован в API
      const signal = signals.find(s => s.id === id);
      if (!signal) throw new Error('Signal not found');
      return signal;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signals'] });
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
    });
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
    isAnalyzing: analyzeSignalMutation.isPending,
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
    queryFn: async () => {
      const response = await apiClient.getSignal(id);
      return response;
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });

  const analyzeSignalMutation = useMutation<Signal, Error, void>({
    mutationFn: async () => {
      // Временно возвращаем сигнал как есть
      if (!signal) throw new Error('Signal not found');
      return signal;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signal', id] });
    },
  });

  return {
    signal,
    isLoading,
    error,
    analyzeSignal: analyzeSignalMutation.mutateAsync,
    isAnalyzing: analyzeSignalMutation.isPending,
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
