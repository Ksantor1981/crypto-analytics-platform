import React, { useEffect, useState } from 'react';
import {
  X,
  CheckCircle,
  AlertTriangle,
  Info,
  TrendingUp,
  TrendingDown,
  DollarSign,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNotifications, Notification } from '@/contexts/NotificationContext';

interface ToastProps {
  notification: Notification;
  onClose: () => void;
}

export function NotificationToast({ notification, onClose }: ToastProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);

  useEffect(() => {
    // Анимация появления
    const timer = setTimeout(() => setIsVisible(true), 100);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    // Автозакрытие для неважных уведомлений
    if (notification.autoHide !== false && !notification.urgent) {
      const timer = setTimeout(() => {
        handleClose();
      }, notification.duration || 5000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  const handleClose = () => {
    setIsLeaving(true);
    setTimeout(onClose, 300); // Ждем завершения анимации
  };

  const getToastIcon = (type: Notification['type']) => {
    switch (type) {
      case 'success':
      case 'target_reached':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'error':
      case 'stop_loss':
        return <AlertTriangle className="h-5 w-5 text-red-600" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'signal':
        return <TrendingUp className="h-5 w-5 text-blue-600" />;
      case 'price_alert':
        return <DollarSign className="h-5 w-5 text-purple-600" />;
      default:
        return <Info className="h-5 w-5 text-gray-600" />;
    }
  };

  const getToastStyle = (type: Notification['type'], urgent?: boolean) => {
    const baseStyle = 'border-l-4 shadow-lg';
    const urgentStyle = urgent ? 'ring-2 ring-red-300 ring-opacity-50' : '';

    switch (type) {
      case 'success':
      case 'target_reached':
        return `${baseStyle} border-l-green-500 bg-green-50 ${urgentStyle}`;
      case 'error':
      case 'stop_loss':
        return `${baseStyle} border-l-red-500 bg-red-50 ${urgentStyle}`;
      case 'warning':
        return `${baseStyle} border-l-yellow-500 bg-yellow-50 ${urgentStyle}`;
      case 'signal':
        return `${baseStyle} border-l-blue-500 bg-blue-50 ${urgentStyle}`;
      case 'price_alert':
        return `${baseStyle} border-l-purple-500 bg-purple-50 ${urgentStyle}`;
      default:
        return `${baseStyle} border-l-gray-500 bg-gray-50 ${urgentStyle}`;
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div
      className={`
        fixed top-20 right-4 z-50 w-96 rounded-lg p-4 transition-all duration-300 ease-in-out
        ${getToastStyle(notification.type, notification.urgent)}
        ${
          isVisible && !isLeaving
            ? 'transform translate-x-0 opacity-100'
            : 'transform translate-x-full opacity-0'
        }
      `}
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">{getToastIcon(notification.type)}</div>

        <div className="ml-3 w-0 flex-1">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-900">
              {notification.title}
            </p>
            {notification.urgent && (
              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                URGENT
              </span>
            )}
          </div>

          <p className="mt-1 text-sm text-gray-700">{notification.message}</p>

          {/* Дополнительная информация для торговых сигналов */}
          {(notification.pair || notification.action || notification.price) && (
            <div className="mt-2 flex items-center space-x-3">
              {notification.pair && (
                <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                  {notification.pair}
                </span>
              )}
              {notification.action && (
                <span
                  className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                    notification.action === 'buy'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {notification.action === 'buy' ? 'LONG' : 'SHORT'}
                </span>
              )}
              {notification.price && (
                <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                  ${notification.price.toLocaleString()}
                </span>
              )}
            </div>
          )}

          <div className="mt-2 flex items-center justify-between">
            <span className="text-xs text-gray-500">
              {formatTimestamp(notification.timestamp)}
            </span>

            {notification.channel && (
              <span className="text-xs text-gray-500">
                {notification.channel}
              </span>
            )}
          </div>
        </div>

        <div className="ml-4 flex-shrink-0">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Progress bar для автозакрытия */}
      {notification.autoHide !== false && !notification.urgent && (
        <div className="mt-3 w-full bg-gray-200 rounded-full h-1">
          <div
            className="bg-blue-600 h-1 rounded-full transition-all duration-300 ease-linear"
            style={{
              animation: `shrink ${notification.duration || 5000}ms linear forwards`,
            }}
          />
        </div>
      )}

      <style jsx>{`
        @keyframes shrink {
          from {
            width: 100%;
          }
          to {
            width: 0%;
          }
        }
      `}</style>
    </div>
  );
}

// Container для всех toast уведомлений
export function ToastContainer() {
  const { state, removeNotification } = useNotifications();
  const [toasts, setToasts] = useState<Notification[]>([]);

  useEffect(() => {
    // Показываем только последние 3 уведомления в виде toast
    const recentNotifications = state.notifications
      .filter(n => !n.read)
      .slice(0, 3);

    setToasts(recentNotifications);
  }, [state.notifications]);

  return (
    <div className="fixed top-0 right-0 z-50 p-4 space-y-4">
      {toasts.map((notification, index) => (
        <div
          key={notification.id}
          style={{
            transform: `translateY(${index * 120}px)`,
            zIndex: 50 - index,
          }}
        >
          <NotificationToast
            notification={notification}
            onClose={() => removeNotification(notification.id)}
          />
        </div>
      ))}
    </div>
  );
}

export default NotificationToast;

