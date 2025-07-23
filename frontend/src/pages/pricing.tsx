import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Check, Star, Zap, Crown } from 'lucide-react';
import StripeProvider from '@/components/stripe/StripeProvider';
import CheckoutForm from '@/components/stripe/CheckoutForm';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface PricingPlan {
  id: string;
  name: string;
  price: number;
  yearlyPrice: number;
  description: string;
  features: string[];
  popular?: boolean;
  icon: React.ReactNode;
  stripePriceId: string;
  stripeYearlyPriceId: string;
}

const plans: PricingPlan[] = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    yearlyPrice: 0,
    description: 'Для знакомства с платформой',
    features: [
      'До 3 каналов для отслеживания',
      'Просмотр топ-10 рейтинга',
      'Полный доступ к антирейтингу',
      'Базовая аналитика',
      'Уведомления в веб-интерфейсе',
    ],
    icon: <Star className="h-6 w-6" />,
    stripePriceId: '',
    stripeYearlyPriceId: '',
  },
  {
    id: 'premium',
    name: 'Premium',
    price: 29,
    yearlyPrice: 290,
    description: 'Для активных трейдеров',
    features: [
      'Безлимитное количество каналов',
      'Полный доступ ко всем рейтингам',
      'Excel/CSV экспорт данных',
      'Email уведомления о сигналах',
      'Расширенная аналитика',
      'Приоритетная поддержка',
    ],
    popular: true,
    icon: <Zap className="h-6 w-6" />,
    stripePriceId: 'price_premium_monthly',
    stripeYearlyPriceId: 'price_premium_yearly',
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 99,
    yearlyPrice: 990,
    description: 'Для профессиональных трейдеров',
    features: [
      'Все функции Premium',
      'API доступ с персональными ключами',
      'Продвинутые ML прогнозы',
      'Кастомные алерты и webhook уведомления',
      'Белый лейбл решения',
      'Персональный менеджер',
    ],
    icon: <Crown className="h-6 w-6" />,
    stripePriceId: 'price_pro_monthly',
    stripeYearlyPriceId: 'price_pro_yearly',
  },
];

export default function PricingPage() {
  const router = useRouter();
  const [isYearly, setIsYearly] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<PricingPlan | null>(null);
  const [showCheckout, setShowCheckout] = useState(false);

  const handleSelectPlan = (plan: PricingPlan) => {
    if (plan.id === 'free') {
      // Для бесплатного плана просто редиректим на регистрацию
      router.push('/auth/register');
      return;
    }

    setSelectedPlan(plan);
    setShowCheckout(true);
  };

  const handleCheckoutSuccess = () => {
    setShowCheckout(false);
    router.push('/dashboard?success=subscription');
  };

  const handleCheckoutError = (error: string) => {
    console.error('Checkout error:', error);
    // Можно показать toast уведомление
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Выберите свой тарифный план
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Получите доступ к профессиональной аналитике криптовалютных сигналов
          </p>

          {/* Переключатель месяц/год */}
          <div className="flex items-center justify-center gap-4 mb-8">
            <span
              className={`text-sm ${!isYearly ? 'font-semibold' : 'text-gray-500'}`}
            >
              Ежемесячно
            </span>
            <button
              onClick={() => setIsYearly(!isYearly)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                isYearly ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  isYearly ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span
              className={`text-sm ${isYearly ? 'font-semibold' : 'text-gray-500'}`}
            >
              Ежегодно
            </span>
            {isYearly && (
              <Badge variant="secondary" className="ml-2">
                Скидка 17%
              </Badge>
            )}
          </div>
        </div>

        {/* Планы */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map(plan => (
            <Card
              key={plan.id}
              className={`relative ${
                plan.popular
                  ? 'border-blue-500 shadow-lg scale-105'
                  : 'border-gray-200'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <Badge className="bg-blue-500 text-white">Популярный</Badge>
                </div>
              )}

              <CardHeader className="text-center">
                <div className="flex justify-center mb-4">
                  <div
                    className={`p-3 rounded-full ${
                      plan.popular
                        ? 'bg-blue-100 text-blue-600'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {plan.icon}
                  </div>
                </div>
                <CardTitle className="text-2xl">{plan.name}</CardTitle>
                <p className="text-gray-600">{plan.description}</p>
                <div className="mt-4">
                  <span className="text-4xl font-bold">
                    ${isYearly ? Math.round(plan.yearlyPrice / 12) : plan.price}
                  </span>
                  <span className="text-gray-600">/мес</span>
                  {isYearly && plan.price > 0 && (
                    <div className="text-sm text-gray-500">
                      ${plan.yearlyPrice} в год
                    </div>
                  )}
                </div>
              </CardHeader>

              <CardContent>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <Check className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-600">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Button
                  onClick={() => handleSelectPlan(plan)}
                  className={`w-full ${
                    plan.popular
                      ? 'bg-blue-600 hover:bg-blue-700'
                      : plan.id === 'free'
                        ? 'bg-gray-600 hover:bg-gray-700'
                        : 'bg-indigo-600 hover:bg-indigo-700'
                  }`}
                >
                  {plan.id === 'free' ? 'Начать бесплатно' : 'Выбрать план'}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* FAQ */}
        <div className="mt-20 max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">
            Часто задаваемые вопросы
          </h2>
          <div className="space-y-8">
            <div>
              <h3 className="text-lg font-semibold mb-2">
                Можно ли отменить подписку в любое время?
              </h3>
              <p className="text-gray-600">
                Да, вы можете отменить подписку в любое время через настройки
                аккаунта. Доступ к премиум функциям сохранится до конца
                оплаченного периода.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-2">
                Безопасны ли мои платежные данные?
              </h3>
              <p className="text-gray-600">
                Мы используем Stripe для обработки платежей - одну из самых
                безопасных платежных систем в мире. Ваши данные карты не
                хранятся на наших серверах.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-2">
                Есть ли скидка при годовой оплате?
              </h3>
              <p className="text-gray-600">
                Да, при выборе годовой подписки вы получаете скидку 17% по
                сравнению с ежемесячными платежами.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Stripe Checkout Modal */}
      <Dialog open={showCheckout} onOpenChange={setShowCheckout}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Оформление подписки</DialogTitle>
          </DialogHeader>
          {selectedPlan && (
            <StripeProvider>
              <CheckoutForm
                planName={selectedPlan.name}
                planPrice={
                  isYearly
                    ? Math.round(selectedPlan.yearlyPrice / 12)
                    : selectedPlan.price
                }
                planFeatures={selectedPlan.features}
                onSuccess={handleCheckoutSuccess}
                onError={handleCheckoutError}
              />
            </StripeProvider>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}


