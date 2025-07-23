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
        return 'text-green-600';
      case 'medium':
        return 'text-yellow-600';
      case 'high':
        return 'text-orange-600';
      case 'extreme':
        return 'text-red-600';
      default:
        return 'text-gray-600';
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
        <title>{channel.name} - CryptoAnalytics</title>
        <meta
          name="description"
          content={`Детальная информация о канале ${channel.name} - статистика, сигналы, аналитика`}
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
                    className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium"
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
                <span className="text-sm text-gray-600">Demo User</span>
                <Button variant="ghost" size="sm">
                  Выйти
                </Button>
              </div>
            </div>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Breadcrumb */}
          <div className="flex items-center space-x-2 text-sm text-gray-600 mb-6">
            <Link
              href="/channels"
              className="hover:text-blue-600 flex items-center"
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              Каналы
            </Link>
            <span>/</span>
            <span className="text-gray-900 font-medium">{channel.name}</span>
          </div>

          {/* Channel Header */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-start space-x-4 mb-4 lg:mb-0">
                <div className="text-4xl">{channel.avatar}</div>
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <h1 className="text-2xl font-bold text-gray-900">
                      {channel.name}
                    </h1>
                    <div className="flex items-center">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`h-4 w-4 ${
                            i < Math.floor(channel.rating)
                              ? 'text-yellow-400 fill-current'
                              : 'text-gray-300'
                          }`}
                        />
                      ))}
                      <span className="text-sm text-gray-600 ml-1">
                        ({channel.rating})
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-600 mb-3">{channel.description}</p>
                  <div className="flex flex-wrap gap-3 text-sm">
                    <span className="flex items-center text-gray-600">
                      <Users className="h-4 w-4 mr-1" />
                      {channel.subscribers.toLocaleString()} подписчиков
                    </span>
                    <span className="flex items-center text-gray-600">
                      <Activity className="h-4 w-4 mr-1" />
                      {channel.signals} сигналов
                    </span>
                    <span className="flex items-center text-gray-600">
                      <Clock className="h-4 w-4 mr-1" />
                      Активен с{' '}
                      {new Date(channel.joinedDate).toLocaleDateString('ru-RU')}
                    </span>
                    <span
                      className={`flex items-center ${getRiskColor(channel.riskLevel)}`}
                    >
                      <Shield className="h-4 w-4 mr-1" />
                      Риск:{' '}
                      {channel.riskLevel === 'low'
                        ? 'Низкий'
                        : channel.riskLevel === 'medium'
                          ? 'Средний'
                          : channel.riskLevel === 'high'
                            ? 'Высокий'
                            : 'Критический'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <Button
                  size="lg"
                  variant={channel.isFollowing ? 'outline' : 'default'}
                  className="flex items-center"
                >
                  {channel.isFollowing ? (
                    <>
                      <CheckCircle className="h-5 w-5 mr-2" />
                      Отслеживается
                    </>
                  ) : (
                    <>
                      <Plus className="h-5 w-5 mr-2" />
                      Отслеживать
                    </>
                  )}
                </Button>
                <Button variant="outline" size="lg">
                  <Bell className="h-5 w-5 mr-2" />
                  Уведомления
                </Button>
                <Button variant="outline" size="lg">
                  <Share2 className="h-5 w-5 mr-2" />
                  Поделиться
                </Button>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 mb-8">
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-green-600">
                  {channel.accuracy}%
                </div>
                <div className="text-xs text-gray-600">Точность</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-blue-600">
                  +{channel.roi}%
                </div>
                <div className="text-xs text-gray-600">ROI</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {channel.winRate}%
                </div>
                <div className="text-xs text-gray-600">Win Rate</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-orange-600">
                  +{channel.avgReturn}%
                </div>
                <div className="text-xs text-gray-600">Средняя прибыль</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-red-600">
                  {channel.maxDrawdown}%
                </div>
                <div className="text-xs text-gray-600">Max DD</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-indigo-600">
                  {channel.sharpeRatio}
                </div>
                <div className="text-xs text-gray-600">Sharpe Ratio</div>
              </CardContent>
            </Card>
          </div>

          {/* Tabs */}
          <div className="mb-8">
            <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
              {tabs.map(tab => {
                const IconComponent = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <IconComponent className="h-4 w-4 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Performance Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Динамика доходности</CardTitle>
                  <CardDescription>
                    Месячная доходность за последний год
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
                    <div className="text-center">
                      <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                      <p className="text-gray-600">График доходности</p>
                      <p className="text-xs text-gray-500">Демо данные</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recent Signals */}
              <Card>
                <CardHeader>
                  <CardTitle>Последние сигналы</CardTitle>
                  <CardDescription>Актуальные торговые сигналы</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {channel.recentSignals?.slice(0, 3).map(signal => (
                      <div
                        key={signal.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                      >
                        <div className="flex items-center space-x-3">
                          <span
                            className={`text-xs px-2 py-1 rounded ${getTypeColor(signal.type)}`}
                          >
                            {signal.type}
                          </span>
                          <div>
                            <div className="font-medium">{signal.pair}</div>
                            <div className="text-xs text-gray-600">
                              {new Date(signal.timestamp).toLocaleDateString('ru-RU')}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          {typeof signal.pnl === 'number' ? (
                            <div
                              className={`font-medium ${
                                signal.pnl > 0 ? 'text-green-600' : 'text-red-600'
                              }`}
                            >
                              {signal.pnl > 0 ? '+' : ''}
                              {signal.pnl.toFixed(2)}%
                            </div>
                          ) : (
                            <div className="font-medium text-gray-500">—</div>
                          )}
                          <div
                            className={`text-xs ${getStatusColor(signal.status)} px-2 py-1 rounded-full inline-block mt-1`}
                          >
                            {signal.status}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <Link href={`/channels/${channel.id}/signals`}>
                    <Button variant="outline" className="w-full mt-4" size="sm">
                      Все сигналы
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === 'signals' && (
            <Card>
              <CardHeader>
                <CardTitle>История сигналов</CardTitle>
                <CardDescription>
                  Все сигналы, опубликованные каналом
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Дата</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Пара</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Тип</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Вход</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Цели</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Стоп</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PnL</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Статус</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {channel.recentSignals?.map(signal => (
                        <tr key={signal.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{new Date(signal.timestamp).toLocaleString('ru-RU')}</td>
                          <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{signal.pair}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getTypeColor(signal.type)}`}>
                              {signal.type}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{signal.entryPrice}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{signal.targetPrice}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{signal.stopLoss}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {typeof signal.pnl === 'number' ? (
                              <div
                                className={`font-medium ${
                                  signal.pnl > 0 ? 'text-green-600' : 'text-red-600'
                                }`}
                              >
                                {signal.pnl > 0 ? '+' : ''}
                                {signal.pnl.toFixed(2)}%
                              </div>
                            ) : (
                              <div className="font-medium text-gray-500">—</div>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(signal.status)}`}>
                              {signal.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'analytics' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <Card>
                <CardHeader>
                  <CardTitle>Распределение по парам</CardTitle>
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
    </>
  );
}
