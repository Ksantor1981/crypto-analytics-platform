// Экспорт всех типов для использования в компонентах
export type { 
  User, 
  Channel, 
  Signal, 
  PredictionRequest, 
  PredictionResponse, 
  ApiResponse 
} from '@/lib/api';

// Дополнительные типы для UI
export interface ApiError {
  message: string;
  status: number;
  field?: string;
}

export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

export interface PaginationParams {
  page: number;
  limit: number;
}

export interface ChannelFilters {
  rating_min?: number;
  rating_max?: number;
  subscribers_min?: number;
  search?: string;
}

export interface SignalFilters {
  channel_id?: number;
  symbol?: string;
  signal_type?: 'LONG' | 'SHORT';
  date_from?: string;
  date_to?: string;
  confidence_min?: number;
}
