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

  /** Admin: очередь Review Console (raw_events без меток и др.). */
  async getReviewQueue(params?: {
    limit?: number;
    offset?: number;
    unlabeled_only?: boolean;
    edited_only?: boolean;
    channel_id?: number;
  }) {
    const { data } = await api.get('/api/v1/admin/review-labels/queue', {
      params,
    });
    return data as {
      items: Array<{
        raw_event_id: number;
        source_type: string;
        channel_id: number | null;
        channel_username: string | null;
        platform_message_id: string | null;
        raw_text_preview: string | null;
        first_seen_at: string | null;
        version_count: number;
        labels_count: number;
      }>;
      total: number;
      limit: number;
      offset: number;
    };
  },

  async getRawEventDetail(rawEventId: number) {
    const { data } = await api.get(
      `/api/v1/admin/review-labels/raw-events/${rawEventId}`
    );
    return data as {
      raw_event: Record<string, unknown>;
      message_versions: Array<Record<string, unknown>>;
      review_labels: Array<Record<string, unknown>>;
      channel: { id: number; username: string | null; name: string } | null;
      extractions?: Array<Record<string, unknown>>;
      normalized_signals?: Array<Record<string, unknown>>;
      signal_relations?: Array<Record<string, unknown>>;
      signal_outcomes?: Array<Record<string, unknown>>;
    };
  },

  async postReviewLabel(body: {
    raw_event_id: number;
    label_type: string;
    notes?: string;
    linked_signal_id?: number;
    corrected_fields?: Record<string, unknown>;
  }) {
    const { data } = await api.post('/api/v1/admin/review-labels/', body);
    return data;
  },

  /** Admin: создать PENDING signal_outcomes для всех normalized этого raw_event. */
  async ensureSignalOutcomesForRawEvent(rawEventId: number) {
    const { data } = await api.post(
      `/api/v1/admin/signal-outcomes/ensure-for-raw-event/${rawEventId}`
    );
    return data as {
      raw_event_id: number;
      normalized_signal_count: number;
      created_total: number;
    };
  },

  /** Admin: заглушка пересчёта outcome (DATA_INCOMPLETE + error_detail). */
  async postSignalOutcomeStubRecalculate(signalOutcomeId: number) {
    const { data } = await api.post(
      `/api/v1/admin/signal-outcomes/${signalOutcomeId}/stub-recalculate`
    );
    return data as Record<string, unknown>;
  },

  /** Admin: пересчёт по свечам (нужен OUTCOME_RECALC_ENABLED на backend). */
  async postSignalOutcomeRecalculate(signalOutcomeId: number, force = false) {
    const { data } = await api.post(
      `/api/v1/admin/signal-outcomes/${signalOutcomeId}/recalculate`,
      null,
      { params: { force } }
    );
    return data as Record<string, unknown>;
  },

  /** Admin: пакетный пересчёт PENDING outcomes. */
  async postSignalOutcomesProcessPendingRecalc(limit = 50) {
    const { data } = await api.post(
      '/api/v1/admin/signal-outcomes/process-pending-recalc',
      null,
      { params: { limit } }
    );
    return data as { processed: number; ok: number; failed: number; errors: string[] };
  },

  /** Статус Telethon-сессии на backend (для MTProto collect). */
  async getTelethonCollectStatus() {
    const { data } = await api.get('/api/v1/collect/telethon-status');
    return data as { authenticated: boolean; how_to_auth?: string };
  },

  /**
   * Premium: Telethon collect по всем активным Telegram-каналам (shadow + legacy).
   * Нужна авторизация Telethon на сервере (`telethon_collector --auth`).
   */
  async telethonCollectAll(days = 7) {
    const { data } = await api.post(
      '/api/v1/collect/telethon-collect-all',
      null,
      { params: { days } }
    );
    return data as Record<string, unknown>;
  },
};

export default apiClient;
