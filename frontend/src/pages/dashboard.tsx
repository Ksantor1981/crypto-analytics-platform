import { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
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

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import DashboardTour from '@/components/tour/DashboardTour';
import { DataExportCard } from '@/components/dashboard/DataExportCard';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface DashboardChannel {
  id: number;
  name: string;
  accuracy: number;
  signals: number;
  roi: number;
  status: string;
}

interface DashboardSignal {
  id: number;
  channel: string;
  pair: string;
  direction: string;
  entry: number;
  status: string;
  profit: number;
  time: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const { user: authUser, isAuthenticated } = useAuth();
  const [runTour, setRunTour] = useState(false);
  const [channels, setChannels] = useState<DashboardChannel[]>([]);
  const [recentSignals, setRecentSignals] = useState<DashboardSignal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        await apiClient.healthCheck();

        try {
          const channelsData = await apiClient.getChannels();
          if (Array.isArray(channelsData)) {
            setChannels(
              channelsData.map((ch: Record<string, unknown>) => ({
                id: ch.id as number,
                name: (ch.name || ch.username || 'Unknown') as string,
                accuracy: (ch.accuracy || ch.expected_accuracy || 0) as number,
                signals: (ch.signals_count || 0) as number,
                roi: (ch.average_roi || 0) as number,
                status: (ch.status || 'active') as string,
              }))
            );
          }
        } catch {
          // channels endpoint may require auth
        }

        try {
          const signalsRaw = await apiClient.getSignals();
          const signalsData = Array.isArray(signalsRaw)
            ? signalsRaw
            : signalsRaw?.signals || [];
          if (signalsData.length > 0) {
            setRecentSignals(
              signalsData.slice(0, 5).map((s: Record<string, unknown>) => ({
                id: s.id as number,
                channel: (s.channel_name ||
                  `Channel ${s.channel_id}`) as string,
                pair: (s.asset || s.symbol || 'N/A') as string,
                direction: (s.direction || 'LONG') as string,
                entry: (s.entry_price || 0) as number,
                status: ((s.status as string) || '')
                  .toLowerCase()
                  .includes('success')
                  ? 'success'
                  : ((s.status as string) || '').toLowerCase().includes('fail')
                    ? 'failed'
                    : 'pending',
                profit: (s.profit_loss || 0) as number,
                time: s.created_at
                  ? new Date(s.created_at as string).toLocaleString('ru-RU')
                  : '',
              }))
            );
          }
        } catch {
          // signals endpoint may require auth
        }
      } catch {
        // health check failed
      } finally {
        setLoading(false);
      }

      const tourCompleted = localStorage.getItem('dashboardTourCompleted');
      if (!tourCompleted) {
        setTimeout(() => setRunTour(true), 1000);
      }
    }
    void loadDashboard();
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
        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-8">
          {/* Header */}
          <div className="mb-8 dashboard-header">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
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
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <h3 className="text-base sm:text-lg font-semibold text-blue-900">
                      Тарифный план: {authUser?.subscription.plan || 'Free'}
                    </h3>
                    <p className="text-blue-700">
                      Отслеживается каналов: {channels.length}
                    </p>
                  </div>
                  <Button
                    className="bg-blue-600 hover:bg-blue-700"
                    onClick={() => router.push('/subscription')}
                  >
                    Обновить план
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <DataExportCard
            isAuthenticated={isAuthenticated}
            subscriptionPlan={authUser?.subscription.plan}
          />

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
                <div className="text-2xl font-bold">{channels.length}</div>
                <p className="text-xs text-muted-foreground">
                  активных каналов
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
                <div className="text-2xl font-bold">
                  {channels.length > 0
                    ? (
                        channels.reduce((s, c) => s + c.accuracy, 0) /
                        channels.length
                      ).toFixed(1)
                    : '—'}
                  %
                </div>
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
                <div className="text-2xl font-bold text-green-600">
                  {channels.length > 0
                    ? `+${(channels.reduce((s, c) => s + c.roi, 0) / channels.length).toFixed(1)}`
                    : '—'}
                  %
                </div>
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
                  <Button
                    size="sm"
                    className="flex items-center add-channel-button"
                    onClick={() => router.push('/channels')}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Добавить канал
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {channels.length === 0 && (
                    <p className="text-gray-500 text-center py-4">
                      Нет отслеживаемых каналов. Добавьте первый канал!
                    </p>
                  )}
                  {channels.map(channel => (
                    <div
                      key={channel.id}
                      className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 border border-gray-200 rounded-lg"
                    >
                      <div className="min-w-0">
                        <h4 className="font-semibold text-gray-900 truncate">
                          {channel.name}
                        </h4>
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-600 mt-1">
                          <span>Точность: {channel.accuracy}%</span>
                          <span>Сигналов: {channel.signals}</span>
                          <span className="text-green-600">
                            ROI: +{channel.roi}%
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Star className="h-4 w-4 text-yellow-400 fill-current" />
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/channels/${channel.id}`)}
                        >
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
                  {recentSignals.length === 0 && (
                    <p className="text-gray-500 text-center py-4">
                      Пока нет сигналов.
                    </p>
                  )}
                  {recentSignals.map(signal => (
                    <div
                      key={signal.id}
                      className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 border border-gray-200 rounded-lg"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
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
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Button
                    className="h-20 flex flex-col items-center justify-center"
                    variant="outline"
                    onClick={() => router.push('/channels')}
                  >
                    <Plus className="h-6 w-6 mb-2" />
                    Добавить канал
                  </Button>
                  <Button
                    className="h-20 flex flex-col items-center justify-center"
                    variant="outline"
                    onClick={() => router.push('/ratings')}
                  >
                    <BarChart3 className="h-6 w-6 mb-2" />
                    Рейтинги
                  </Button>
                  <Button
                    className="h-20 flex flex-col items-center justify-center"
                    variant="outline"
                    onClick={() => router.push('/signals')}
                  >
                    <TrendingUp className="h-6 w-6 mb-2" />
                    Все сигналы
                  </Button>
                  <Button
                    className="h-20 flex flex-col items-center justify-center"
                    variant="outline"
                    onClick={() => router.push('/alerts')}
                  >
                    <AlertTriangle className="h-6 w-6 mb-2" />
                    Алерты
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </>
  );
}
