import React, { useState } from 'react';
import { useStripe, useElements, CardElement } from '@stripe/react-stripe-js';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CreditCard, Shield, Check } from 'lucide-react';

interface CheckoutFormProps {
  planName: string;
  planPrice: number;
  planFeatures: string[];
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export const CheckoutForm: React.FC<CheckoutFormProps> = ({
  planName,
  planPrice,
  planFeatures,
  onSuccess,
  onError,
}) => {
  const stripe = useStripe();
  const elements = useElements();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setIsLoading(true);
    setError(null);

    const cardElement = elements.getElement(CardElement);

    if (!cardElement) {
      setError('Card element not found');
      setIsLoading(false);
      return;
    }

    try {
      // Создаем payment intent на backend
      const response = await fetch('/api/payments/create-payment-intent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          amount: planPrice * 100, // Stripe expects cents
          currency: 'usd',
          plan_name: planName,
        }),
      });

      const { client_secret } = await response.json();

      // Подтверждаем платеж
      const { error: stripeError, paymentIntent } =
        await stripe.confirmCardPayment(client_secret, {
          payment_method: {
            card: cardElement,
            billing_details: {
              name: 'Customer Name', // Можно получить из профиля пользователя
            },
          },
        });

      if (stripeError) {
        setError(stripeError.message || 'Payment failed');
        onError?.(stripeError.message || 'Payment failed');
      } else if (paymentIntent?.status === 'succeeded') {
        onSuccess?.();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Payment failed';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const cardElementOptions = {
    style: {
      base: {
        fontSize: '16px',
        color: '#424770',
        '::placeholder': {
          color: '#aab7c4',
        },
      },
      invalid: {
        color: '#9e2146',
      },
    },
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-5 w-5" />
          Оформить подписку {planName}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* План и цена */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex justify-between items-center mb-3">
            <span className="font-medium">{planName}</span>
            <span className="text-2xl font-bold">${planPrice}/мес</span>
          </div>
          <ul className="space-y-1">
            {planFeatures.map((feature, index) => (
              <li
                key={index}
                className="flex items-center gap-2 text-sm text-gray-600"
              >
                <Check className="h-4 w-4 text-green-500" />
                {feature}
              </li>
            ))}
          </ul>
        </div>

        {/* Форма оплаты */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="p-4 border rounded-lg">
            <label className="block text-sm font-medium mb-2">
              Данные карты
            </label>
            <CardElement options={cardElementOptions} />
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button
            type="submit"
            disabled={!stripe || isLoading}
            className="w-full"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Обработка платежа...
              </>
            ) : (
              `Оплатить $${planPrice}`
            )}
          </Button>
        </form>

        {/* Безопасность */}
        <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
          <Shield className="h-4 w-4" />
          Защищено Stripe. Ваши данные в безопасности.
        </div>
      </CardContent>
    </Card>
  );
};

export default CheckoutForm;


