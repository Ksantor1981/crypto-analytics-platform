import React, { useState, useEffect, useRef } from 'react';
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Target,
  DollarSign,
  Clock,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useNotifications } from '@/contexts/NotificationContext';
import apiClient from '@/lib/api';

interface PriceAlert {
  id: string;
  pair: string;
  targetPrice: number;
  currentPrice: number;
  condition: 'above' | 'below';
  enabled: boolean;
  created: Date;
}

interface Alert {
  id: string;
  type: 'price' | 'signal' | 'profit' | 'loss' | 'volume' | 'volatility';
  title: string;
  description: string;
  condition: string;
  enabled: boolean;
  triggered: boolean;
  lastTriggered?: Date;
  metadata?: any;
}

export function AlertSystem() {
  const { addNotification } = useNotifications();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [priceAlerts, setPriceAlerts] = useState<PriceAlert[]>([]);
  const [newAlert, setNewAlert] = useState({
    pair: 'BTC/USDT',
    targetPrice: '',
    condition: 'above' as 'above' | 'below',
  });

  const priceAlertsRef = useRef(priceAlerts);
  priceAlertsRef.current = priceAlerts;

  // Мониторинг цен: реальные котировки с API (нужна авторизация)
  useEffect(() => {
    if (!apiClient.isAuthenticated()) return;

    const tick = async () => {
      const active = priceAlertsRef.current.filter(a => a.enabled);
      for (const alert of active) {
        try {
          const base = alert.pair.split('/')[0]?.trim() || 'BTC';
          const res = await apiClient.getAnalyticsCurrentPrice(base);
          const cp = Number(res?.data?.current_price);
          if (!Number.isFinite(cp) || cp <= 0) continue;

          setPriceAlerts(prev =>
            prev.map(a => (a.id === alert.id ? { ...a, currentPrice: cp } : a))
          );

          const shouldTrigger =
            alert.condition === 'above'
              ? cp > alert.targetPrice
              : cp < alert.targetPrice;

          if (shouldTrigger) {
            addNotification({
              type: 'price_alert',
              title: `Price Alert: ${alert.pair}`,
              message: `${alert.pair} — условие выполнено (текущая ~$${cp.toFixed(2)})`,
              urgent: true,
              read: false,
              pair: alert.pair,
              price: cp,
            });
            setPriceAlerts(prev =>
              prev.map(a => (a.id === alert.id ? { ...a, enabled: false } : a))
            );
          }
        } catch {
          /* сеть / лимиты — пропуск цикла */
        }
      }
    };

    const interval = setInterval(() => {
      void tick();
    }, 25000);
    return () => clearInterval(interval);
  }, [addNotification]);

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'price':
        return <DollarSign className="h-5 w-5 text-blue-600" />;
      case 'signal':
        return <TrendingUp className="h-5 w-5 text-green-600" />;
      case 'profit':
        return <Target className="h-5 w-5 text-green-600" />;
      case 'loss':
        return <TrendingDown className="h-5 w-5 text-red-600" />;
      case 'volume':
        return <Clock className="h-5 w-5 text-purple-600" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
    }
  };

  const toggleAlert = (id: string) => {
    setAlerts(prev =>
      prev.map(alert =>
        alert.id === id ? { ...alert, enabled: !alert.enabled } : alert
      )
    );
  };

  const removeAlert = (id: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== id));
  };

  const createPriceAlert = async () => {
    if (!newAlert.targetPrice) return;
    if (!apiClient.isAuthenticated()) {
      addNotification({
        type: 'warning',
        title: 'Нужен вход',
        message: 'Войдите в аккаунт, чтобы подтягивать цены с API',
        read: false,
      });
      return;
    }

    const targetPrice = parseFloat(newAlert.targetPrice);
    const base = newAlert.pair.split('/')[0]?.trim() || 'BTC';
    let currentPrice = 0;
    try {
      const res = await apiClient.getAnalyticsCurrentPrice(base);
      currentPrice = Number(res?.data?.current_price) || 0;
    } catch {
      addNotification({
        type: 'error',
        title: 'Цена недоступна',
        message: 'Не удалось получить текущую цену. Проверьте API и лимиты.',
        read: false,
      });
      return;
    }

    if (!Number.isFinite(currentPrice) || currentPrice <= 0) {
      addNotification({
        type: 'error',
        title: 'Нет котировки',
        message: `Символ ${base}: пустой ответ price API`,
        read: false,
      });
      return;
    }

    const alert: PriceAlert = {
      id: Date.now().toString(),
      pair: newAlert.pair,
      targetPrice,
      currentPrice,
      condition: newAlert.condition,
      enabled: true,
      created: new Date(),
    };

    setPriceAlerts(prev => [...prev, alert]);
    setNewAlert({ pair: 'BTC/USDT', targetPrice: '', condition: 'above' });

    addNotification({
      type: 'success',
      title: 'Алерт создан',
      message: `${alert.pair}: текущая ~$${currentPrice.toFixed(2)}`,
      autoHide: true,
      read: false,
    });
  };

  return (
    <div className="space-y-6">
      {/* Создание нового price alert */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <DollarSign className="h-5 w-5 mr-2" />
            Создать Price Alert
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <select
              className="border rounded-lg px-3 py-2"
              value={newAlert.pair}
              onChange={e =>
                setNewAlert(prev => ({ ...prev, pair: e.target.value }))
              }
            >
              <option value="BTC/USDT">BTC/USDT</option>
              <option value="ETH/USDT">ETH/USDT</option>
              <option value="BNB/USDT">BNB/USDT</option>
              <option value="ADA/USDT">ADA/USDT</option>
            </select>

            <select
              className="border rounded-lg px-3 py-2"
              value={newAlert.condition}
              onChange={e =>
                setNewAlert(prev => ({
                  ...prev,
                  condition: e.target.value as 'above' | 'below',
                }))
              }
            >
              <option value="above">Выше</option>
              <option value="below">Ниже</option>
            </select>

            <input
              type="number"
              placeholder="Цена"
              className="border rounded-lg px-3 py-2"
              value={newAlert.targetPrice}
              onChange={e =>
                setNewAlert(prev => ({ ...prev, targetPrice: e.target.value }))
              }
            />

            <Button onClick={() => void createPriceAlert()} className="w-full">
              Создать Alert
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Активные price alerts */}
      {priceAlerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Price Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {priceAlerts.map(alert => (
                <div
                  key={alert.id}
                  className={`flex items-center justify-between p-3 rounded-lg border ${
                    alert.enabled
                      ? 'border-green-200 bg-green-50'
                      : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <DollarSign
                      className={`h-4 w-4 ${alert.enabled ? 'text-green-600' : 'text-gray-400'}`}
                    />
                    <div>
                      <p className="font-medium">
                        {alert.pair} {alert.condition === 'above' ? '>' : '<'} $
                        {alert.targetPrice.toLocaleString()}
                      </p>
                      <p className="text-sm text-gray-500">
                        Текущая: ${alert.currentPrice.toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        setPriceAlerts(prev =>
                          prev.map(a =>
                            a.id === alert.id
                              ? { ...a, enabled: !a.enabled }
                              : a
                          )
                        )
                      }
                    >
                      {alert.enabled ? 'Выключить' : 'Включить'}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        setPriceAlerts(prev =>
                          prev.filter(a => a.id !== alert.id)
                        )
                      }
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Системные алерты */}
      <Card>
        <CardHeader>
          <CardTitle>Системные алерты</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {alerts.length === 0 && (
              <p className="text-sm text-gray-500 py-4 text-center">
                Нет предустановленных системных алертов. Создайте price alert выше
                или дождитесь интеграции с пользовательскими правилами (Pro).
              </p>
            )}
            {alerts.map(alert => (
              <div
                key={alert.id}
                className={`flex items-center justify-between p-4 rounded-lg border ${
                  alert.enabled
                    ? alert.triggered
                      ? 'border-yellow-200 bg-yellow-50'
                      : 'border-green-200 bg-green-50'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-center space-x-3">
                  {getAlertIcon(alert.type)}
                  <div>
                    <h4 className="font-medium">{alert.title}</h4>
                    <p className="text-sm text-gray-600">{alert.description}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Условие: {alert.condition}
                    </p>
                    {alert.lastTriggered && (
                      <p className="text-xs text-yellow-600 mt-1">
                        Последнее срабатывание:{' '}
                        {alert.lastTriggered.toLocaleTimeString()}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <div
                    className={`px-2 py-1 rounded-full text-xs ${
                      alert.triggered
                        ? 'bg-yellow-100 text-yellow-800'
                        : alert.enabled
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {alert.triggered
                      ? 'Сработал'
                      : alert.enabled
                        ? 'Активен'
                        : 'Выключен'}
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleAlert(alert.id)}
                  >
                    {alert.enabled ? 'Выключить' : 'Включить'}
                  </Button>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeAlert(alert.id)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Статистика алертов */}
      <Card>
        <CardHeader>
          <CardTitle>Статистика алертов</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {alerts.filter(a => a.enabled).length}
              </div>
              <div className="text-sm text-gray-600">Активных</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {alerts.filter(a => a.triggered).length}
              </div>
              <div className="text-sm text-gray-600">Сработало</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {priceAlerts.filter(a => a.enabled).length}
              </div>
              <div className="text-sm text-gray-600">Price Alerts</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {alerts.length + priceAlerts.length}
              </div>
              <div className="text-sm text-gray-600">Всего</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default AlertSystem;


