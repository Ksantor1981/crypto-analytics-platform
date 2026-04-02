import axios from 'axios';

import { env } from '@/config/env';

/** Axios шлёт пути вида /api/v1/... — база должна быть origin без /api/v1. */
function apiOriginFromEnv(): string {
  const base = env.NEXT_PUBLIC_API_URL.replace(/\/$/, '');
  return base.replace(/\/api\/v1\/?$/, '') || 'http://localhost:8000';
}

const api = axios.create({
  baseURL: apiOriginFromEnv(),
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(config => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export const apiClient = {
  isAuthenticated(): boolean {
    if (typeof window === 'undefined') return false;
    return !!localStorage.getItem('access_token');
  },

  async login(email: string, password: string) {
    const { data } = await api.post('/api/v1/users/login', {
      email,
      password,
    });
    localStorage.setItem('access_token', data.access_token);
    return data;
  },

  async register(userData: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }) {
    const { data } = await api.post('/api/v1/users/register', {
      email: userData.email,
      password: userData.password,
      confirm_password: userData.password,
      full_name: `${userData.first_name} ${userData.last_name}`.trim(),
    });
    return data;
  },

  logout() {
    localStorage.removeItem('access_token');
  },

  async getCurrentUser() {
    const { data } = await api.get('/api/v1/users/me');
    return data;
  },

  async getLimits() {
    const { data } = await api.get('/api/v1/users/me/limits');
    return data;
  },

  async healthCheck() {
    const { data } = await api.get('/health');
    return data;
  },

  async getChannels(params?: Record<string, string | number | boolean>) {
    const { data } = await api.get('/api/v1/channels/', { params });
    return data;
  },

  async getChannel(id: string) {
    const { data } = await api.get(`/api/v1/channels/${id}`);
    return data;
  },

  async createChannel(channelData: Record<string, unknown>) {
    const { data } = await api.post('/api/v1/channels/', channelData);
    return data;
  },

  async updateChannel(id: string, channelData: Record<string, unknown>) {
    const { data } = await api.put(`/api/v1/channels/${id}`, channelData);
    return data;
  },

  async deleteChannel(id: string) {
    const { data } = await api.delete(`/api/v1/channels/${id}`);
    return data;
  },

  async getSignals(channelId?: string, page?: number, limit?: number) {
    const params: Record<string, string> = {};
    if (channelId) params.channel_id = channelId;
    if (limit) params.limit = String(limit);
    if (page != null && limit != null) params.skip = String((page - 1) * limit);
    const { data } = await api.get('/api/v1/signals/', { params });
    return data;
  },

  async getSignalsWithTotal(channelId?: string, limit = 1000) {
    const params: Record<string, string> = { limit: String(limit) };
    if (channelId) params.channel_id = channelId;
    const { data } = await api.get('/api/v1/signals/', { params });
    return { signals: data?.signals ?? [], total: data?.total ?? 0 };
  },

  async getSubscriptionPlans() {
    const { data } = await api.get('/api/v1/subscriptions/plans');
    return Array.isArray(data) ? data : [];
  },

  async getSignal(id: string) {
    const { data } = await api.get(`/api/v1/signals/${id}`);
    return data;
  },

  async getSubscriptions() {
    const { data } = await api.get('/api/v1/subscriptions');
    return data;
  },

  async updateSubscription(planType: 'free' | 'pro' | 'enterprise') {
    const { data } = await api.post('/api/v1/subscriptions', {
      plan_type: planType,
    });
    return data;
  },

  /**
   * Premium/Pro: экспорт своих данных (фильтры по подписке на бэкенде).
   */
  async downloadPremiumExport(
    kind: 'signals' | 'channels' | 'analytics',
    format: 'csv' | 'excel' | 'json' = 'csv'
  ): Promise<void> {
    const response = await api.get(`/api/v1/export/${kind}`, {
      params: { format },
      responseType: 'blob',
      validateStatus: () => true,
    });

    if (response.status >= 400) {
      const text = await (response.data as Blob).text();
      let msg = text;
      try {
        const j = JSON.parse(text) as { detail?: string | unknown };
        if (typeof j.detail === 'string') msg = j.detail;
        else if (j.detail != null) msg = JSON.stringify(j.detail);
      } catch {
        /* оставляем text */
      }
      throw new Error(msg || `Ошибка экспорта (${response.status})`);
    }

    const blob = response.data as Blob;
    const disposition = response.headers['content-disposition'] as
      | string
      | undefined;
    let filename = `${kind}.${format === 'excel' ? 'xlsx' : format}`;
    if (disposition) {
      const utf8Match = /filename\*=UTF-8''([^;\s]+)/i.exec(disposition);
      if (utf8Match) {
        filename = decodeURIComponent(utf8Match[1]);
      } else {
        const m = /filename="([^"]+)"/i.exec(disposition);
        if (m?.[1]) filename = m[1].trim();
      }
    }

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  /**
   * Снимок сигналов CSV (до 1000 строк) — для любого авторизованного пользователя.
   */
  /** Текущая цена символа (нужен JWT). symbol: BTC или ETH */
  async getAnalyticsCurrentPrice(symbol: string) {
    const sym = symbol.split('/')[0]?.trim() || symbol;
    const { data } = await api.get(
      `/api/v1/analytics/analytics/price/${encodeURIComponent(sym)}`
    );
    return data as {
      success?: boolean;
      data?: { current_price?: number | null };
    };
  },

  async downloadSignalsCsvSnapshot(): Promise<void> {
    const response = await api.get('/api/v1/export/signals.csv', {
      responseType: 'blob',
      validateStatus: () => true,
    });
    if (response.status >= 400) {
      const text = await (response.data as Blob).text();
      throw new Error(text || `Ошибка загрузки CSV (${response.status})`);
    }
    const blob = response.data as Blob;
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'signals_export.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },
};

export default apiClient;
