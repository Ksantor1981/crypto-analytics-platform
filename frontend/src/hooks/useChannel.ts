import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

export interface ChannelSignal {
  id: number;
  symbol: string;
  type: 'LONG' | 'SHORT';
  entry_price: number;
  target_price?: number;
  stop_loss?: number;
  status: string;
  timestamp: string;
  pnl?: number;
}

export interface ChannelDetails {
  id: number;
  name: string;
  username?: string;
  description: string;
  platform: string;
  category: string;
  url?: string;
  accuracy: number;
  roi: number;
  subscribers: number;
  signals_count: number;
  successful_signals: number;
  average_roi: number;
  rating: number;
  avatar: string;
  status: string;
  isFollowing: boolean;
  riskLevel: string;
  totalTrades: number;
  winRate: number;
  avgReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  monthlyGrowth: number[];
  recent_signals: ChannelSignal[];
}

const fetchChannelById = async (channelId: string): Promise<ChannelDetails> => {
  const raw = await apiClient.getChannel(channelId);

  let signals: ChannelSignal[] = [];
  try {
    const sigResp = await apiClient.getSignals(channelId);
    const sigData = Array.isArray(sigResp) ? sigResp : (sigResp?.signals || []);
    signals = sigData.map((s: Record<string, unknown>) => ({
      id: s.id as number,
      symbol: (s.asset || s.symbol || '') as string,
      type: (s.direction || 'LONG') as 'LONG' | 'SHORT',
      entry_price: (s.entry_price || 0) as number,
      target_price: (s.tp1_price || undefined) as number | undefined,
      stop_loss: (s.stop_loss || undefined) as number | undefined,
      status: ((s.status as string) || 'open').toLowerCase().includes('hit') ? 'closed'
        : ((s.status as string) || '').includes('SL') ? 'failed' : 'open',
      timestamp: (s.created_at || new Date().toISOString()) as string,
      pnl: (s.profit_loss_percentage || undefined) as number | undefined,
    }));
  } catch {}

  return {
    id: raw.id,
    name: raw.name || 'Unknown',
    username: raw.username,
    description: raw.description || '',
    platform: raw.platform || 'telegram',
    category: raw.category || 'general',
    url: raw.url,
    accuracy: raw.accuracy || 0,
    roi: raw.average_roi || 0,
    subscribers: raw.subscribers_count || 0,
    signals_count: raw.signals_count || 0,
    successful_signals: raw.successful_signals || 0,
    average_roi: raw.average_roi || 0,
    rating: Math.min(5, (raw.accuracy || 0) / 20),
    avatar: raw.platform === 'reddit' ? '🔴' : '📡',
    status: raw.status || 'active',
    isFollowing: false,
    riskLevel: (raw.accuracy || 0) > 70 ? 'low' : (raw.accuracy || 0) > 50 ? 'medium' : 'high',
    totalTrades: raw.signals_count || 0,
    winRate: raw.accuracy || 0,
    avgReturn: raw.average_roi || 0,
    maxDrawdown: 0,
    sharpeRatio: 0,
    monthlyGrowth: [],
    recent_signals: signals,
  };
};

export const useChannel = (channelId: string | undefined) => {
  return useQuery<ChannelDetails, Error>({
    queryKey: ['channel', channelId],
    queryFn: () => fetchChannelById(channelId!),
    enabled: !!channelId,
  });
};
