import { useEffect, useRef } from 'react';
import { useNotifications } from '@/contexts/NotificationContext';

interface SignalEvent {
  type: 'new_signal' | 'signal_update' | 'target_reached' | 'stop_loss_hit';
  signal_id: string;
  symbol: string;
  signal_type: 'long' | 'short';
  entry_price?: number;
  current_price?: number;
  target_price?: number;
  stop_loss?: number;
  confidence?: number;
  channel?: string;
  change_percent?: number;
}

interface PriceEvent {
  type: 'price_update';
  symbol: string;
  price: number;
  change_24h: number;
  volume_24h: number;
}

interface ChannelEvent {
  type: 'channel_update';
  channel_id: string;
  channel_name: string;
  new_accuracy?: number;
  new_signals_count?: number;
}

type NotificationEvent = SignalEvent | PriceEvent | ChannelEvent;

export function useRealTimeNotifications() {
  const { addNotification, state } = useNotifications();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connectWebSocket = () => {
    if (!state.settings.enabled) return;

    try {
      const wsUrl =
        process.env.NEXT_PUBLIC_WS_URL ||
        'ws://localhost:8000/ws/notifications';
      const token = localStorage.getItem('auth_token'); // JWT token for authentication

      wsRef.current = new WebSocket(`${wsUrl}?token=${token}`);

      wsRef.current.onopen = () => {
        console.log('🔔 Real-time notifications connected');
        reconnectAttempts.current = 0;

        // Подписываемся на нужные типы событий
        wsRef.current?.send(
          JSON.stringify({
            type: 'subscribe',
            events: ['signals', 'prices', 'channels', 'alerts'],
          })
        );
      };

      wsRef.current.onmessage = event => {
        try {
          const data: NotificationEvent = JSON.parse(event.data);
          handleNotificationEvent(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onclose = event => {
        console.log('🔔 WebSocket disconnected:', event.code);

        // Попытка переподключения
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.pow(2, reconnectAttempts.current) * 1000; // Exponential backoff
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connectWebSocket();
          }, delay);
        }
      };

      wsRef.current.onerror = error => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  };

  const handleNotificationEvent = (event: NotificationEvent) => {
    switch (event.type) {
      case 'new_signal':
        addNotification({
          type: 'signal',
          title: `Новый сигнал: ${event.symbol}`,
          message: `${event.signal_type.toUpperCase()} сигнал от ${event.channel || 'канала'}`,
          urgent: (event.confidence || 0) > 0.85,
          channel: event.channel,
          pair: event.symbol,
          action: event.signal_type === 'long' ? 'buy' : 'sell',
          price: event.entry_price,
        });
        break;

      case 'target_reached':
        addNotification({
          type: 'target_reached',
          title: `🎯 Цель достигнута!`,
          message: `${event.symbol} достиг TP ${event.change_percent ? `(+${event.change_percent.toFixed(2)}%)` : ''}`,
          urgent: false,
          pair: event.symbol,
          price: event.current_price,
        });
        break;

      case 'stop_loss_hit':
        addNotification({
          type: 'stop_loss',
          title: `⚠️ Стоп-лосс сработал`,
          message: `${event.symbol} достиг SL ${event.change_percent ? `(${event.change_percent.toFixed(2)}%)` : ''}`,
          urgent: true,
          pair: event.symbol,
          price: event.current_price,
        });
        break;

      case 'signal_update':
        if (event.change_percent && Math.abs(event.change_percent) > 5) {
          addNotification({
            type: event.change_percent > 0 ? 'success' : 'warning',
            title: `Изменение позиции`,
            message: `${event.symbol}: ${event.change_percent > 0 ? '+' : ''}${event.change_percent.toFixed(2)}%`,
            urgent: Math.abs(event.change_percent) > 10,
            pair: event.symbol,
            price: event.current_price,
            autoHide: true,
          });
        }
        break;

      case 'price_update':
        // Уведомления только для значительных изменений цены
        if (Math.abs(event.change_24h) > 10) {
          addNotification({
            type: event.change_24h > 0 ? 'success' : 'warning',
            title: `Большое движение цены`,
            message: `${event.symbol}: ${event.change_24h > 0 ? '+' : ''}${event.change_24h.toFixed(2)}% за 24ч`,
            urgent: Math.abs(event.change_24h) > 20,
            pair: event.symbol,
            price: event.price,
            autoHide: true,
            duration: 3000,
          });
        }
        break;

      case 'channel_update':
        if (event.new_accuracy !== undefined) {
          addNotification({
            type: 'info',
            title: `Обновление канала`,
            message: `${event.channel_name}: точность ${event.new_accuracy.toFixed(1)}%`,
            channel: event.channel_name,
            autoHide: true,
            duration: 4000,
          });
        }
        break;

      default:
        console.log('Unknown notification event:', event);
    }
  };

  // Polling fallback для случаев, когда WebSocket недоступен
  useEffect(() => {
    if (!state.settings.enabled) return;

    const pollNotifications = async () => {
      try {
        const response = await fetch('/api/notifications/poll', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
          },
        });

        if (response.ok) {
          const notifications = await response.json();
          notifications.forEach((notif: any) => {
            addNotification({
              type: notif.type,
              title: notif.title,
              message: notif.message,
              urgent: notif.urgent,
              channel: notif.channel,
              pair: notif.pair,
              autoHide: true,
            });
          });
        }
      } catch (error) {
        console.debug('Polling notifications failed:', error);
      }
    };

    // Polling каждые 30 секунд как fallback
    const pollInterval = setInterval(pollNotifications, 30000);

    return () => clearInterval(pollInterval);
  }, [state.settings.enabled, addNotification]);

  // Основное подключение WebSocket
  useEffect(() => {
    if (state.settings.enabled) {
      connectWebSocket();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [state.settings.enabled]);

  // API для ручной проверки уведомлений
  const checkForNotifications = async () => {
    try {
      const response = await fetch('/api/notifications/check', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();

        if (data.notifications?.length > 0) {
          data.notifications.forEach((notif: any) => {
            addNotification(notif);
          });
        }

        return data;
      }
    } catch (error) {
      console.error('Failed to check notifications:', error);
      return null;
    }
  };

  // API для отправки тестового уведомления
  const sendTestNotification = () => {
    addNotification({
      type: 'info',
      title: 'Тестовое уведомление',
      message: 'Система уведомлений работает корректно',
      autoHide: true,
      duration: 3000,
    });
  };

  return {
    checkForNotifications,
    sendTestNotification,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  };
}

export default useRealTimeNotifications;
