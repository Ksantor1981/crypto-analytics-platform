import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { subscriptionsApi } from '@/lib/api';
import { Subscription } from '@/types';

export const useSubscriptions = () => {
  const queryClient = useQueryClient();

  const {
    data: subscriptions = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['subscriptions'],
    queryFn: () => subscriptionsApi.getUserSubscriptions(),
    select: data => data.data,
  });

  const createSubscriptionMutation = useMutation({
    mutationFn: subscriptionsApi.createSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });

  const cancelSubscriptionMutation = useMutation({
    mutationFn: subscriptionsApi.cancelSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });

  const reactivateSubscriptionMutation = useMutation({
    mutationFn: subscriptionsApi.reactivateSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });

  const createCheckoutSessionMutation = useMutation({
    mutationFn: subscriptionsApi.createCheckoutSession,
    onSuccess: data => {
      // Redirect to Stripe Checkout
      window.location.href = data.checkout_url;
    },
  });

  return {
    subscriptions,
    isLoading,
    error,
    refetch,
    createSubscription: createSubscriptionMutation.mutateAsync,
    cancelSubscription: cancelSubscriptionMutation.mutateAsync,
    reactivateSubscription: reactivateSubscriptionMutation.mutateAsync,
    createCheckoutSession: createCheckoutSessionMutation.mutateAsync,
    isCreating: createSubscriptionMutation.isPending,
    isCancelling: cancelSubscriptionMutation.isPending,
    isReactivating: reactivateSubscriptionMutation.isPending,
    isCreatingCheckout: createCheckoutSessionMutation.isPending,
  };
};

export const useSubscription = (id: string) => {
  const queryClient = useQueryClient();

  const {
    data: subscription,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['subscription', id],
    queryFn: () => subscriptionsApi.getSubscription(id),
    select: data => data.data,
    enabled: !!id,
  });

  const updateSubscriptionMutation = useMutation({
    mutationFn: (data: Partial<Subscription>) =>
      subscriptionsApi.updateSubscription(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscription', id] });
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });

  const cancelSubscriptionMutation = useMutation({
    mutationFn: () => subscriptionsApi.cancelSubscription(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscription', id] });
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });

  return {
    subscription,
    isLoading,
    error,
    updateSubscription: updateSubscriptionMutation.mutateAsync,
    cancelSubscription: cancelSubscriptionMutation.mutateAsync,
    isUpdating: updateSubscriptionMutation.isPending,
    isCancelling: cancelSubscriptionMutation.isPending,
  };
};

export const usePricingPlans = () => {
  const {
    data: plans = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['pricing-plans'],
    queryFn: () => subscriptionsApi.getPricingPlans(),
    select: data => data.data,
  });

  return {
    plans,
    isLoading,
    error,
  };
};
