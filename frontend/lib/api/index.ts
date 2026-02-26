const API_BASE =
  typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL
    : 'http://localhost:8000/api/v1';

const SERVER_BASE = API_BASE.replace(/\/api\/v1\/?$/, '') || 'http://localhost:8000';

const getToken = (): string | null =>
  typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

async function request<T>(
  url: string,
  options: RequestInit & { base?: string } = {}
): Promise<T> {
  const { base = API_BASE, ...init } = options;
  const fullUrl = url.startsWith('http') ? url : `${base}${url.startsWith('/') ? '' : '/'}${url}`;
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(fullUrl, { ...init, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(
      Array.isArray(err.detail) ? err.detail.map((d: { msg?: string }) => d.msg).join(', ') : err.detail || res.statusText
    );
  }
  return res.json();
}

export const apiClient = {
  isAuthenticated: () => !!getToken(),

  healthCheck: () =>
    request<{ status?: string }>(`${SERVER_BASE}/health`, { base: '' }),

  login: async (email: string, password: string) => {
    const res = await request<{ access_token: string; token_type?: string }>(
      '/users/login',
      {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }
    );
    if (res.access_token && typeof window !== 'undefined') {
      localStorage.setItem('access_token', res.access_token);
    }
  },

  register: async (data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }) => {
    await request('/users/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },

  getCurrentUser: () =>
    request<{
      id: number;
      email: string;
      subscription_type: string;
      is_active: boolean;
      name?: string;
    }>('/users/me'),

  getChannels: (params?: { skip?: number; limit?: number; sort?: string }) => {
    const q = new URLSearchParams();
    if (params?.skip != null) q.set('skip', String(params.skip));
    if (params?.limit != null) q.set('limit', String(params.limit));
    if (params?.sort) q.set('sort', params.sort);
    const query = q.toString();
    return request<any[]>(`/channels${query ? `?${query}` : ''}`);
  },

  getChannel: (id: string) => request<any>(`/channels/${id}`),

  createChannel: (data: Record<string, unknown>) =>
    request<any>('/channels/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateChannel: (id: string, data: Record<string, unknown>) =>
    request<any>(`/channels/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteChannel: (id: string) =>
    request(`/channels/${id}`, { method: 'DELETE' }),

  getSignals: (channelId?: string, page?: number, limit?: number) => {
    const q = new URLSearchParams();
    if (channelId) q.set('channel_id', channelId);
    if (page != null) q.set('skip', String((page - 1) * (limit ?? 20)));
    if (limit != null) q.set('limit', String(limit));
    const query = q.toString();
    const path = `/signals${query ? `?${query}` : ''}`;
    return request<{ signals?: any[]; items?: any[] }>(path).then(
      (r) => r.signals ?? r.items ?? []
    );
  },

  getSignal: (id: string) => request<any>(`/signals/${id}`),

  getSubscriptions: () => request<any>('/subscriptions/me'),

  updateSubscription: (planType: string) =>
    request('/subscriptions/me', {
      method: 'PUT',
      body: JSON.stringify({ plan_type: planType }),
    }),
};
