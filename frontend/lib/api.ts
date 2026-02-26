import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
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

  async register(userData: { email: string; password: string; first_name: string; last_name: string }) {
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

  async healthCheck() {
    const { data } = await api.get('/health');
    return data;
  },

  async getChannels() {
    const { data } = await api.get('/api/v1/channels/');
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
    if (page) params.page = String(page);
    if (limit) params.limit = String(limit);
    const { data } = await api.get('/api/v1/signals/', { params });
    return data;
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
    const { data } = await api.post('/api/v1/subscriptions', { plan_type: planType });
    return data;
  },
};

export default apiClient;
