import { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { signalsApi } from '@/lib/api';
import { Signal, SignalFilters } from '@/types';

export const useSignals = (filters?: SignalFilters) => {
  const queryClient = useQueryClient();

  const {
    data: signals = [],
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['signals', filters],
    queryFn: () => signalsApi.getSignals(filters),
    select: (data) => data.data
  });

  const analyzeSignalMutation = useMutation({
    mutationFn: signalsApi.analyzeSignal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signals'] });
    }
  });

  const updateSignalMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Signal> }) =>
      signalsApi.updateSignal(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signals'] });
    }
  });

  return {
    signals,
    isLoading,
    error,
    refetch,
    analyzeSignal: analyzeSignalMutation.mutateAsync,
    updateSignal: updateSignalMutation.mutateAsync,
    isAnalyzing: analyzeSignalMutation.isPending,
    isUpdating: updateSignalMutation.isPending
  };
};

export const useSignal = (id: string) => {
  const queryClient = useQueryClient();

  const {
    data: signal,
    isLoading,
    error
  } = useQuery({
    queryKey: ['signal', id],
    queryFn: () => signalsApi.getSignal(id),
    select: (data) => data.data,
    enabled: !!id
  });

  const analyzeSignalMutation = useMutation({
    mutationFn: () => signalsApi.analyzeSignal(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signal', id] });
    }
  });

  const updateSignalMutation = useMutation({
    mutationFn: (data: Partial<Signal>) => signalsApi.updateSignal(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signal', id] });
      queryClient.invalidateQueries({ queryKey: ['signals'] });
    }
  });

  return {
    signal,
    isLoading,
    error,
    analyzeSignal: analyzeSignalMutation.mutateAsync,
    updateSignal: updateSignalMutation.mutateAsync,
    isAnalyzing: analyzeSignalMutation.isPending,
    isUpdating: updateSignalMutation.isPending
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
    const avgPnl = signalsWithPnl.length > 0 ? totalPnl / signalsWithPnl.length : 0;
    
    const winRate = signalsWithPnl.length > 0 ? (profitable / signalsWithPnl.length) * 100 : 0;
    
    const bestSignal = signalsWithPnl.reduce((best, current) => 
      current.pnl! > (best?.pnl || -Infinity) ? current : best, null as Signal | null
    );
    
    const worstSignal = signalsWithPnl.reduce((worst, current) => 
      current.pnl! < (worst?.pnl || Infinity) ? current : worst, null as Signal | null
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
      shortSignals
    };
  }, [signals]);

  return stats;
}; 