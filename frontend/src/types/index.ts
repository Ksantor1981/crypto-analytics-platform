// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// User Types
export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_premium: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserProfile extends User {
  first_name?: string;
  last_name?: string;
  phone?: string;
  telegram_username?: string;
  preferred_language: string;
  timezone: string;
}

// Authentication Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// Channel Types
export interface Channel {
  id: string;
  name: string;
  telegram_id: string;
  description?: string;
  subscriber_count: number;
  is_active: boolean;
  accuracy_rate: number;
  total_signals: number;
  successful_signals: number;
  avg_roi: number;
  created_at: string;
  updated_at: string;
}

export interface ChannelStats {
  total_signals: number;
  successful_signals: number;
  accuracy_rate: number;
  avg_roi: number;
  best_month: string;
  worst_month: string;
  performance_trend: 'up' | 'down' | 'stable';
}

// Signal Types
export type SignalType = 'LONG' | 'SHORT';
export type SignalStatus = 'PENDING' | 'ACTIVE' | 'PARTIAL' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface Signal {
  id: string;
  channel_id: string;
  channel_name: string;
  symbol: string;
  type: SignalType;
  status: SignalStatus;
  entry_price: number;
  current_price?: number;
  stop_loss?: number;
  take_profit_1?: number;
  take_profit_2?: number;
  take_profit_3?: number;
  leverage?: number;
  confidence_score: number;
  roi?: number;
  created_at: string;
  updated_at: string;
  closed_at?: string;
}

export interface SignalStats {
  total_signals: number;
  active_signals: number;
  completed_signals: number;
  failed_signals: number;
  avg_roi: number;
  best_signal_roi: number;
  worst_signal_roi: number;
  accuracy_rate: number;
}

// Subscription Types
export interface SubscriptionPlan {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  interval: 'month' | 'year';
  features: string[];
  is_popular: boolean;
  stripe_price_id: string;
}

export interface UserSubscription {
  id: string;
  user_id: string;
  plan_id: string;
  plan_name: string;
  status: 'active' | 'cancelled' | 'expired';
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  stripe_subscription_id: string;
}

// ML Prediction Types
export interface MLPrediction {
  success_probability: number;
  confidence_score: number;
  recommendation: 'STRONG_BUY' | 'BUY' | 'NEUTRAL' | 'SELL' | 'STRONG_SELL';
  risk_score: number;
  feature_importance: Record<string, number>;
  model_version: string;
  prediction_timestamp: string;
}

export interface MLPredictionRequest {
  channel_accuracy: number;
  signal_strength: number;
  market_trend: number;
  volatility: number;
  volume_profile: number;
  risk_reward_ratio: number;
  time_of_day: number;
}

// UI Types
export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface TableColumn<T> {
  key: keyof T;
  title: string;
  width?: string;
  sortable?: boolean;
  render?: (value: any, record: T) => React.ReactNode;
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }[];
}

// Filter Types
export interface ChannelFilters {
  search?: string;
  min_accuracy?: number;
  min_signals?: number;
  sort_by?: 'accuracy' | 'signals' | 'roi' | 'created_at';
  sort_order?: 'asc' | 'desc';
}

export interface SignalFilters {
  channel_id?: string;
  symbol?: string;
  type?: SignalType;
  status?: SignalStatus;
  date_from?: string;
  date_to?: string;
  sort_by?: 'created_at' | 'roi' | 'confidence';
  sort_order?: 'asc' | 'desc';
}

// Error Types
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

export interface FormError {
  field: string;
  message: string;
}

// Navigation Types
export interface NavItem {
  name: string;
  href: string;
  icon?: React.ComponentType<{ className?: string }>;
  current?: boolean;
  children?: NavItem[];
}

// Theme Types
export type Theme = 'light' | 'dark';

export interface ThemeConfig {
  theme: Theme;
  toggleTheme: () => void;
} 