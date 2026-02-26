export interface Signal {
  id: string;
  channel_id?: string;
  channel_name?: string;
  asset?: string;
  symbol?: string;
  pair?: string;
  direction: 'long' | 'short' | 'BUY' | 'SELL';
  entry_price?: number;
  target_price?: number;
  tp1_price?: number;
  stop_loss?: number;
  exit_price?: number;
  original_text?: string;
  status: 'active' | 'completed' | 'cancelled' | 'failed' | 'pending' | 'PENDING' | 'SUCCESSFUL' | 'FAILED' | 'CANCELLED';
  confidence_score?: number;
  pnl?: number;
  profit_loss?: number;
  created_at: string;
  updated_at?: string;
}

export interface SignalFilters {
  status?: string;
  direction?: string;
  pair?: string;
  channel_id?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface Channel {
  id: string;
  name: string;
  username?: string;
  description?: string;
  platform: string;
  url?: string;
  category?: string;
  is_active: boolean;
  is_verified: boolean;
  subscribers_count?: number;
  signals_count?: number;
  successful_signals?: number;
  accuracy?: number;
  expected_accuracy?: number;
  priority?: number;
  status?: string;
  average_roi?: number;
  created_at?: string;
  updated_at?: string;
}

export interface ChannelFilters {
  platform?: string;
  category?: string;
  is_active?: boolean;
  search?: string;
}

export type ChannelType = 'telegram' | 'reddit' | 'web';
export type ChannelSortField = 'name' | 'accuracy' | 'signals_count' | 'created_at';
export type SortOrder = 'asc' | 'desc';

export interface User {
  id: string;
  name: string;
  username: string;
  email: string;
  avatar?: string;
  joinDate: string;
  role: string;
  subscription: {
    plan: string;
    status: string;
    price: number;
  };
  stats: {
    channelsFollowed: number;
    successRate: number;
    profit: number;
    totalProfit: number;
    totalSignals: number;
    winRate: number;
    totalReturn: number;
    daysActive: number;
  };
  settings: {
    emailNotifications: boolean;
    pushNotifications: boolean;
    telegramAlerts: boolean;
    weeklyReports: boolean;
    darkMode: boolean;
    language: string;
    timezone: string;
  };
}

export interface APIUser {
  id: number;
  email: string;
  name?: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  subscription_type?: string;
  subscription_tier?: string;
  created_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  features: string[];
  is_current: boolean;
}
