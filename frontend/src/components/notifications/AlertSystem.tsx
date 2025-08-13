import React, { useState, useEffect } from 'react';
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

const mockAlerts: Alert[] = [
  {
    id: '1',
    type: 'price',
    title: 'BTC Price Alert',
    description: 'Bitcoin выше $100,000',
    condition: 'BTC/USDT > 100000',
    enabled: true,
    triggered: false,
  },
  {
    id: '2',
    type: 'signal',
    title: 'High Confidence Signals',
    description: 'Сигналы с уверенностью > 90%',
    condition: 'confidence > 0.9',
    enabled: true,
    triggered: false,
  },
  {
    id: '3',
    type: 'profit',
    title: 'Target Reached',
    description: 'Достижение TP1',
    condition: 'target_1_reached',
    enabled: true,
    triggered: true,
    lastTriggered: new Date(Date.now() - 30 * 60 * 1000),
  },
];

export function AlertSystem() {
  const { addNotification } = useNotifications();
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);
  const [priceAlerts, setPriceAlerts] = useState<PriceAlert[]>([]);
  const [newAlert, setNewAlert] = useState({
    pair: 'BTC/USDT',
    targetPrice: '',
    condition: 'above' as 'above' | 'below',
  });

  // Мониторинг цен для алертов
  useEffect(() => {
    const checkPriceAlerts = () => {
      priceAlerts.forEach(alert => {
        if (!alert.enabled) return;

        // Здесь будет реальная проверка цен через API
        const shouldTrigger =
          alert.condition === 'above'
            ? alert.currentPrice > alert.targetPrice
            : alert.currentPrice < alert.targetPrice;

        if (shouldTrigger) {
          addNotification({
            type: 'price_alert',
            title: `Price Alert: ${alert.pair}`,
            message: `${alert.pair} достиг цели ${alert.targetPrice}`,
            urgent: true,
            read: false,
            pair: alert.pair,
            price: alert.currentPrice,
          });

          // Отключаем алерт после срабатывания
          setPriceAlerts(prev =>
            prev.map(a => (a.id === alert.id ? { ...a, enabled: false } : a))
          );
        }
      });
    };

    const interval = setInterval(checkPriceAlerts, 10000); // Проверка каждые 10 секунд
    return () => clearInterval(interval);
  }, [priceAlerts, addNotification]);

  // Симуляция различных типов алертов
  useEffect(() => {
    const triggerRandomAlerts = () => {
      const alertTypes = [
        {
          type: 'signal' as const,
          title: 'Новый высокоточный сигнал',
          message: 'ETH/USDT LONG с confidence 94%',
          urgent: true,
          read: false,
        },
        {
          type: 'target_reached' as const,
          title: 'Цель достигнута',
          message: 'BTC/USDT достиг TP1 (+3.5%)',
          urgent: false,
          read: false,
        },
        {
          type: 'warning' as const,
          title: 'Приближение к стоп-лоссу',
          message: 'ADA/USDT близко к SL (-1.8%)',
          urgent: true,
          read: false,
        },
        {
          type: 'info' as const,
          title: 'Высокая волатильность',
          message: 'DOGE показывает необычную активность',
          urgent: false,
          read: false,
        },
      ];

      // Случайный алерт каждые 15-30 секунд
      if (Math.random() < 0.3) {
        const randomAlert =
          alertTypes[Math.floor(Math.random() * alertTypes.length)];
        addNotification(randomAlert);
      }
    };

    const interval = setInterval(triggerRandomAlerts, 15000);
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

  const createPriceAlert = () => {
    if (!newAlert.targetPrice) return;

    const alert: PriceAlert = {
      id: Date.now().toString(),
      pair: newAlert.pair,
      targetPrice: parseFloat(newAlert.targetPrice),
      currentPrice: Math.random() * 100000, // Mock current price
      condition: newAlert.condition,
      enabled: true,
      created: new Date(),
    };

    setPriceAlerts(prev => [...prev, alert]);
    setNewAlert({ pair: 'BTC/USDT', targetPrice: '', condition: 'above' });

    addNotification({
      type: 'success',
      title: 'Алерт создан',
      message: `Price alert для ${alert.pair} настроен`,
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

            <Button onClick={createPriceAlert} className="w-full">
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


