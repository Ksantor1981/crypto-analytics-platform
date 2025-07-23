import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  CreditCard,
  Calendar,
  Download,
  Settings,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from 'lucide-react';

interface Subscription {
  id: string;
  plan: 'free' | 'premium' | 'pro';
  status: 'active' | 'cancelled' | 'past_due' | 'trialing';
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  stripe_subscription_id?: string;
}

interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: 'paid' | 'pending' | 'failed';
  created: string;
  invoice_pdf?: string;
}

export const SubscriptionManager: React.FC = () => {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    fetchSubscriptionData();
  }, []);

  const fetchSubscriptionData = async () => {
    try {
      setLoading(true);

      // Получаем данные подписки
      const subResponse = await fetch('/api/subscriptions/me', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (subResponse.ok) {
        const subData = await subResponse.json();
        setSubscription(subData);
      }

      // Получаем историю платежей
      const invoicesResponse = await fetch('/api/payments/me', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (invoicesResponse.ok) {
        const invoicesData = await invoicesResponse.json();
        setInvoices(invoicesData.items || []);
      }
    } catch (error) {
      console.error('Error fetching subscription data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (
      !subscription ||
      !confirm('Вы уверены, что хотите отменить подписку?')
    ) {
      return;
    }

    try {
      setActionLoading(true);

      const response = await fetch('/api/subscriptions/me/cancel', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          reason: 'user_requested',
        }),
      });

      if (response.ok) {
        await fetchSubscriptionData();
        alert(
          'Подписка отменена. Доступ к премиум функциям сохранится до конца текущего периода.'
        );
      } else {
        throw new Error('Failed to cancel subscription');
      }
    } catch (error) {
      console.error('Error canceling subscription:', error);
      alert('Ошибка при отмене подписки. Попробуйте позже.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReactivateSubscription = async () => {
    if (!subscription) return;

    try {
      setActionLoading(true);

      const response = await fetch('/api/subscriptions/me/reactivate', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        await fetchSubscriptionData();
        alert('Подписка возобновлена!');
      } else {
        throw new Error('Failed to reactivate subscription');
      }
    } catch (error) {
      console.error('Error reactivating subscription:', error);
      alert('Ошибка при возобновлении подписки. Попробуйте позже.');
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-100 text-green-800">Активна</Badge>;
      case 'cancelled':
        return <Badge className="bg-red-100 text-red-800">Отменена</Badge>;
      case 'past_due':
        return (
          <Badge className="bg-yellow-100 text-yellow-800">Просрочена</Badge>
        );
      case 'trialing':
        return (
          <Badge className="bg-blue-100 text-blue-800">Пробный период</Badge>
        );
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getPlanName = (plan: string) => {
    switch (plan) {
      case 'premium':
        return 'Premium';
      case 'pro':
        return 'Pro';
      default:
        return 'Free';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Текущая подписка */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Текущая подписка
          </CardTitle>
        </CardHeader>
        <CardContent>
          {subscription ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold">
                    {getPlanName(subscription.plan)}
                  </h3>
                  <p className="text-gray-600">
                    {subscription.plan === 'free'
                      ? 'Бесплатный план'
                      : `Активна до ${new Date(subscription.current_period_end).toLocaleDateString()}`}
                  </p>
                </div>
                {getStatusBadge(subscription.status)}
              </div>

              {subscription.plan !== 'free' && (
                <>
                  {subscription.cancel_at_period_end && (
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        Подписка будет отменена{' '}
                        {new Date(
                          subscription.current_period_end
                        ).toLocaleDateString()}
                        . Вы можете возобновить её в любое время до этой даты.
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className="flex gap-2">
                    {subscription.cancel_at_period_end ? (
                      <Button
                        onClick={handleReactivateSubscription}
                        disabled={actionLoading}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        <CheckCircle className="mr-2 h-4 w-4" />
                        Возобновить подписку
                      </Button>
                    ) : (
                      <Button
                        onClick={handleCancelSubscription}
                        disabled={actionLoading}
                        variant="destructive"
                      >
                        <XCircle className="mr-2 h-4 w-4" />
                        Отменить подписку
                      </Button>
                    )}

                    <Button variant="outline">
                      <Settings className="mr-2 h-4 w-4" />
                      Изменить план
                    </Button>
                  </div>
                </>
              )}

              {subscription.plan === 'free' && (
                <div className="pt-4">
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    Обновить до Premium
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">У вас нет активной подписки</p>
              <Button className="bg-blue-600 hover:bg-blue-700">
                Выбрать план
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* История платежей */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            История платежей
          </CardTitle>
        </CardHeader>
        <CardContent>
          {invoices.length > 0 ? (
            <div className="space-y-3">
              {invoices.map(invoice => (
                <div
                  key={invoice.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div>
                    <p className="font-medium">
                      ${invoice.amount} {invoice.currency.toUpperCase()}
                    </p>
                    <p className="text-sm text-gray-600">
                      {new Date(invoice.created).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(invoice.status)}
                    {invoice.invoice_pdf && (
                      <Button size="sm" variant="outline">
                        <Download className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600 text-center py-8">
              История платежей пуста
            </p>
          )}
        </CardContent>
      </Card>

      {/* Информация о безопасности */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              Защищено SSL
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              Обработка через Stripe
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              Отмена в любое время
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SubscriptionManager;


