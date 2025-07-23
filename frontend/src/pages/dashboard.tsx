import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  TrendingUp,
  Users,
  BarChart3,
  AlertTriangle,
  Plus,
  Star,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
} from 'lucide-react';
import DashboardTour from '@/components/tour/DashboardTour';

// Mock data for demonstration
const mockChannels = [
  {
    id: 1,
    name: 'CryptoSignals Pro',
    accuracy: 87.5,
    signals: 156,
    roi: 24.3,
    status: 'active',
  },
  {
    id: 2,
    name: 'TradingMaster',
    accuracy: 82.1,
    signals: 89,
    roi: 18.7,
    status: 'active',
  },
  {
    id: 3,
    name: 'CoinHunter',
    accuracy: 91.2,
    signals: 203,
    roi: 31.5,
    status: 'active',
  },
];

const mockRecentSignals = [
  {
    id: 1,
    channel: 'CryptoSignals Pro',
    pair: 'BTC/USDT',
    direction: 'LONG',
    entry: 43250,
    status: 'success',
    profit: 5.2,
    time: '2 часа назад',
  },
  {
    id: 2,
    channel: 'TradingMaster',
    pair: 'ETH/USDT',
    direction: 'SHORT',
    entry: 2680,
    status: 'pending',
    profit: 0,
    time: '30 мин назад',
  },
  {
    id: 3,
    channel: 'CoinHunter',
    pair: 'BNB/USDT',
    direction: 'LONG',
    entry: 315,
    status: 'failed',
    profit: -2.1,
    time: '1 час назад',
  },
];

