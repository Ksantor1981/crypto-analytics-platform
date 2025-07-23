import { useState, useEffect } from 'react';
import {
  Bell,
  X,
  Check,
  AlertTriangle,
  Info,
  TrendingUp,
  TrendingDown,
  Settings,
  Filter,
  RefreshCw,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useNotifications } from '@/contexts/NotificationContext';
import NotificationSettings from './NotificationSettings';
import useRealTimeNotifications from '@/hooks/useRealTimeNotifications';

interface NotificationCenterProps {
  isOpen: boolean;
  onClose: () => void;
}

export function NotificationCenter({
  isOpen,
  onClose,
}: NotificationCenterProps) {
  const { state, markAsRead, markAllAsRead, removeNotification } =
    useNotifications();
  const { checkForNotifications, isConnected } = useRealTimeNotifications();
  const [filter, setFilter] = useState<'all' | 'unread' | 'signals' | 'alerts'>(
    'all'
  );
  const [showSettings, setShowSettings] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'signal':
        return <TrendingUp className="h-5 w-5 text-blue-600" />;
      case 'success':
      case 'target_reached':
        return <Check className="h-5 w-5 text-green-600" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'error':
      case 'stop_loss':
        return <X className="h-5 w-5 text-red-600" />;
      case 'alert':
      case 'price_alert':
        return <AlertTriangle className="h-5 w-5 text-orange-600" />;
      default:
        return <Info className="h-5 w-5 text-gray-600" />;
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await checkForNotifications();
    } finally {
      setIsRefreshing(false);
    }
  };

  const filteredNotifications = state.notifications.filter(notif => {
    switch (filter) {
      case 'unread':
        return !notif.read;
      case 'signals':
        return (
          notif.type === 'signal' ||
          notif.type === 'target_reached' ||
          notif.type === 'stop_loss'
        );
      case 'alerts':
        return (
          notif.type === 'alert' ||
          notif.type === 'price_alert' ||
          notif.type === 'warning'
        );
      default:
        return true;
    }
  });

  const formatTimestamp = (timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'только что';
    if (minutes < 60) return `${minutes} мин назад`;
    if (hours < 24) return `${hours} ч назад`;
    return `${days} дн назад`;
  };

  if (!isOpen) return null;

  if (showSettings) {
    return (
      <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold">Настройки уведомлений</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSettings(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <NotificationSettings onClose={() => setShowSettings(false)} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-start justify-end pt-16 pr-4">
      <Card className="w-96 max-h-[80vh] overflow-hidden">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Bell className="h-5 w-5" />
              <CardTitle className="text-lg">Уведомления</CardTitle>
              {state.unreadCount > 0 && (
                <span className="bg-red-500 text-white text-xs rounded-full px-2 py-1">
                  {state.unreadCount}
                </span>
              )}
              <div
                className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}
                title={isConnected ? 'Подключено' : 'Отключено'}
              />
            </div>

            <div className="flex items-center space-x-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                disabled={isRefreshing}
                title="Обновить"
              >
                <RefreshCw
                  className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`}
                />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSettings(true)}
                title="Настройки"
              >
                <Settings className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Filters */}
          <div className="flex space-x-2 mt-3">
            {[
              { key: 'all', label: 'Все', count: state.notifications.length },
              {
                key: 'unread',
                label: 'Непрочитанные',
                count: state.unreadCount,
              },
              {
                key: 'signals',
                label: 'Сигналы',
                count: state.notifications.filter(n =>
                  ['signal', 'target_reached', 'stop_loss'].includes(n.type)
                ).length,
              },
              {
                key: 'alerts',
                label: 'Алерты',
                count: state.notifications.filter(n =>
                  ['alert', 'price_alert', 'warning'].includes(n.type)
                ).length,
              },
            ].map(filterOption => (
              <button
                key={filterOption.key}
                onClick={() => setFilter(filterOption.key as any)}
                className={`px-3 py-1 text-xs rounded-full transition-colors flex items-center space-x-1 ${
                  filter === filterOption.key
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <span>{filterOption.label}</span>
                {filterOption.count > 0 && (
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded-full ${
                      filter === filterOption.key
                        ? 'bg-blue-700'
                        : 'bg-gray-300'
                    }`}
                  >
                    {filterOption.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {state.unreadCount > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={markAllAsRead}
              className="mt-2 w-full"
            >
              Отметить все как прочитанные
            </Button>
          )}
        </CardHeader>

        <CardContent className="p-0">
          <div className="max-h-96 overflow-y-auto">
            {filteredNotifications.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                <Bell className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <p>
                  {filter === 'all'
                    ? 'Нет уведомлений'
                    : filter === 'unread'
                      ? 'Нет непрочитанных уведомлений'
                      : filter === 'signals'
                        ? 'Нет сигналов'
                        : 'Нет алертов'}
                </p>
              </div>
            ) : (
              filteredNotifications.map(notification => (
                <div
                  key={notification.id}
                  className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors ${
                    !notification.read
                      ? 'bg-blue-50 border-l-4 border-l-blue-500'
                      : ''
                  } ${notification.urgent ? 'border-l-red-500 bg-red-50' : ''}`}
                  onClick={() => markAsRead(notification.id)}
                >
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {getNotificationIcon(notification.type)}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p
                          className={`text-sm font-medium ${!notification.read ? 'text-gray-900' : 'text-gray-600'}`}
                        >
                          {notification.title}
                          {notification.urgent && (
                            <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                              URGENT
                            </span>
                          )}
                        </p>
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            removeNotification(notification.id);
                          }}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>

                      <p
                        className={`text-sm mt-1 ${!notification.read ? 'text-gray-700' : 'text-gray-500'}`}
                      >
                        {notification.message}
                      </p>

                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-gray-400">
                          {formatTimestamp(notification.timestamp)}
                        </span>

                        {notification.channel && (
                          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                            {notification.channel}
                          </span>
                        )}
                      </div>

                      {(notification.pair || notification.price) && (
                        <div className="flex items-center mt-2 space-x-2">
                          {notification.pair && (
                            <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
                              {notification.pair}
                            </span>
                          )}
                          {notification.action && (
                            <span
                              className={`text-xs px-2 py-1 rounded ${
                                notification.action === 'buy'
                                  ? 'bg-green-100 text-green-600'
                                  : 'bg-red-100 text-red-600'
                              }`}
                            >
                              {notification.action === 'buy' ? 'LONG' : 'SHORT'}
                            </span>
                          )}
                          {notification.price && (
                            <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded">
                              ${notification.price.toLocaleString()}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default NotificationCenter;


