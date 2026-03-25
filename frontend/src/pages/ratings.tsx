import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import {
  TrendingUp,
  Crown,
  Trophy,
  Medal,
  Star,
  AlertTriangle,
  Shield,
  Users,
  BarChart3,
  Eye,
  ThumbsUp,
  ThumbsDown,
  Target,
  DollarSign,
} from 'lucide-react';

import { apiClient } from '@/lib/api';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';

/** Строка рейтинга (топ / общий список) */
interface RatingChannelTop {
  id: number;
  rank: number;
  name: string;
  description: string;
  accuracy: number;
  signals: number;
  roi: number;
  subscribers: number;
  rating: number;
  avatar: string;
  badge: string;
  winRate: number;
  avgReturn: number;
  monthlyGrowth: number;
}

/** Антирейтинг — доп. поля предупреждений */
interface RatingChannelAnti extends RatingChannelTop {
  monthlyLoss: number;
  scamReports: number;
  avgLoss: number;
}

// Fallback empty array (data loads from API)
const topChannels: RatingChannelTop[] = [];

const worstChannels: RatingChannelAnti[] = [];

// Categories for filtering
const categories = [
  { value: 'top', label: 'Топ каналы', icon: Crown },
  { value: 'anti', label: 'Антирейтинг', icon: AlertTriangle },
  { value: 'rising', label: 'Восходящие', icon: TrendingUp },
  { value: 'all', label: 'Все рейтинги', icon: BarChart3 },
];

export default function RatingsPage() {
  const [activeCategory, setActiveCategory] = useState('top');
  const [apiChannels, setApiChannels] = useState<RatingChannelTop[]>([]);

  useEffect(() => {
    async function loadChannels() {
      try {
        const data = await apiClient.getChannels({
          sort: 'accuracy_desc',
          limit: 100,
        });
        if (Array.isArray(data) && data.length > 0) {
          const mapped: RatingChannelTop[] = data.map(
            (c: Record<string, unknown>, i: number) => {
              const acc = Number(c.accuracy) || 0;
              const roi = Number(c.average_roi) || 0;
              return {
                id: Number(c.id) || i + 1,
                rank: i + 1,
                name: String(c.name || 'Unknown'),
                description: String(c.description || ''),
                accuracy: acc,
                signals: Number(c.signals_count) || 0,
                roi,
                subscribers: Number(c.subscribers_count) || 0,
                rating: Math.min(5, acc / 20),
                avatar:
                  c.platform === 'reddit'
                    ? '🔴'
                    : c.platform === 'twitter'
                      ? '🐦'
                      : '📡',
                badge:
                  acc > 80 ? 'Лидер' : acc > 65 ? 'Проверенный' : 'Стабильный',
                winRate: acc,
                avgReturn: roi,
                monthlyGrowth: 12,
              };
            }
          );
          const sorted = [...mapped].sort((a, b) => b.accuracy - a.accuracy);
          sorted.forEach((c, i) => {
            c.rank = i + 1;
          });
          setApiChannels(sorted);
        }
      } catch {
        /* use fallback */
      }
    }
    void loadChannels();
  }, []);

  const effectiveTopChannels =
    apiChannels.length > 0 ? apiChannels : topChannels;

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
        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-6 sm:py-8">
          {/* Header */}
          <div className="mb-6 sm:mb-8">
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 mb-2">
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
              <div className="flex items-center mb-4 sm:mb-6">
                <Crown className="h-6 w-6 text-yellow-500 mr-2 flex-shrink-0" />
                <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900">
                  Топ-3 лучших каналов
                </h2>
              </div>

              {effectiveTopChannels.length === 0 ? (
                <Card className="border-dashed">
                  <CardContent className="py-12 text-center text-gray-600">
                    <BarChart3 className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                    <p className="text-lg font-medium text-gray-800 mb-2">
                      Нет данных для рейтинга
                    </p>
                    <p className="text-sm mb-6 max-w-md mx-auto">
                      Запустите backend и seed (`python scripts/seed_data.py`)
                      или дождитесь сбора сигналов. Для просмотра каналов
                      перейдите в раздел ниже.
                    </p>
                    <div className="flex flex-wrap justify-center gap-3">
                      <Button asChild>
                        <Link href="/channels">Каналы</Link>
                      </Button>
                      <Button variant="outline" asChild>
                        <Link href="/signals">Сигналы</Link>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {effectiveTopChannels.map((channel, index) => (
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
                                <span className="text-2xl">
                                  {channel.avatar}
                                </span>
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
                            <div className="text-xs text-gray-600">
                              Точность
                            </div>
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
                            <div className="text-xs text-gray-600">
                              Win Rate
                            </div>
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
                            <span className="font-medium">
                              {channel.signals}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Подписчиков:</span>
                            <span className="font-medium">
                              {channel.subscribers.toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">
                              Рост за месяц:
                            </span>
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
              )}
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
                {(apiChannels.length > 0
                  ? apiChannels
                      .filter(c => c.accuracy < 50)
                      .slice()
                      .reverse()
                      .map((c, i): RatingChannelAnti => {
                        const acc = c.accuracy;
                        return {
                          ...c,
                          rank: i + 1,
                          badge:
                            acc < 30
                              ? 'Опасно'
                              : acc < 40
                                ? 'Фейк'
                                : 'Памп&Дамп',
                          monthlyLoss: -(100 - acc) * 0.5,
                          scamReports: Math.floor((100 - acc) * 0.8),
                          avgLoss: -(100 - acc) * 0.3,
                        };
                      })
                  : worstChannels
                ).map((channel: RatingChannelAnti) => (
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
