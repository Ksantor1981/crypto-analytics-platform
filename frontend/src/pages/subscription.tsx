import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import { formatDate } from '@/lib/utils';

interface Subscription {
  id: string;
  channel_id: string;
  channel_name: string;
  status: 'active' | 'cancelled' | 'expired';
  price: number;
  currency: 'USD';
  billing_period: 'monthly' | 'yearly';
  start_date: string;
  end_date: string;
  auto_renew: boolean;
  stripe_subscription_id?: string;
}

interface PricingPlan {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: 'USD';
  billing_period: 'monthly' | 'yearly';
  features: string[];
  popular?: boolean;
}

export default function SubscriptionPage() {
  const { user } = useAuth();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [pricingPlans, setPricingPlans] = useState<PricingPlan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);

  useEffect(() => {
    fetchSubscriptions();
    fetchPricingPlans();
  }, []);

  const fetchSubscriptions = async () => {
    try {
      const response = await apiClient.getSubscriptions();
      // Временно используем моковые данные, так как API может возвращать другую структуру
      setSubscriptions([
        {
          id: '1',
          channel_id: '1',
          channel_name: 'Crypto Signals Pro',
          status: 'active',
          price: 50,
          currency: 'USD',
          billing_period: 'monthly',
          start_date: new Date('2024-01-01').toISOString(),
          end_date: new Date('2024-02-01').toISOString(),
          auto_renew: true,
          stripe_subscription_id: 'sub_123',
        },
        {
          id: '2',
          channel_id: '2',
          channel_name: 'Technical Analysis Hub',
          status: 'cancelled',
          price: 30,
          currency: 'USD',
          billing_period: 'monthly',
          start_date: new Date('2023-12-01').toISOString(),
          end_date: new Date('2024-01-01').toISOString(),
          auto_renew: false,
        },
      ]);
    } catch (error) {
      console.error('Error fetching subscriptions:', error);
    }
  };

  const fetchPricingPlans = async () => {
    try {
      // Временно используем моковые данные
      setPricingPlans([
        {
          id: 'basic',
          name: 'Базовый',
          description: 'Для начинающих трейдеров',
          price: 29,
          currency: 'USD',
          billing_period: 'monthly',
          features: [
            'Доступ к 5 каналам',
            'Базовые сигналы',
            'Email уведомления',
            'Поддержка по email',
          ],
        },
        {
          id: 'pro',
          name: 'Профессиональный',
          description: 'Для активных трейдеров',
          price: 79,
          currency: 'USD',
          billing_period: 'monthly',
          features: [
            'Доступ к 20 каналам',
            'Премиум сигналы',
            'ML анализ',
            'Приоритетная поддержка',
            'API доступ',
            'Персональный менеджер',
          ],
          popular: true,
        },
        {
          id: 'enterprise',
          name: 'Корпоративный',
          description: 'Для команд и компаний',
          price: 199,
          currency: 'USD',
          billing_period: 'monthly',
          features: [
            'Неограниченный доступ',
            'Все каналы',
            'Кастомные интеграции',
            'Dedicated поддержка',
            'White-label решение',
            'Обучение команды',
          ],
        },
      ]);
    } catch (error) {
      console.error('Error fetching pricing plans:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpgrade = async (planId: string) => {
    try {
      setSelectedPlan(planId);
      await apiClient.updateSubscription(planId as 'free' | 'pro' | 'enterprise');
      // Обновляем данные после успешного обновления
      await fetchSubscriptions();
    } catch (error) {
      console.error('Error upgrading subscription:', error);
    } finally {
      setSelectedPlan(null);
    }
  };

  const handleCancelSubscription = async (subscriptionId: string) => {
    try {
      // Временно просто логируем, так как cancelSubscription не реализован в API
      console.log('Cancelling subscription:', subscriptionId);
      await fetchSubscriptions();
    } catch (error) {
      console.error('Error cancelling subscription:', error);
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <>
      <Head>
        <title>Подписки - Crypto Analytics Platform</title>
        <meta name="description" content="Управление подписками и тарифными планами" />
      </Head>

      <DashboardLayout>
        <div className="space-y-6">
          {/* Header */}
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Подписки</h1>
            <p className="text-gray-600">
              Управляйте своими подписками и тарифными планами
            </p>
          </div>

          {/* Current Subscriptions */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Текущие подписки
            </h2>
            <div className="grid gap-4">
              {subscriptions.map(subscription => (
                <Card key={subscription.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-medium">
                          {subscription.channel_name}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {subscription.price} {subscription.currency}/{subscription.billing_period}
                        </p>
                      </div>
                      <Badge
                        variant={
                          subscription.status === 'active'
                            ? 'default'
                            : subscription.status === 'cancelled'
                            ? 'secondary'
                            : 'destructive'
                        }
                      >
                        {subscription.status === 'active'
                          ? 'Активна'
                          : subscription.status === 'cancelled'
                          ? 'Отменена'
                          : 'Истекла'}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Начало:</span>
                        <br />
                        {formatDate(subscription.start_date)}
                      </div>
                      <div>
                        <span className="text-gray-500">Окончание:</span>
                        <br />
                        {formatDate(subscription.end_date)}
                      </div>
                    </div>
                  </CardContent>
                  <CardFooter>
                    <div className="flex space-x-2">
                      {subscription.status === 'active' && (
                        <Button
                          variant="outline"
                          onClick={() => handleCancelSubscription(subscription.id)}
                        >
                          Отменить
                        </Button>
                      )}
                      <Button variant="outline">Детали</Button>
                    </div>
                  </CardFooter>
                </Card>
              ))}
            </div>
          </div>

          {/* Pricing Plans */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Тарифные планы
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {pricingPlans.map(plan => (
                <Card
                  key={plan.id}
                  className={`relative ${
                    plan.popular ? 'ring-2 ring-blue-500' : ''
                  }`}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <Badge className="bg-blue-500 text-white">
                        Популярный
                      </Badge>
                    </div>
                  )}
                  <CardHeader>
                    <h3 className="text-xl font-semibold">{plan.name}</h3>
                    <p className="text-gray-600">{plan.description}</p>
                    <div className="text-3xl font-bold">
                      ${plan.price}
                      <span className="text-sm font-normal text-gray-500">
                        /{plan.billing_period}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-center">
                          <span className="text-green-500 mr-2">✓</span>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                  <CardFooter>
                    <Button
                      className="w-full"
                      onClick={() => handleUpgrade(plan.id)}
                      disabled={selectedPlan === plan.id}
                    >
                      {selectedPlan === plan.id ? 'Обновление...' : 'Выбрать план'}
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </DashboardLayout>
    </>
  );
}


