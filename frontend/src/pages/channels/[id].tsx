import { useState } from 'react';
import { useChannel } from '@/hooks/useChannel';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  TrendingUp,
  ArrowLeft,
  Star,
  Users,
  BarChart3,
  AlertTriangle,
  Plus,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  CheckCircle,
  XCircle,
  Zap,
  Target,
  DollarSign,
  TrendingDown,
  Calendar,
  Activity,
  Eye,
  Bell,
  Share2,
  Settings,
  Shield,
} from 'lucide-react';



export default function ChannelDetailPage() {
  const router = useRouter();
    const { id } = router.query;
  const [activeTab, setActiveTab] = useState('overview');

  const { data: channel, isLoading, isError, error } = useChannel(id as string | undefined);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 className="h-16 w-16 animate-spin text-blue-600" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col justify-center items-center min-h-screen">
        <AlertTriangle className="h-16 w-16 text-red-500" />
        <h2 className="mt-4 text-xl font-semibold">Ошибка при загрузке данных</h2>
        <p className="text-gray-600">{(error as Error)?.message || 'Не удалось получить информацию о канале.'}</p>
        <Link href="/channels">
          <Button variant="outline" className="mt-4">Вернуться к списку каналов</Button>
        </Link>
      </div>
    );
  }

  if (!channel) {
    return (
      <div className="flex flex-col justify-center items-center min-h-screen">
        <h2 className="text-xl font-semibold">Канал не найден</h2>
        <Link href="/channels">
          <Button variant="outline" className="mt-4">Вернуться к списку каналов</Button>
        </Link>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return 'text-blue-600 bg-blue-100';
      case 'closed':
        return 'text-green-600 bg-green-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'LONG':
        return 'text-green-600 bg-green-100';
      case 'SHORT':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'text-green-600 bg-green-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'high':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const tabs = [
    { id: 'overview', label: 'Обзор', icon: BarChart3 },
    { id: 'signals', label: 'Сигналы', icon: Zap },
    { id: 'analytics', label: 'Аналитика', icon: TrendingUp },
    { id: 'reviews', label: 'Отзывы', icon: Star },
  ];

  return (
    <>
      <Head>
        <title>{channel.name} - Crypto Analytics Platform</title>
        <meta name="description" content={`Детальная информация о канале ${channel.name}`} />
      </Head>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-4">
                <Link href="/channels">
                  <Button variant="ghost" size="sm">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Назад к каналам
                  </Button>
                </Link>
                <div className="h-6 w-px bg-gray-300" />
                <div>
                  <h1 className="text-xl font-semibold text-gray-900">
                    {channel.name}
                  </h1>
                  <p className="text-sm text-gray-500">
                    {channel.platform} • {channel.category}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Button variant="outline" size="sm">
                  <Share2 className="h-4 w-4 mr-2" />
                  Поделиться
                </Button>
                <Button variant="outline" size="sm">
                  <Bell className="h-4 w-4 mr-2" />
                  Подписаться
                </Button>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Добавить в избранное
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Channel Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Channel Info */}
            <div className="lg:col-span-1">
              <Card>
                <CardHeader>
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center">
                      <span className="text-white font-semibold text-lg">
                        {channel.name.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <CardTitle className="text-lg">{channel.name}</CardTitle>
                      <CardDescription>
                        {channel.platform} • {channel.category}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Key Metrics */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {channel.accuracy}%
                      </div>
                      <div className="text-xs text-gray-600">Точность</div>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {channel.roi}%
                      </div>
                      <div className="text-xs text-gray-600">ROI</div>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Подписчиков:</span>
                      <span className="font-medium">{channel.subscribers}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Сигналов:</span>
                      <span className="font-medium">{channel.signals_count}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Рейтинг:</span>
                      <div className="flex items-center">
                        <Star className="h-4 w-4 text-yellow-400 fill-current" />
                        <span className="ml-1 font-medium">{channel.rating}</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="space-y-2">
                    <Button className="w-full">
                      <Bell className="h-4 w-4 mr-2" />
                      Подписаться на уведомления
                    </Button>
                    <Button variant="outline" className="w-full">
                      <Settings className="h-4 w-4 mr-2" />
                      Настройки
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Stats */}
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle className="text-lg">Быстрая статистика</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="h-4 w-4 text-green-500" />
                      <span className="text-sm text-gray-600">Успешных сигналов</span>
                    </div>
                    <span className="font-medium">87%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4 text-blue-500" />
                      <span className="text-sm text-gray-600">Среднее время</span>
                    </div>
                    <span className="font-medium">2.3ч</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Target className="h-4 w-4 text-purple-500" />
                      <span className="text-sm text-gray-600">Точность входа</span>
                    </div>
                    <span className="font-medium">92%</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Right Column - Content */}
            <div className="lg:col-span-2">
              {/* Tabs */}
              <div className="bg-white rounded-lg shadow-sm border mb-6">
                <div className="border-b">
                  <nav className="flex space-x-8 px-6">
                    {[
                      { id: 'overview', label: 'Обзор', icon: BarChart3 },
                      { id: 'signals', label: 'Сигналы', icon: Activity },
                      { id: 'analytics', label: 'Аналитика', icon: TrendingUp },
                      { id: 'reviews', label: 'Отзывы', icon: Star },
                    ].map((tab) => {
                      const Icon = tab.icon;
                      return (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTab(tab.id)}
                          className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                            activeTab === tab.id
                              ? 'border-blue-500 text-blue-600'
                              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                          }`}
                        >
                          <Icon className="h-4 w-4" />
                          <span>{tab.label}</span>
                        </button>
                      );
                    })}
                  </nav>
                </div>
              </div>

              {/* Tab Content */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Описание канала</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-gray-700 leading-relaxed">
                        {channel.description || 'Описание канала отсутствует.'}
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Последние сигналы</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {channel.recent_signals?.slice(0, 5).map((signal, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between p-4 border rounded-lg"
                          >
                            <div className="flex items-center space-x-3">
                              <div
                                className={`w-3 h-3 rounded-full ${
                                  signal.status === 'open'
                                    ? 'bg-blue-500'
                                    : signal.status === 'closed'
                                    ? 'bg-green-500'
                                    : 'bg-red-500'
                                }`}
                              />
                              <div>
                                <div className="font-medium">{signal.symbol}</div>
                                <div className="text-sm text-gray-500">
                                  {signal.type} • {signal.entry_price}
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div
                                className={`font-medium ${
                                  (signal.pnl || 0) > 0 ? 'text-green-600' : 'text-red-600'
                                }`}
                              >
                                {(signal.pnl || 0) > 0 ? '+' : ''}{(signal.pnl || 0)}%
                              </div>
                              <div className="text-sm text-gray-500">
                                {signal.status}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {activeTab === 'signals' && (
                <Card>
                  <CardHeader>
                    <CardTitle>История сигналов</CardTitle>
                    <CardDescription>
                      Полная история всех сигналов канала
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {channel.recent_signals?.map((signal, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                        >
                          <div className="flex items-center space-x-4">
                            <div className="flex items-center space-x-2">
                              <span
                                className={`px-2 py-1 rounded text-xs font-medium ${getTypeColor(
                                  signal.type
                                )}`}
                              >
                                {signal.type}
                              </span>
                              <span
                                className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(
                                  signal.status
                                )}`}
                              >
                                {signal.status}
                              </span>
                            </div>
                            <div>
                              <div className="font-medium">{signal.symbol}</div>
                              <div className="text-sm text-gray-500">
                                Вход: {signal.entry_price} | Выход: {signal.exit_price || '—'}
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div
                              className={`font-medium ${
                                (signal.pnl || 0) > 0 ? 'text-green-600' : 'text-red-600'
                              }`}
                            >
                              {(signal.pnl || 0) > 0 ? '+' : ''}{(signal.pnl || 0)}%
                            </div>
                            <div className="text-sm text-gray-500">
                              {signal.timestamp}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {activeTab === 'analytics' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Распределение по типам</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
                        <div className="text-center">
                          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                          <p className="text-gray-600">Pie Chart - Типы сигналов</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Торговые пары</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
                        <div className="text-center">
                          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                          <p className="text-gray-600">Pie Chart - Торговые пары</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Временное распределение</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
                        <div className="text-center">
                          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                          <p className="text-gray-600">
                            Heat Map - Активность по часам
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {activeTab === 'reviews' && (
                <Card>
                  <CardHeader>
                    <CardTitle>Отзывы пользователей</CardTitle>
                    <CardDescription>
                      Что говорят подписчики о канале
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                              А
                            </div>
                            <span className="font-medium">Алексей К.</span>
                            <div className="flex items-center">
                              {[...Array(5)].map((_, i) => (
                                <Star
                                  key={i}
                                  className="h-3 w-3 text-yellow-400 fill-current"
                                />
                              ))}
                            </div>
                          </div>
                          <span className="text-xs text-gray-600">3 дня назад</span>
                        </div>
                        <p className="text-gray-700">
                          Отличный канал! Сигналы действительно работают, уже
                          получил +15% за месяц. Особенно нравится детальный анализ
                          перед каждым сигналом.
                        </p>
                      </div>

                      <div className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                              М
                            </div>
                            <span className="font-medium">Мария Д.</span>
                            <div className="flex items-center">
                              {[...Array(4)].map((_, i) => (
                                <Star
                                  key={i}
                                  className="h-3 w-3 text-yellow-400 fill-current"
                                />
                              ))}
                              <Star className="h-3 w-3 text-gray-300" />
                            </div>
                          </div>
                          <span className="text-xs text-gray-600">
                            1 неделю назад
                          </span>
                        </div>
                        <p className="text-gray-700">
                          Хороший канал, но иногда сигналы приходят с задержкой. В
                          целом доволен результатами - стабильная прибыль.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// Отключаем SSG для этой страницы
export async function getServerSideProps() {
  return {
    props: {},
  };
}
