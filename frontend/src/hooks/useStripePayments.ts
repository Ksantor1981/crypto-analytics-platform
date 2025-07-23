import { useState, useCallback } from 'react';

interface PaymentIntentData {
  amount: number;
  currency: string;
  plan_name: string;
  stripe_price_id?: string;
}

interface PaymentIntentResponse {
  client_secret: string;
  payment_intent_id: string;
}

interface SubscriptionData {
  price_id: string;
  success_url?: string;
  cancel_url?: string;
}

interface CheckoutSessionResponse {
  checkout_url: string;
  session_id: string;
}

export const useStripePayments = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createPaymentIntent = useCallback(
    async (data: PaymentIntentData): Promise<PaymentIntentResponse | null> => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch('/api/payments/create-payment-intent', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || 'Failed to create payment intent'
          );
        }

        const result = await response.json();
        return result;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Payment failed';
        setError(errorMessage);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const createCheckoutSession = useCallback(
    async (data: SubscriptionData): Promise<CheckoutSessionResponse | null> => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch('/api/payments/create-checkout-session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || 'Failed to create checkout session'
          );
        }

        const result = await response.json();
        return result;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Checkout failed';
        setError(errorMessage);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const createCustomerPortalSession = useCallback(async (): Promise<
    string | null
  > => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/payments/customer-portal', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || 'Failed to create customer portal session'
        );
      }

      const result = await response.json();
      return result.url;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Portal access failed';
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const cancelSubscription = useCallback(
    async (reason?: string): Promise<boolean> => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch('/api/subscriptions/me/cancel', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify({ reason: reason || 'user_requested' }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to cancel subscription');
        }

        return true;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Cancellation failed';
        setError(errorMessage);
        return false;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const reactivateSubscription = useCallback(async (): Promise<boolean> => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/subscriptions/me/reactivate', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || 'Failed to reactivate subscription'
        );
      }

      return true;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Reactivation failed';
      setError(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    loading,
    error,
    createPaymentIntent,
    createCheckoutSession,
    createCustomerPortalSession,
    cancelSubscription,
    reactivateSubscription,
    clearError,
  };
};

export default useStripePayments;
