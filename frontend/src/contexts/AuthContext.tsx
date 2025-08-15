'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { User, APIUser } from '@/types';

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  register: (userData: { email: string; password: string; first_name: string; last_name: string }) => Promise<boolean>;
  logout: () => Promise<void>;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

// Функция для маппинга APIUser в User
const mapAPIUserToUser = (apiUser: APIUser): User => {
  return {
    id: apiUser.id.toString(),
    name: apiUser.name || apiUser.email,
    username: apiUser.email,
    email: apiUser.email,
    avatar: undefined,
    joinDate: new Date().toISOString(),
    role: 'user',
    subscription: {
      plan: apiUser.subscription_type === 'pro' ? 'Pro' : 
            apiUser.subscription_type === 'enterprise' ? 'Pro' : 'Free',
      status: 'active',
      price: 0
    },
    stats: {
      channelsFollowed: 0,
      successRate: 0,
      profit: 0,
      totalProfit: 0,
      totalSignals: 0,
      winRate: 0,
      totalReturn: 0,
      daysActive: 0
    },
    settings: {
      emailNotifications: true,
      pushNotifications: true,
      telegramAlerts: false,
      weeklyReports: false,
      darkMode: false,
      language: 'ru',
      timezone: 'Europe/Moscow'
    }
  };
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Проверяем авторизацию при загрузке
    checkAuth();
  }, []);

  const checkAuth = async () => {
    if (apiClient.isAuthenticated()) {
      try {
        const apiUser = await apiClient.getCurrentUser();
        const userData = mapAPIUserToUser(apiUser);
        setUser(userData);
      } catch (error) {
        console.error('Auth check failed:', error);
        apiClient.logout();
      }
    }
    setIsLoading(false);
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      await apiClient.login(email, password);
      
      // Получаем данные пользователя после успешного логина
      const apiUser = await apiClient.getCurrentUser();
      const userData = mapAPIUserToUser(apiUser);
      setUser(userData);
      setIsLoading(false);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
      setIsLoading(false);
      return false;
    }
  };

  const register = async (userData: { email: string; password: string; first_name: string; last_name: string }): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      await apiClient.register(userData);
      
      // Автоматически входим после регистрации
      await apiClient.login(userData.email, userData.password);
      const apiUser = await apiClient.getCurrentUser();
      const userDataUI = mapAPIUserToUser(apiUser);
      setUser(userDataUI);
      setIsLoading(false);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
      setIsLoading(false);
      return false;
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      apiClient.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setError(null);
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      login,
      register,
      logout,
      isLoading,
      isAuthenticated: !!user,
      error
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};