export default function DashboardPage() {
  const [runTour, setRunTour] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

    useEffect(() => {
    // Mock user data - in real app this would come from API
    setUser({
      name: 'Demo User',
      email: 'demo@cryptoanalytics.com',
      plan: 'Free',
      channelsUsed: 3,
      channelsLimit: 3,
    });
    setLoading(false);

    // Check if the tour should run
    const tourCompleted = localStorage.getItem('dashboardTourCompleted');
    if (!tourCompleted) {
      // Use a timeout to ensure the DOM is ready for the tour
      setTimeout(() => setRunTour(true), 1000);
    }
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <DashboardTour run={runTour} setRun={setRunTour} />
      <Head>
        <title>Панель управления - CryptoAnalytics</title>
        <meta
          name="description"
          content="Управляйте своими каналами и отслеживайте результаты"
        />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Link href="/" className="flex items-center">
                  <TrendingUp className="h-8 w-8 text-blue-600" />
                  <span className="ml-2 text-xl font-bold gradient-text">
                    CryptoAnalytics
                  </span>
                </Link>
                <div className="ml-8 flex space-x-4">
                  <Link
                    href="/dashboard"
                    className="text-gray-900 px-3 py-2 text-sm font-medium"
                  >
                    Панель
                  </Link>
                  <Link
                    href="/channels"
                    className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium"
                  >
                    Каналы
                  </Link>
                  <Link
                    href="/ratings"
                    className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium"
                  >
                    Рейтинги
                  </Link>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">
                  Привет, {user?.name}!
                </span>
                <Button variant="ghost" size="sm">
                  Выйти
                </Button>
              </div>
            </div>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8 dashboard-header">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Панель управления
            </h1>
            <p className="text-gray-600">
              Добро пожаловать в CryptoAnalytics! Отслеживайте ваши каналы и
              анализируйте результаты.
            </p>
          </div>

          {/* Plan Status */}
          <div className="mb-8">
            <Card className="border-blue-200 bg-blue-50">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-blue-900">
                      Тарифный план: {user?.plan}
                    </h3>
                    <p className="text-blue-700">
                      Используется каналов: {user?.channelsUsed} из{' '}
                      {user?.channelsLimit}
                    </p>
                  </div>
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    Обновить план
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 key-metrics">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Отслеживаемые каналы
                </CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{mockChannels.length}</div>
                <p className="text-xs text-muted-foreground">
                  из {user?.channelsLimit} доступных
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Средняя точность
                </CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">86.9%</div>
                <p className="text-xs text-muted-foreground">
                  <span className="text-green-600">+2.1%</span> за последний
                  месяц
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Общий ROI</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">+24.8%</div>
                <p className="text-xs text-muted-foreground">
                  за последние 30 дней
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Мои каналы */}
            <Card className="followed-channels-list">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Мои каналы</CardTitle>
                  <Button size="sm" className="flex items-center add-channel-button">
                    <Plus className="h-4 w-4 mr-2" />
                    Добавить канал
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockChannels.map(channel => (
                    <div
                      key={channel.id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
                    >
                      <div>
                        <h4 className="font-semibold text-gray-900">
                          {channel.name}
                        </h4>
                        <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                          <span>Точность: {channel.accuracy}%</span>
                          <span>Сигналов: {channel.signals}</span>
                          <span className="text-green-600">
                            ROI: +{channel.roi}%
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Star className="h-4 w-4 text-yellow-400 fill-current" />
                        <Button variant="outline" size="sm">
                          Детали
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Последние сигналы */}
            <Card className="recent-activity-feed">
              <CardHeader>
                <CardTitle>Последние сигналы</CardTitle>
                <CardDescription>
                  Актуальная информация по вашим каналам
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockRecentSignals.map(signal => (
                    <div
                      key={signal.id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
                    >
                      <div>
                        <div className="flex items-center space-x-2">
                          <h4 className="font-semibold text-gray-900">
                            {signal.pair}
                          </h4>
                          <span
                            className={`px-2 py-1 text-xs rounded ${
                              signal.direction === 'LONG'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {signal.direction}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">
                          {signal.channel}
                        </p>
                        <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                          <span>Вход: {signal.entry}</span>
                          <span className="flex items-center">
                            <Clock className="h-3 w-3 mr-1" />
                            {signal.time}
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div
                          className={`flex items-center ${
                            signal.status === 'success'
                              ? 'text-green-600'
                              : signal.status === 'failed'
                                ? 'text-red-600'
                                : 'text-gray-600'
                          }`}
                        >
                          {signal.status === 'success' && (
                            <ArrowUpRight className="h-4 w-4 mr-1" />
                          )}
                          {signal.status === 'failed' && (
                            <ArrowDownRight className="h-4 w-4 mr-1" />
                          )}
                          {signal.profit !== 0 && (
                            <span className="font-semibold">
                              {signal.profit > 0 ? '+' : ''}
                              {signal.profit}%
                            </span>
                          )}
                          {signal.status === 'pending' && (
                            <span className="text-xs">В ожидании</span>
                          )}
                        </div>
                        <div
                          className={`text-xs px-2 py-1 rounded mt-1 ${
                            signal.status === 'success'
                              ? 'bg-green-100 text-green-800'
                              : signal.status === 'failed'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-yellow-100 text-yellow-800'
                          }`}
                        >
                          {signal.status === 'success' && 'Успех'}
                          {signal.status === 'failed' && 'Неудача'}
                          {signal.status === 'pending' && 'Ожидание'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <div className="mt-8">
            <Card>
              <CardHeader>
                <CardTitle>Быстрые действия</CardTitle>
                <CardDescription>
                  Популярные функции для максимальной эффективности
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Button
                    className="h-20 flex flex-col items-center justify-center"
                    variant="outline"
                  >
                    <Plus className="h-6 w-6 mb-2" />
                    Добавить канал
                  </Button>
                  <Button
                    className="h-20 flex flex-col items-center justify-center"
                    variant="outline"
                  >
                    <BarChart3 className="h-6 w-6 mb-2" />
                    Посмотреть рейтинги
                  </Button>
                  <Button
                    className="h-20 flex flex-col items-center justify-center"
                    variant="outline"
                  >
                    <AlertTriangle className="h-6 w-6 mb-2" />
                    Антирейтинг каналов
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Demo Notice */}
          <div className="mt-8">
            <Card className="border-yellow-200 bg-yellow-50">
              <CardContent className="p-6">
                <div className="flex items-start">
                  <AlertTriangle className="h-5 w-5 text-yellow-600 mr-3 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-yellow-800">
                      Демо-режим
                    </h4>
                    <p className="text-yellow-700 text-sm mt-1">
                      Это демонстрационная версия. Данные не являются реальными.
                      Для получения доступа к актуальной аналитике
                      зарегистрируйтесь или войдите в систему.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </>
  );
}


