import { Channel as BaseChannel } from './index';

// Расширенный тип для отображения на фронтенде
export interface ChannelView extends BaseChannel {
  // Поля из моковых данных, которые могут отсутствовать в API
  url?: string; // Добавлено для ChannelActions
  avatar?: string;
  rating?: number;
  accuracy?: number;
  roi?: number;
  subscribers?: number;
  signals?: number;
  category?: string;
  isFollowing?: boolean;
  lastSignal?: string;
  priceRange?: string;
  riskLevel?: 'low' | 'medium' | 'high';
}
