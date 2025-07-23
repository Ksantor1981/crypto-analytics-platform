import { useState } from 'react';
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
  Crown,
  Trophy,
  Medal,
  Star,
  TrendingDown,
  AlertTriangle,
  Shield,
  Users,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  Zap,
  Eye,
  ThumbsUp,
  ThumbsDown,
  Target,
  DollarSign,
} from 'lucide-react';

// Mock data for top channels
const topChannels = [
  {
    id: 3,
    rank: 1,
    name: 'CoinHunter',
    description: 'Поиск перспективных альткоинов с высочайшей точностью',
    accuracy: 91.2,
    signals: 203,
    roi: 31.5,
    subscribers: 15600,
    rating: 4.9,
    avatar: '🎯',
    badge: 'Лидер',
    monthlyGrowth: 12.3,
    winRate: 94.1,
    avgReturn: 18.7,
  },
  {
    id: 1,
    rank: 2,
    name: 'CryptoSignals Pro',
    description: 'Профессиональные сигналы для опытных трейдеров',
    accuracy: 87.5,
    signals: 156,
    roi: 24.3,
    subscribers: 12500,
    rating: 4.8,
    avatar: '🚀',
    badge: 'Проверенный',
    monthlyGrowth: 8.9,
    winRate: 89.2,
    avgReturn: 15.6,
  },
  {
    id: 2,
    rank: 3,
    name: 'TradingMaster',
    description: 'Стабильные ежедневные торговые возможности',
    accuracy: 82.1,
    signals: 89,
    roi: 18.7,
    subscribers: 8900,
    rating: 4.5,
    avatar: '📈',
    badge: 'Стабильный',
    monthlyGrowth: 6.2,
    winRate: 84.7,
    avgReturn: 12.3,
  },
];

// Mock data for worst channels (anti-rating)
const worstChannels = [
  {
    id: 6,
    rank: 1,
    name: 'ScamAlert',
    description: 'Известные мошеннические сигналы - избегать!',
    accuracy: 23.1,
    signals: 45,
    roi: -67.2,
    subscribers: 1200,
    rating: 1.2,
    avatar: '❌',
    badge: 'Опасно',
    monthlyLoss: -45.3,
    scamReports: 89,
    avgLoss: -34.5,
  },
  {
    id: 7,
    rank: 2,
    name: 'FakeSignals',
    description: 'Поддельные сигналы для накрутки статистики',
    accuracy: 31.8,
    signals: 78,
    roi: -52.1,
    subscribers: 2400,
    rating: 1.8,
    avatar: '🚫',
    badge: 'Фейк',
    monthlyLoss: -38.7,
    scamReports: 67,
    avgLoss: -28.9,
  },
  {
    id: 8,
    rank: 3,
    name: 'PumpDump Channel',
    description: 'Пампы без реальной стратегии',
    accuracy: 42.5,
    signals: 134,
    roi: -34.6,
    subscribers: 5600,
    rating: 2.1,
    avatar: '📉',
    badge: 'Памп&Дамп',
    monthlyLoss: -25.4,
    scamReports: 45,
    avgLoss: -19.7,
  },
];

// Categories for filtering
const categories = [
  { value: 'top', label: 'Топ каналы', icon: Crown },
  { value: 'anti', label: 'Антирейтинг', icon: AlertTriangle },
  { value: 'rising', label: 'Восходящие', icon: TrendingUp },
  { value: 'all', label: 'Все рейтинги', icon: BarChart3 },
];

