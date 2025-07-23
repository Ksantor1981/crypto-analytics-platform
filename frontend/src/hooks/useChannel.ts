import { useQuery } from 'react-query';
import axios from 'axios';

// 1. Типы данных для канала (на основе моковых данных)
interface ChannelSignal {
  id: number;
  pair: string;
  type: 'LONG' | 'SHORT';
  entryPrice: number;
  targetPrice: number;
  stopLoss: number;
  status: 'open' | 'closed' | 'failed';
  timestamp: string;
  currentPrice?: number;
  exitPrice?: number;
  pnl?: number;
}

export interface ChannelDetails {
  id: number;
  name: string;
  description: string;
  accuracy: number;
  signals: number;
  roi: number;
  subscribers: number;
  rating: number;
  avatar: string;
  category: string;
  status: 'active' | 'pending' | 'error';
  isFollowing: boolean;
  lastSignal: string;
  priceRange: string;
  riskLevel: 'low' | 'medium' | 'high' | 'extreme';
  joinedDate: string;
  totalTrades: number;
  winRate: number;
  avgReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  monthlyGrowth: number[];
  recentSignals: ChannelSignal[];
}

// 2. Функция для загрузки данных с API
const fetchChannelById = async (channelId: string): Promise<ChannelDetails> => {
  const { data } = await axios.get(`/api/v1/channels/${channelId}`);
  return data;
};

// 3. Кастомный хук для использования в компонентах
export const useChannel = (channelId: string | undefined) => {
  return useQuery<ChannelDetails, Error>(
    ['channel', channelId], // Ключ для кэширования
    () => fetchChannelById(channelId!),
    {
      // Хук не будет выполняться, если channelId не определен
      enabled: !!channelId,
    }
  );
};
