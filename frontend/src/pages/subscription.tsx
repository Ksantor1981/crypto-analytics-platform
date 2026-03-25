import { useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { CheckCircle, Zap, Crown, Star, Loader2 } from 'lucide-react';

import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';

const plans = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    period: 'навсегда',
    icon: Star,
    color: 'gray',
    features: [
      'До 3 каналов',
      'Базовая аналитика',
      'Антирейтинг (топ-3)',
      'Email поддержка',
    ],
  },
  {
    id: 'premium',
    name: 'Premium',
    price: 19,
    period: '/мес',
    icon: Zap,
    color: 'blue',
    popular: true,
    features: [
      'До 15 каналов',
      'Полная аналитика',
      'Excel экспорт',
      'Расширенные фильтры',
      'Push уведомления',
      'Приоритетная поддержка',
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 49,
    period: '/мес',
    icon: Crown,
    color: 'purple',
    features: [
      'Безлимит каналов',
      'ML предсказания',
      'API доступ',
      'Кастомные алерты',
      'VIP поддержка',
      'Персональный менеджер',
    ],
  },
];

export default function SubscriptionPage() {
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  /** Только для авторизованных; гость не считается «на Free» — кнопка Free ведёт в регистрацию */
  const currentPlan = isAuthenticated
    ? user?.subscription?.plan?.toLowerCase() || 'free'
    : null;
  const success = router.query.success === 'true';
  const cancelled = router.query.cancelled === 'true';

  const handleSelectPlan = async (planId: string) => {
    if (planId === 'free') {
      if (!isAuthenticated) void router.push('/auth/register');
      return;
    }
    if (currentPlan != null && planId === currentPlan) return;
    if (!isAuthenticated) {
      void router.push('/auth/login');
      return;
    }
    setLoading(true);
    setSelectedPlan(planId);
    try {
      const token = localStorage.getItem('access_token');
      const resp = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/stripe/create-checkout`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            plan: planId,
            success_url: `${window.location.origin}/subscription?success=true`,
            cancel_url: `${window.location.origin}/subscription?cancelled=true`,
          }),
        }
      );
      const data = await resp.json();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        alert(data.detail || 'Ошибка создания сессии оплаты');
      }
    } catch {
      alert('Ошибка подключения к серверу');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Подписки - CryptoAnalytics</title>
      </Head>
      <div className="max-w-5xl mx-auto px-4 py-8">
        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800 text-center">
            <CheckCircle className="h-5 w-5 inline mr-2" />
            Подписка успешно оформлена! Спасибо за покупку.
          </div>
        )}
        {cancelled && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 text-center">
            Оформление подписки отменено. Вы можете попробовать позже.
          </div>
        )}
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Тарифные планы
          </h1>
          <p className="text-gray-600">
            Выберите план, который подходит для ваших задач
          </p>
          <p className="text-sm text-blue-600 mt-2">
            Текущий план:{' '}
            <span className="font-semibold capitalize">
              {!isAuthenticated
                ? '— войдите, чтобы увидеть'
                : currentPlan || 'free'}
            </span>
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map(plan => {
            const Icon = plan.icon;
            const isCurrent = currentPlan != null && currentPlan === plan.id;
            return (
              <Card
                key={plan.id}
                className={`relative flex flex-col ${plan.popular ? 'border-2 border-blue-500 shadow-lg' : 'border'}`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-500 text-white text-xs font-semibold px-4 py-1 rounded-full">
                    Популярный
                  </div>
                )}
                <CardHeader className="text-center pb-2">
                  <Icon
                    className={`h-8 w-8 mx-auto mb-2 text-${plan.color}-500`}
                  />
                  <CardTitle className="text-xl">{plan.name}</CardTitle>
                  <div className="mt-2">
                    <span className="text-4xl font-bold">${plan.price}</span>
                    <span className="text-gray-500 text-sm">{plan.period}</span>
                  </div>
                </CardHeader>
                <CardContent className="flex-grow">
                  <ul className="space-y-3">
                    {plan.features.map((f, i) => (
                      <li
                        key={i}
                        className="flex items-center text-sm text-gray-700"
                      >
                        <CheckCircle className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                </CardContent>
                <div className="p-4 pt-0 mt-auto">
                  <Button
                    className={`w-full ${isCurrent ? 'bg-gray-200 text-gray-600' : plan.popular ? 'bg-blue-600 hover:bg-blue-700 text-white' : ''}`}
                    variant={plan.popular ? 'default' : 'outline'}
                    disabled={
                      isCurrent || (loading && selectedPlan === plan.id)
                    }
                    onClick={() => handleSelectPlan(plan.id)}
                  >
                    {loading && selectedPlan === plan.id ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Переход к оплате...
                      </>
                    ) : isCurrent ? (
                      'Текущий план'
                    ) : plan.price === 0 ? (
                      'Начать бесплатно'
                    ) : (
                      'Оформить подписку'
                    )}
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>

        <div className="mt-10 text-center text-sm text-gray-500">
          <p>Все платные планы включают 7-дневный бесплатный пробный период.</p>
          <p className="mt-1">Отмена подписки возможна в любое время.</p>
        </div>
      </div>
    </>
  );
}
