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
  name?: string;
  role: 'user' | 'admin';
  status: 'active' | 'inactive';
  createdAt: string;
  updatedAt: string;
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
  user: User;
  token: string;
}

// Channel Types
export type ChannelType = 'telegram' | 'reddit' | 'rss' | 'twitter' | 'tradingview';

export interface Channel {
  id: string;
  name: string;
  description?: string;
  url: string;
  type: ChannelType;
  status: 'active' | 'inactive' | 'pending';
  createdAt: string;
  updatedAt: string;
  // Parser-specific configuration
  parser_config?: Record<string, any>;
  // Channel metadata
  category?: string;
  allowed_symbols?: string[];
  min_confidence?: number;
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
export type SignalStatus =
  | 'PENDING'
  | 'ACTIVE'
  | 'PARTIAL'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

export interface Signal {
  id: string;
  channelId: string;
  content: string;
  type: 'buy' | 'sell';
  status: 'active' | 'completed' | 'cancelled';
  createdAt: string;
  updatedAt: string;
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
  type?: Channel['type'];
  status?: Channel['status'];
  search?: string;
}

export interface SignalFilters {
  channelId?: string;
  type?: Signal['type'];
  status?: Signal['status'];
  dateFrom?: string;
  dateTo?: string;
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
