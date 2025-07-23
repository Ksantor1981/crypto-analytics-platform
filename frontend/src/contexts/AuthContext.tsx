import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User } from '@/types';
import axios from 'axios';

interface AuthContextType {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  login: (token: string, refreshToken: string, user: User) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<boolean>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Axios interceptor для автоматического обновления токенов
let isRefreshing = false;
let failedQueue: Array<{ resolve: Function; reject: Function }> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  
  failedQueue = [];
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshAccessToken = useCallback(async (): Promise<boolean> => {
    const currentRefreshToken = localStorage.getItem('refreshToken');
    
    if (!currentRefreshToken) {
      return false;
    }

    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/users/refresh-token`,
        { refresh_token: currentRefreshToken }
      );

      const { access_token, refresh_token: newRefreshToken, user: userData } = response.data;
      
      setToken(access_token);
      setRefreshToken(newRefreshToken);
      setUser(userData);
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('refreshToken', newRefreshToken);
      localStorage.setItem('user', JSON.stringify(userData));
      
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      await logout();
      return false;
    }
  }, []);

  useEffect(() => {
    // Проверяем наличие токенов при загрузке
    const initializeAuth = async () => {
      const savedToken = localStorage.getItem('token');
      const savedRefreshToken = localStorage.getItem('refreshToken');
      const savedUser = localStorage.getItem('user');

      if (savedToken && savedRefreshToken && savedUser) {
        setToken(savedToken);
        setRefreshToken(savedRefreshToken);
        setUser(JSON.parse(savedUser));
        
        // Проверяем валидность токена
        try {
          await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/users/me`, {
            headers: { Authorization: `Bearer ${savedToken}` }
          });
        } catch (error) {
          // Токен истек, пытаемся обновить
          const refreshed = await refreshAccessToken();
          if (!refreshed) {
            await logout();
          }
        }
      }
      
      setIsLoading(false);
    };

    initializeAuth();
  }, [refreshAccessToken]);

  // Настройка axios interceptors
  useEffect(() => {
    const requestInterceptor = axios.interceptors.request.use(
      (config) => {
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    const responseInterceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          if (isRefreshing) {
            return new Promise((resolve, reject) => {
              failedQueue.push({ resolve, reject });
            }).then(token => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return axios(originalRequest);
            }).catch(err => {
              return Promise.reject(err);
            });
          }

          originalRequest._retry = true;
          isRefreshing = true;

          try {
            const refreshed = await refreshAccessToken();
            if (refreshed) {
              processQueue(null, token);
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return axios(originalRequest);
            } else {
              processQueue(error, null);
              return Promise.reject(error);
            }
          } catch (refreshError) {
            processQueue(refreshError, null);
            return Promise.reject(refreshError);
          } finally {
            isRefreshing = false;
          }
        }

        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.request.eject(requestInterceptor);
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, [token, refreshAccessToken]);

  const login = async (newToken: string, newRefreshToken: string, newUser: User) => {
    setToken(newToken);
    setRefreshToken(newRefreshToken);
    setUser(newUser);
    localStorage.setItem('token', newToken);
    localStorage.setItem('refreshToken', newRefreshToken);
    localStorage.setItem('user', JSON.stringify(newUser));
  };

  const logout = async () => {
    try {
      // Уведомляем backend о выходе
      if (refreshToken) {
        await axios.post(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/users/logout`,
          { refresh_token: refreshToken }
        );
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setToken(null);
      setRefreshToken(null);
      setUser(null);
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        refreshToken,
        isLoading,
        login,
        logout,
        refreshAccessToken,
        isAuthenticated: !!token && !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
