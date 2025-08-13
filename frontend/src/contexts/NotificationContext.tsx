import React, {
  createContext,
  useContext,
  useReducer,
  useEffect,
  ReactNode,
} from 'react';

export interface Notification {
  id: string;
  type:
    | 'signal'
    | 'alert'
    | 'info'
    | 'success'
    | 'warning'
    | 'error'
    | 'price_alert'
    | 'target_reached'
    | 'stop_loss';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  channel?: string;
  pair?: string;
  action?: 'buy' | 'sell';
  price?: number;
  change?: number;
  urgent?: boolean;
  autoHide?: boolean;
  duration?: number;
}

interface NotificationState {
  notifications: Notification[];
  isWebSocketConnected: boolean;
  unreadCount: number;
  settings: {
    enabled: boolean;
    browserNotifications: boolean;
    soundEnabled: boolean;
    onlyImportant: boolean;
    autoMarkAsRead: boolean;
  };
}

type NotificationAction =
  | { type: 'ADD_NOTIFICATION'; payload: Notification }
  | { type: 'MARK_AS_READ'; payload: string }
  | { type: 'MARK_ALL_AS_READ' }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'CLEAR_ALL_NOTIFICATIONS' }
  | { type: 'SET_WEBSOCKET_STATUS'; payload: boolean }
  | {
      type: 'UPDATE_SETTINGS';
      payload: Partial<NotificationState['settings']>;
    };

const initialState: NotificationState = {
  notifications: [],
  isWebSocketConnected: false,
  unreadCount: 0,
  settings: {
    enabled: true,
    browserNotifications: true,
    soundEnabled: true,
    onlyImportant: false,
    autoMarkAsRead: false,
  },
};

function notificationReducer(
  state: NotificationState,
  action: NotificationAction
): NotificationState {
  switch (action.type) {
    case 'ADD_NOTIFICATION':
      const newNotifications = [action.payload, ...state.notifications];
      return {
        ...state,
        notifications: newNotifications,
        unreadCount: newNotifications.filter(n => !n.read).length,
      };

    case 'MARK_AS_READ':
      const updatedNotifications = state.notifications.map(notif =>
        notif.id === action.payload ? { ...notif, read: true } : notif
      );
      return {
        ...state,
        notifications: updatedNotifications,
        unreadCount: updatedNotifications.filter(n => !n.read).length,
      };

    case 'MARK_ALL_AS_READ':
      const allReadNotifications = state.notifications.map(notif => ({
        ...notif,
        read: true,
      }));
      return {
        ...state,
        notifications: allReadNotifications,
        unreadCount: 0,
      };

    case 'REMOVE_NOTIFICATION':
      const filteredNotifications = state.notifications.filter(
        notif => notif.id !== action.payload
      );
      return {
        ...state,
        notifications: filteredNotifications,
        unreadCount: filteredNotifications.filter(n => !n.read).length,
      };

    case 'CLEAR_ALL_NOTIFICATIONS':
      return {
        ...state,
        notifications: [],
        unreadCount: 0,
      };

    case 'SET_WEBSOCKET_STATUS':
      return {
        ...state,
        isWebSocketConnected: action.payload,
      };

    case 'UPDATE_SETTINGS':
      return {
        ...state,
        settings: { ...state.settings, ...action.payload },
      };

    default:
      return state;
  }
}

interface NotificationContextType {
  state: NotificationState;
  addNotification: (
    notification: Omit<Notification, 'id' | 'timestamp'>
  ) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;
  updateSettings: (settings: Partial<NotificationState['settings']>) => void;
  showBrowserNotification: (
    title: string,
    message: string,
    icon?: string
  ) => Promise<boolean>;
  requestNotificationPermission: () => Promise<boolean>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(
  undefined
);

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error(
      'useNotifications must be used within a NotificationProvider'
    );
  }
  return context;
}

interface NotificationProviderProps {
  children: ReactNode;
}