export default function RatingsPage() {
  const [activeCategory, setActiveCategory] = useState('top');

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Crown className="h-6 w-6 text-yellow-500" />;
      case 2:
        return <Trophy className="h-6 w-6 text-gray-400" />;
      case 3:
        return <Medal className="h-6 w-6 text-amber-600" />;
      default:
        return (
          <span className="h-6 w-6 flex items-center justify-center font-bold text-gray-600">
            #{rank}
          </span>
        );
    }
  };

  const getBadgeColor = (badge: string) => {
    switch (badge) {
      case 'Лидер':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'Проверенный':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'Стабильный':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'Опасно':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'Фейк':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'Памп&Дамп':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <>
      <Head>
        <title>Рейтинги каналов - CryptoAnalytics</title>
        <meta
          name="description"
          content="Рейтинги лучших и худших криптовалютных каналов с торговыми сигналами"
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
                    className="text-gray-900 px-3 py-2 text-sm font-medium border-b-2 border-blue-600"
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
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Рейтинги каналов
            </h1>
            <p className="text-gray-600">
              Объективная оценка лучших и худших криптовалютных каналов
            </p>
          </div>

          {/* Category Tabs */}
          <div className="mb-8">
            <div className="flex flex-wrap gap-2">
              {categories.map(category => {
                const IconComponent = category.icon;
                return (
                  <button
                    key={category.value}
                    onClick={() => setActiveCategory(category.value)}
                    className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeCategory === category.value
                        ? 'bg-blue-600 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <IconComponent className="h-4 w-4 mr-2" />
                    {category.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* TOP CHANNELS */}
          {(activeCategory === 'top' || activeCategory === 'all') && (
            <div className="mb-12">
              <div className="flex items-center mb-6">
                <Crown className="h-6 w-6 text-yellow-500 mr-2" />
                <h2 className="text-2xl font-bold text-gray-900">
                  Топ-3 лучших каналов
                </h2>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {topChannels.map((channel, index) => (
                  <Card
                    key={channel.id}
                    className={`card-hover relative overflow-hidden ${
                      index === 0 ? 'ring-2 ring-yellow-400 shadow-lg' : ''
                    }`}
                  >
                    {index === 0 && (
                      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-yellow-400 to-yellow-600"></div>
                    )}

                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3">
                          {getRankIcon(channel.rank)}
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="text-2xl">{channel.avatar}</span>
                              <CardTitle className="text-lg">
                                {channel.name}
                              </CardTitle>
                            </div>
                            <div className="flex items-center space-x-2 mt-1">
                              <div className="flex items-center">
                                {[...Array(5)].map((_, i) => (
                                  <Star
                                    key={i}
                                    className={`h-3 w-3 ${
                                      i < Math.floor(channel.rating)
                                        ? 'text-yellow-400 fill-current'
                                        : 'text-gray-300'
                                    }`}
                                  />
                                ))}
                                <span className="text-xs text-gray-600 ml-1">
                                  {channel.rating}
                                </span>
                              </div>
                              <span
                                className={`text-xs px-2 py-1 rounded border ${getBadgeColor(channel.badge)}`}
                              >
                                {channel.badge}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                      <CardDescription className="mt-2">
                        {channel.description}
                      </CardDescription>
                    </CardHeader>

                    <CardContent>
                      {/* Key Metrics Grid */}
                      <div className="grid grid-cols-2 gap-4 mb-4">
                        <div className="text-center p-3 bg-green-50 rounded-md">
                          <div className="text-xl font-bold text-green-600">
                            {channel.accuracy}%
                          </div>
                          <div className="text-xs text-gray-600">Точность</div>
                        </div>
                        <div className="text-center p-3 bg-blue-50 rounded-md">
                          <div className="text-xl font-bold text-blue-600">
                            +{channel.roi}%
                          </div>
                          <div className="text-xs text-gray-600">ROI</div>
                        </div>
                        <div className="text-center p-3 bg-purple-50 rounded-md">
                          <div className="text-xl font-bold text-purple-600">
                            {channel.winRate}%
                          </div>
                          <div className="text-xs text-gray-600">Win Rate</div>
                        </div>
                        <div className="text-center p-3 bg-orange-50 rounded-md">
                          <div className="text-xl font-bold text-orange-600">
                            +{channel.avgReturn}%
                          </div>
                          <div className="text-xs text-gray-600">
                            Средняя прибыль
                          </div>
                        </div>
                      </div>

                      {/* Stats */}
                      <div className="space-y-2 text-sm mb-4">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Сигналов:</span>
                          <span className="font-medium">{channel.signals}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Подписчиков:</span>
                          <span className="font-medium">
                            {channel.subscribers.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Рост за месяц:</span>
                          <span className="font-medium text-green-600">
                            +{channel.monthlyGrowth}%
                          </span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex space-x-2">
                        <Link
                          href={`/channels/${channel.id}`}
                          className="flex-1"
                        >
                          <Button
                            variant="outline"
                            className="w-full"
                            size="sm"
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            Подробнее
                          </Button>
                        </Link>
                        <Button size="sm" className="flex-1">
                          <ThumbsUp className="h-4 w-4 mr-2" />
                          Подписаться
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* ANTI-RATING */}
          {(activeCategory === 'anti' || activeCategory === 'all') && (
            <div className="mb-12">
              <div className="flex items-center mb-6">
                <AlertTriangle className="h-6 w-6 text-red-500 mr-2" />
                <h2 className="text-2xl font-bold text-gray-900">
                  Антирейтинг - избегайте этих каналов
                </h2>
              </div>

              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                <div className="flex items-center">
                  <Shield className="h-5 w-5 text-red-600 mr-2" />
                  <p className="text-red-800 text-sm">
                    <strong>Предупреждение:</strong> Эти каналы показали крайне
                    низкую эффективность или признаки мошенничества. Мы
                    настоятельно рекомендуем избегать подписки на них.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {worstChannels.map(channel => (
                  <Card
                    key={channel.id}
                    className="card-hover border-red-200 bg-red-50"
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="flex items-center justify-center w-8 h-8 bg-red-100 rounded-full">
                            <span className="text-lg text-red-600 font-bold">
                              #{channel.rank}
                            </span>
                          </div>
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="text-2xl">{channel.avatar}</span>
                              <CardTitle className="text-lg text-red-900">
                                {channel.name}
                              </CardTitle>
                            </div>
                            <div className="flex items-center space-x-2 mt-1">
                              <div className="flex items-center">
                                {[...Array(5)].map((_, i) => (
                                  <Star
                                    key={i}
                                    className={`h-3 w-3 ${
                                      i < Math.floor(channel.rating)
                                        ? 'text-red-400 fill-current'
                                        : 'text-gray-300'
                                    }`}
                                  />
                                ))}
                                <span className="text-xs text-gray-600 ml-1">
                                  {channel.rating}
                                </span>
                              </div>
                              <span
                                className={`text-xs px-2 py-1 rounded border ${getBadgeColor(channel.badge)}`}
                              >
                                {channel.badge}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                      <CardDescription className="mt-2 text-red-700">
                        {channel.description}
                      </CardDescription>
                    </CardHeader>

                    <CardContent>
                      {/* Warning Metrics */}
                      <div className="grid grid-cols-2 gap-4 mb-4">
                        <div className="text-center p-3 bg-red-100 rounded-md">
                          <div className="text-xl font-bold text-red-600">
                            {channel.accuracy}%
                          </div>
                          <div className="text-xs text-gray-600">Точность</div>
                        </div>
                        <div className="text-center p-3 bg-red-100 rounded-md">
                          <div className="text-xl font-bold text-red-600">
                            {channel.roi}%
                          </div>
                          <div className="text-xs text-gray-600">ROI</div>
                        </div>
                        <div className="text-center p-3 bg-red-100 rounded-md">
                          <div className="text-xl font-bold text-red-600">
                            {channel.scamReports}
                          </div>
                          <div className="text-xs text-gray-600">Жалобы</div>
                        </div>
                        <div className="text-center p-3 bg-red-100 rounded-md">
                          <div className="text-xl font-bold text-red-600">
                            {channel.avgLoss}%
                          </div>
                          <div className="text-xs text-gray-600">
                            Средний убыток
                          </div>
                        </div>
                      </div>

                      {/* Warning Stats */}
                      <div className="space-y-2 text-sm mb-4">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Сигналов:</span>
                          <span className="font-medium">{channel.signals}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Подписчиков:</span>
                          <span className="font-medium">
                            {channel.subscribers.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">
                            Убытки за месяц:
                          </span>
                          <span className="font-medium text-red-600">
                            {channel.monthlyLoss}%
                          </span>
                        </div>
                      </div>

                      {/* Warning Actions */}
                      <div className="flex space-x-2">
                        <Button
                          variant="outline"
                          className="flex-1"
                          size="sm"
                          disabled
                        >
                          <AlertTriangle className="h-4 w-4 mr-2" />
                          Заблокирован
                        </Button>
                        <Button variant="outline" size="sm">
                          <ThumbsDown className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Rating Methodology */}
          <div className="mt-12">
            <Card className="border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="text-blue-900">
                  Методология рейтинга
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
                  <div>
                    <div className="flex items-center mb-2">
                      <Target className="h-4 w-4 text-blue-600 mr-2" />
                      <span className="font-medium text-blue-900">
                        Точность сигналов
                      </span>
                    </div>
                    <p className="text-blue-700">
                      Процент успешных торговых сигналов за последние 3 месяца
                    </p>
                  </div>
                  <div>
                    <div className="flex items-center mb-2">
                      <DollarSign className="h-4 w-4 text-blue-600 mr-2" />
                      <span className="font-medium text-blue-900">
                        ROI и прибыльность
                      </span>
                    </div>
                    <p className="text-blue-700">
                      Общая доходность следования сигналам канала
                    </p>
                  </div>
                  <div>
                    <div className="flex items-center mb-2">
                      <Users className="h-4 w-4 text-blue-600 mr-2" />
                      <span className="font-medium text-blue-900">
                        Обратная связь
                      </span>
                    </div>
                    <p className="text-blue-700">
                      Отзывы пользователей и количество жалоб
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


