import React, { useState, useEffect } from 'react';
import { GetServerSideProps } from 'next';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { SignalsList, SignalsStats } from '@/components/signals';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useAuth } from '@/contexts/AuthContext';
import { channelsApi, signalsApi } from '@/lib/api';
import { Channel, Signal } from '@/types';
import { formatDate } from '@/lib/utils';

interface ChannelDetailPageProps {
  channel: Channel;
  signals: Signal[];
}

export default function ChannelDetailPage({ channel, signals }: ChannelDetailPageProps) {
  const router = useRouter();
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);

  useEffect(() => {
    // Проверяем подписку пользователя
    checkSubscription();
  }, [channel.id]);

  const checkSubscription = async () => {
    try {
      // Здесь будет проверка подписки пользователя
      // const subscription = await subscriptionsApi.checkSubscription(channel.id);
      // setIsSubscribed(subscription.is_active);
    } catch (error) {
      console.error('Error checking subscription:', error);
    }
  };

  const handleSubscribe = async () => {
    setIsLoading(true);
    try {
      // Здесь будет логика подписки
      // await subscriptionsApi.subscribe(channel.id);
      setIsSubscribed(true);
    } catch (error) {
      console.error('Error subscribing:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUnsubscribe = async () => {
    setIsLoading(true);
    try {
      // Здесь будет логика отписки
      // await subscriptionsApi.unsubscribe(channel.id);
      setIsSubscribed(false);
    } catch (error) {
      console.error('Error unsubscribing:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (isActive: boolean) => {
    return isActive ? (
      <Badge variant="success">Активен</Badge>
    ) : (
      <Badge variant="secondary">Неактивен</Badge>
    );
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 80) return 'text-green-600';
    if (accuracy >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const channelSignals = signals.filter(signal => signal.channel?.id === channel.id);

  return (
    <>
      <Head>
        <title>{channel.name} - Crypto Analytics Platform</title>
        <meta name="description" content={channel.description} />
      </Head>

      <DashboardLayout>
        <div className="space-y-6">
          {/* Breadcrumb */}
          <nav className="flex" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-4">
              <li>
                <Link href="/channels" className="text-gray-400 hover:text-gray-500">
                  Каналы
                </Link>
              </li>
              <li>
                <span className="text-gray-400">/</span>
              </li>
              <li>
                <span className="text-gray-900 font-medium">{channel.name}</span>
              </li>
            </ol>
          </nav>

          {/* Channel header */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-8">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-6">
                  <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-2xl">
                      {channel.name.charAt(0)}
                    </span>
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">
                      {channel.name}
                    </h1>
                    <p className="text-gray-600 text-lg mb-4">
                      {channel.description}
                    </p>
                    <div className="flex items-center space-x-4">
                      <span className="text-sm text-gray-500">
                        {channel.username}
                      </span>
                      {getStatusBadge(channel.is_active)}
                      <span className="text-sm text-gray-500">
                        Создан {formatDate(channel.created_at)}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex flex-col items-end space-y-3">
                  {isSubscribed ? (
                    <Button
                      variant="outline"
                      onClick={handleUnsubscribe}
                      disabled={isLoading}
                    >
                      ✓ Подписан
                    </Button>
                  ) : (
                    <Button
                      variant="primary"
                      onClick={handleSubscribe}
                      disabled={isLoading}
                    >
                      💎 Подписаться за ${channel.subscription_price}
                    </Button>
                  )}
                  <Link href={`/channels/${channel.id}/analysis`}>
                    <Button variant="outline">
                      📊 Анализ ML
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </div>

          {/* Channel stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardBody className="p-6 text-center">
                <div className="text-3xl font-bold text-gray-900">
                  {channel.subscribers_count.toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">Подписчиков</div>
              </CardBody>
            </Card>

            <Card>
              <CardBody className="p-6 text-center">
                <div className={`text-3xl font-bold ${getAccuracyColor(channel.accuracy)}`}>
                  {channel.accuracy.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">Точность</div>
              </CardBody>
            </Card>

            <Card>
              <CardBody className="p-6 text-center">
                <div className="text-3xl font-bold text-gray-900">
                  {channel.total_signals}
                </div>
                <div className="text-sm text-gray-600">Всего сигналов</div>
              </CardBody>
            </Card>

            <Card>
              <CardBody className="p-6 text-center">
                <div className="text-3xl font-bold text-green-600">
                  +{channel.avg_profit.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">Средняя прибыль</div>
              </CardBody>
            </Card>
          </div>

          {/* Performance breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900">
                  Результативность
                </h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Успешных сигналов</span>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-green-600">
                        {channel.successful_signals}
                      </span>
                      <span className="text-gray-400">
                        из {channel.total_signals}
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{
                        width: `${(channel.successful_signals / channel.total_signals) * 100}%`
                      }}
                    ></div>
                  </div>
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>Неуспешных: {channel.total_signals - channel.successful_signals}</span>
                    <span>Процент успеха: {channel.accuracy.toFixed(1)}%</span>
                  </div>
                </div>
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900">
                  Подписка
                </h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Стоимость</span>
                    <span className="text-2xl font-bold text-gray-900">
                      ${channel.subscription_price}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Период</span>
                    <span className="text-gray-900">Месяц</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Статус</span>
                    {isSubscribed ? (
                      <Badge variant="success">Активна</Badge>
                    ) : (
                      <Badge variant="secondary">Не подписан</Badge>
                    )}
                  </div>
                  {!isSubscribed && (
                    <Button
                      variant="primary"
                      className="w-full"
                      onClick={handleSubscribe}
                      disabled={isLoading}
                    >
                      Подписаться сейчас
                    </Button>
                  )}
                </div>
              </CardBody>
            </Card>
          </div>

          {/* Signals section */}
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                Сигналы канала ({channelSignals.length})
              </h2>
              <Link href={`/signals?channel_id=${channel.id}`}>
                <Button variant="outline">
                  Все сигналы канала
                </Button>
              </Link>
            </div>

            {channelSignals.length > 0 ? (
              <>
                <SignalsStats signals={channelSignals} />
                <SignalsList
                  signals={channelSignals.slice(0, 10)} // Показываем только последние 10
                  showChannel={false}
                />
              </>
            ) : (
              <Card>
                <CardBody className="text-center py-12">
                  <div className="text-gray-400 text-6xl mb-4">⚡</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Нет сигналов
                  </h3>
                  <p className="text-gray-600">
                    Сигналы от этого канала появятся здесь
                  </p>
                </CardBody>
              </Card>
            )}
          </div>
        </div>
      </DashboardLayout>
    </>
  );
}

export const getServerSideProps: GetServerSideProps = async (context) => {
  const { id } = context.params!;

  try {
    // В реальном приложении здесь будут запросы к API
    // const channel = await channelsApi.getChannel(id as string);
    // const signals = await signalsApi.getSignals({ channel_id: id as string });

    // Моковые данные
    const channel: Channel = {
      id: id as string,
      name: 'Crypto Signals Pro',
      description: 'Профессиональные торговые сигналы криптовалют с высокой точностью',
      username: '@crypto_signals_pro',
      subscribers_count: 15000,
      accuracy: 78.5,
      total_signals: 245,
      successful_signals: 192,
      avg_profit: 12.3,
      created_at: new Date('2023-01-15').toISOString(),
      updated_at: new Date().toISOString(),
      is_active: true,
      subscription_price: 50
    };

    const signals: Signal[] = [
      {
        id: '1',
        asset: 'BTC/USDT',
        direction: 'long',
        entry_price: 45000,
        target_price: 48000,
        stop_loss: 43000,
        status: 'active',
        pnl: 2.5,
        confidence: 0.85,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        channel: channel
      },
      {
        id: '2',
        asset: 'ETH/USDT',
        direction: 'short',
        entry_price: 3200,
        target_price: 3000,
        stop_loss: 3350,
        status: 'completed',
        pnl: 6.25,
        confidence: 0.92,
        created_at: new Date(Date.now() - 86400000).toISOString(),
        updated_at: new Date().toISOString(),
        channel: channel
      }
    ];

    return {
      props: {
        channel,
        signals
      }
    };
  } catch (error) {
    console.error('Error fetching channel:', error);
    return {
      notFound: true
    };
  }
}; 