export function NotificationProvider({ children }: NotificationProviderProps) {
  const [state, dispatch] = useReducer(notificationReducer, initialState);

  // WebSocket connection for real-time notifications
  useEffect(() => {
    if (!state.settings.enabled) return;

    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;

    const connectWebSocket = () => {
      try {
        // Подключение к WebSocket серверу для real-time уведомлений
        const wsUrl =
          process.env.NEXT_PUBLIC_WS_URL ||
          'ws://localhost:8000/ws/notifications';
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log('📡 WebSocket connected for notifications');
          dispatch({ type: 'SET_WEBSOCKET_STATUS', payload: true });
        };

        ws.onmessage = event => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === 'notification') {
              const notification: Notification = {
                id: Date.now().toString() + Math.random(),
                timestamp: new Date(),
                read: false,
                ...data.notification,
              };

              addNotification(notification);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onclose = () => {
          console.log('📡 WebSocket disconnected');
          dispatch({ type: 'SET_WEBSOCKET_STATUS', payload: false });

          // Автопереподключение через 5 секунд
          reconnectTimeout = setTimeout(connectWebSocket, 5000);
        };

        ws.onerror = error => {
          console.error('WebSocket error:', error);
          dispatch({ type: 'SET_WEBSOCKET_STATUS', payload: false });
        };
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        // Retry after 10 seconds
        reconnectTimeout = setTimeout(connectWebSocket, 10000);
      }
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, [state.settings.enabled]);

  // Запрос разрешения на browser notifications при первом запуске
  useEffect(() => {
    if (state.settings.browserNotifications && 'Notification' in window) {
      requestNotificationPermission();
    }
  }, [state.settings.browserNotifications]);

  const addNotification = (
    notification: Omit<Notification, 'id' | 'timestamp'>
  ) => {
    const fullNotification: Notification = {
      ...notification,
      id: Date.now().toString() + Math.random(),
      timestamp: new Date(),
      read: notification.read ?? false,
    };

    // Фильтрация по настройкам
    if (state.settings.onlyImportant && !notification.urgent) {
      return;
    }

    dispatch({ type: 'ADD_NOTIFICATION', payload: fullNotification });

    // Browser notification
    if (state.settings.browserNotifications && !notification.read) {
      showBrowserNotification(
        fullNotification.title,
        fullNotification.message,
        '/favicon.ico'
      );
    }

    // Sound notification
    if (state.settings.soundEnabled) {
      playNotificationSound(fullNotification.type);
    }

    // Auto-hide for non-urgent notifications
    if (fullNotification.autoHide !== false && !fullNotification.urgent) {
      setTimeout(() => {
        if (state.settings.autoMarkAsRead) {
          markAsRead(fullNotification.id);
        }
      }, fullNotification.duration || 5000);
    }
  };

  const markAsRead = (id: string) => {
    dispatch({ type: 'MARK_AS_READ', payload: id });
  };

  const markAllAsRead = () => {
    dispatch({ type: 'MARK_ALL_AS_READ' });
  };

  const removeNotification = (id: string) => {
    dispatch({ type: 'REMOVE_NOTIFICATION', payload: id });
  };

  const clearAllNotifications = () => {
    dispatch({ type: 'CLEAR_ALL_NOTIFICATIONS' });
  };

  const updateSettings = (settings: Partial<NotificationState['settings']>) => {
    dispatch({ type: 'UPDATE_SETTINGS', payload: settings });
  };

  const requestNotificationPermission = async (): Promise<boolean> => {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return false;
    }

    if (Notification.permission === 'granted') {
      return true;
    }

    if (Notification.permission === 'denied') {
      return false;
    }

    const permission = await Notification.requestPermission();
    return permission === 'granted';
  };

  const showBrowserNotification = async (
    title: string,
    message: string,
    icon?: string
  ): Promise<boolean> => {
    if (!state.settings.browserNotifications) return false;

    const hasPermission = await requestNotificationPermission();
    if (!hasPermission) return false;

    try {
      const notification = new Notification(title, {
        body: message,
        icon: icon || '/favicon.ico',
        badge: '/favicon.ico',
        // vibrate удален - не поддерживается в браузере
        requireInteraction: false,
        silent: !state.settings.soundEnabled,
      });

      // Автозакрытие через 5 секунд
      setTimeout(() => notification.close(), 5000);

      // Click handler
      notification.onclick = () => {
        window.focus();
        notification.close();
      };

      return true;
    } catch (error) {
      console.error('Failed to show browser notification:', error);
      return false;
    }
  };

  const playNotificationSound = (type: Notification['type']) => {
    if (!state.settings.soundEnabled) return;

    try {
      const audio = new Audio();

      // Разные звуки для разных типов уведомлений
      switch (type) {
        case 'signal':
          audio.src = '/sounds/signal.mp3';
          break;
        case 'alert':
        case 'warning':
          audio.src = '/sounds/alert.mp3';
          break;
        case 'success':
        case 'target_reached':
          audio.src = '/sounds/success.mp3';
          break;
        case 'error':
        case 'stop_loss':
          audio.src = '/sounds/error.mp3';
          break;
        default:
          audio.src = '/sounds/default.mp3';
      }

      audio.volume = 0.3;
      audio.play().catch(error => {
        // Игнорируем ошибки воспроизведения (возможно нет файлов звуков)
        console.debug('Sound play failed:', error);
      });
    } catch (error) {
      console.debug('Sound notification failed:', error);
    }
  };

  const contextValue: NotificationContextType = {
    state,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAllNotifications,
    updateSettings,
    showBrowserNotification,
    requestNotificationPermission,
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
    </NotificationContext.Provider>
  );
}

export default NotificationProvider;
