import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card, CardHeader, CardBody, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/Badge';
import { useAuth } from '@/contexts/AuthContext';
import { subscriptionsApi } from '@/lib/api';
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
      // const response = await subscriptionsApi.getUserSubscriptions();
      // setSubscriptions(response.data);

      // Моковые данные
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
      // const response = await subscriptionsApi.getPricingPlans();
      // setPricingPlans(response.data);

      // Моковые данные
      setPricingPlans([
        {
          id: 'basic',
          name: 'Базовый',
          description: 'Для начинающих трейдеров',
          price: 29,
          currency: 'USD',
          billing_period: 'monthly',
          features: [
            'До 3 каналов',
            'Базовая аналитика',
            'Email поддержка',
            'Мобильные уведомления',
          ],
        },
        {
          id: 'pro',
          name: 'Профессиональный',
          description: 'Для опытных трейдеров',
          price: 79,
          currency: 'USD',
          billing_period: 'monthly',
          features: [
            'До 10 каналов',
            'Продвинутая аналитика',
            'ML прогнозы',
            'Приоритетная поддержка',
            'API доступ',
            'Экспорт данных',
          ],
          popular: true,
        },
        {
          id: 'enterprise',
          name: 'Корпоративный',
          description: 'Для профессиональных команд',
          price: 199,
          currency: 'USD',
          billing_period: 'monthly',
          features: [
            'Неограниченное количество каналов',
            'Полная аналитика',
            'Персональный менеджер',
            'Кастомные интеграции',
            'White-label решения',
            'SLA гарантии',
          ],
        },
      ]);
    } catch (error) {
      console.error('Error fetching pricing plans:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubscribe = async (planId: string) => {
    setSelectedPlan(planId);
    try {
      // Интеграция с Stripe
      // const response = await subscriptionsApi.createCheckoutSession(planId);
      // window.location.href = response.checkout_url;

      console.log('Subscribing to plan:', planId);
      // Здесь будет редирект на Stripe Checkout
    } catch (error) {
      console.error('Error creating subscription:', error);
    } finally {
      setSelectedPlan(null);
    }
  };

  const handleCancelSubscription = async (subscriptionId: string) => {
    try {
      // await subscriptionsApi.cancelSubscription(subscriptionId);
      await fetchSubscriptions();
    } catch (error) {
      console.error('Error cancelling subscription:', error);
    }
  };

  const handleReactivateSubscription = async (subscriptionId: string) => {
    try {
      // await subscriptionsApi.reactivateSubscription(subscriptionId);
      await fetchSubscriptions();
    } catch (error) {
      console.error('Error reactivating subscription:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="success">Активна</Badge>;
      case 'cancelled':
        return <Badge variant="warning">Отменена</Badge>;
      case 'expired':
        return <Badge variant="danger">Истекла</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Загрузка...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <>
      <Head>
        <title>Подписки - Crypto Analytics Platform</title>
        <meta
          name="description"
          content="Управление подписками и тарифными планами"
        />
      </Head>

      <DashboardLayout>
        <div className="space-y-8">
          {/* Header */}
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900">Подписки</h1>
            <p className="mt-2 text-gray-600">
              Управляйте вашими подписками и выберите подходящий тарифный план
            </p>
          </div>

          {/* Current subscriptions */}
          {subscriptions.length > 0 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">
                Текущие подписки
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {subscriptions.map(subscription => (
                  <Card key={subscription.id}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-gray-900">
                          {subscription.channel_name}
                        </h3>
                        {getStatusBadge(subscription.status)}
                      </div>
                    </CardHeader>
                    <CardBody className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Стоимость</span>
                        <span className="font-semibold">
                          ${subscription.price}/
                          {subscription.billing_period === 'monthly'
                            ? 'мес'
                            : 'год'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Начало</span>
                        <span className="text-sm">
                          {formatDate(subscription.start_date)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Окончание</span>
                        <span className="text-sm">
                          {formatDate(subscription.end_date)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Автопродление</span>
                        <span className="text-sm">
                          {subscription.auto_renew ? 'Включено' : 'Выключено'}
                        </span>
                      </div>
                    </CardBody>
                    <CardFooter>
                      {subscription.status === 'active' ? (
                        <Button
                          variant="outline"
                          className="w-full"
                          onClick={() =>
                            handleCancelSubscription(subscription.id)
                          }
                        >
                          Отменить подписку
                        </Button>
                      ) : subscription.status === 'cancelled' ? (
                        <Button
                          variant="primary"
                          className="w-full"
                          onClick={() =>
                            handleReactivateSubscription(subscription.id)
                          }
                        >
                          Возобновить подписку
                        </Button>
                      ) : (
                        <Button variant="outline" className="w-full" disabled>
                          Подписка истекла
                        </Button>
                      )}
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Pricing plans */}
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-semibold text-gray-900">
                Тарифные планы
              </h2>
              <p className="mt-2 text-gray-600">
                Выберите план, который подходит для ваших потребностей
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {pricingPlans.map(plan => (
                <Card
                  key={plan.id}
                  className={`relative ${plan.popular ? 'border-blue-500 border-2' : ''}`}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <Badge variant="primary">Популярный</Badge>
                    </div>
                  )}

                  <CardHeader className="text-center">
                    <h3 className="text-xl font-semibold text-gray-900">
                      {plan.name}
                    </h3>
                    <p className="text-gray-600 mt-2">{plan.description}</p>
                    <div className="mt-4">
                      <span className="text-4xl font-bold text-gray-900">
                        ${plan.price}
                      </span>
                      <span className="text-gray-600">
                        /{plan.billing_period === 'monthly' ? 'мес' : 'год'}
                      </span>
                    </div>
                  </CardHeader>

                  <CardBody>
                    <ul className="space-y-3">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-green-500 mr-2">✓</span>
                          <span className="text-gray-700">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </CardBody>

                  <CardFooter>
                    <Button
                      variant={plan.popular ? 'primary' : 'outline'}
                      className="w-full"
                      onClick={() => handleSubscribe(plan.id)}
                      disabled={selectedPlan === plan.id}
                    >
                      {selectedPlan === plan.id
                        ? 'Обработка...'
                        : 'Выбрать план'}
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          </div>

          {/* FAQ */}
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900">
              Часто задаваемые вопросы
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardBody>
                  <h3 className="font-semibold text-gray-900 mb-2">
                    Как отменить подписку?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Вы можете отменить подписку в любое время через эту
                    страницу. Доступ к каналам сохранится до окончания
                    оплаченного периода.
                  </p>
                </CardBody>
              </Card>

              <Card>
                <CardBody>
                  <h3 className="font-semibold text-gray-900 mb-2">
                    Можно ли изменить план?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Да, вы можете повысить или понизить тарифный план в любое
                    время. Изменения вступят в силу в следующем биллинговом
                    периоде.
                  </p>
                </CardBody>
              </Card>

              <Card>
                <CardBody>
                  <h3 className="font-semibold text-gray-900 mb-2">
                    Безопасны ли платежи?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Все платежи обрабатываются через Stripe - надежную платежную
                    систему. Мы не храним данные ваших карт.
                  </p>
                </CardBody>
              </Card>

              <Card>
                <CardBody>
                  <h3 className="font-semibold text-gray-900 mb-2">
                    Есть ли возврат средств?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Мы предлагаем полный возврат средств в течение 7 дней после
                    покупки, если вы не удовлетворены сервисом.
                  </p>
                </CardBody>
              </Card>
            </div>
          </div>
        </div>
      </DashboardLayout>
    </>
  );
}


