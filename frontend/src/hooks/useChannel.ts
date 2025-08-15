import { useQuery } from 'react-query';
import axios from 'axios';

// 1. Типы данных для канала (на основе моковых данных)
interface ChannelSignal {
  id: number;
  symbol: string;
  type: 'LONG' | 'SHORT';
  entry_price: number;
  target_price?: number;
  stop_loss?: number;
  status: 'open' | 'closed' | 'failed';
  timestamp: string;
  current_price?: number;
  exit_price?: number;
  pnl?: number;
}

export interface ChannelDetails {
  id: number;
  name: string;
  description: string;
  platform: string; // Добавляем platform
  category: string;
  accuracy: number;
  roi: number;
  subscribers: number;
  signals_count: number; // Добавляем signals_count
  rating: number;
  avatar: string;
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
  recent_signals: ChannelSignal[]; // Переименовываем в recent_signals
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
