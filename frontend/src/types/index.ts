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

// Базовые типы данных
export type ChannelStatus = 'active' | 'inactive' | 'error' | 'pending';
export type ChannelType = 'telegram' | 'reddit' | 'twitter' | 'custom' | 'rss' | 'tradingview';
export type SignalStatus = 'active' | 'completed' | 'cancelled' | 'failed';
export type SignalDirection = 'long' | 'short';
export type SortOrder = 'asc' | 'desc';

// Типы для сортировки
export type ChannelSortField = 
  | 'id' 
  | 'name' 
  | 'accuracy' 
  | 'signals_count' 
  | 'created_at';

export type SignalSortField = 
  | 'id' 
  | 'pair' 
  | 'status' 
  | 'created_at' 
  | 'pnl';

// API User тип (для данных с бэкенда)
export interface APIUser {
  id: number;
  email: string;
  subscription_type: 'free' | 'pro' | 'enterprise';
  is_active: boolean;
  name?: string;
}

// UI User тип (для фронтенда)
export interface User {
  id: string;
  name: string;
  username: string;
  email: string;
  avatar?: string;
  joinDate: string;
  
  // ДОБАВЛЯЕМ РОЛЬ - это единственное изменение
  role: 'user' | 'admin' | 'moderator';
  
  subscription: {
    plan: SubscriptionPlan['name'];
    status: 'active' | 'cancelled' | 'expired';
    price: number;
  };
  
  stats?: {
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

// Интерфейс канала
export interface Channel {
  // Идентификация
  id: string;
  name: string;
  username?: string;
  type?: ChannelType;
  
  // Статус и метаданные
  status: ChannelStatus;
  created_at: string;
  updated_at?: string;
  
  // Статистические показатели
  accuracy?: number;
  signals_count?: number;
  subscribers_count?: number;
  
  // Финансовые метрики
  avg_profit?: number;
  avg_roi?: number;
  
  // Дополнительные метаданные
  description?: string;
  url?: string;
  category?: string;
}

// Интерфейс сигнала
export interface Signal {
  id: string;
  channel_id: string;
  pair: string;
  asset: string; // Добавляем asset для отображения
  entry_price: number;
  target_price?: number;
  stop_loss?: number;
  
  status: SignalStatus;
  direction: SignalDirection;
  
  created_at: string;
  closed_at?: string;
  
  pnl?: number;
  roi?: number;
  confidence?: number; // Уверенность в сигнале (0-1)
  description?: string; // Описание сигнала
  
  // Связанный канал (опционально)
  channel?: {
    id: string;
    name: string;
  };
}

// Интерфейс подписки
export interface SubscriptionPlan {
  id: string;
  name: 'Free' | 'Premium' | 'Pro';
  price: number;
  features: string[];
}

// Существующий тип User - ИСПРАВЛЯЕМ ТОЛЬКО ЭТО
export interface User {
  id: string;
  name: string;
  username: string;
  email: string;
  avatar?: string;
  joinDate: string;
  
  // ДОБАВЛЯЕМ РОЛЬ - это единственное изменение
  role: 'user' | 'admin' | 'moderator';
  
  subscription: {
    plan: SubscriptionPlan['name'];
    status: 'active' | 'cancelled' | 'expired';
    price: number;
  };
  
  stats?: {
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

// Интерфейс уведомления
export interface Notification {
  id: string;
  type: 'signal' | 'target_reached' | 'stop_loss' | 'info' | 'success' | 'warning';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  urgent?: boolean;
  channel?: string;
  pair?: string;
  price?: number;
}

// Утилитарные типы
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;

// Реэкспорт типов таблицы
export * from './table';

// Типы для фильтрации и сортировки
export interface ChannelFilters {
  type?: ChannelType;
  status?: ChannelStatus;
  search?: string;
  accuracy_range?: string | [number, number];
  signals_range?: string;
  created_from?: string;
  created_to?: string;
}

// Дублированные типы удалены - используются определения выше

// Утилитарные функции типизации
export function isValidChannel(channel: Partial<Channel>): channel is Channel {
  return !!channel.id && !!channel.name;
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

// Signal Types (дублированные удалены - используются определения выше)
export type SignalType = 'LONG' | 'SHORT';

// Удален дублирующий интерфейс Signal

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

// Дублированный интерфейс SubscriptionPlan удален - используется определение выше

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
export interface SignalFilters {
  channelId?: string;
  channel_id?: string; // Дублируем для совместимости
  type?: SignalDirection;
  direction?: SignalDirection; // Дублируем для совместимости
  status?: SignalStatus;
  dateFrom?: string;
  dateTo?: string;
  date_from?: string; // Дублируем для совместимости
  date_to?: string; // Дублируем для совместимости
  search?: string; // Поиск по тексту
  pnl_range?: string; // Диапазон прибыли/убытка
  time_range?: string; // Временной диапазон
  price_from?: string; // Цена от
  price_to?: string; // Цена до
  pair?: string; // Торговая пара
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

// Типы для аутентификации
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username?: string;
  password: string;
  confirm_password?: string;
  first_name?: string;
  last_name?: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirmRequest {
  token: string;
  new_password: string;
  confirm_password: string;
}

// Типы для WebSocket событий
export interface BaseEvent {
  type: string;
  timestamp: string;
}

export interface SignalEvent extends BaseEvent {
  type: 'signal';
  signal_id: string;
  pair: string;
  direction: 'long' | 'short';
  entry_price: number;
  target_price?: number;
  stop_loss?: number;
}

export interface PriceEvent extends BaseEvent {
  type: 'price';
  pair: string;
  current_price: number;
  change_percent: number;
  change_24h: number;
}

export interface ChannelEvent extends BaseEvent {
  type: 'channel';
  channel_id: string;
  name: string;
  status: 'active' | 'inactive';
  accuracy_change: number;
}

export type NotificationEvent = SignalEvent | PriceEvent | ChannelEvent;
