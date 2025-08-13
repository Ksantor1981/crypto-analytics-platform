// Неиспользуемые импорты удалены
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { subscriptionsApi } from '@/lib/api/subscriptions';
// import { SubscriptionPlan } from '@/types';

export const useSubscriptions = () => {
  const queryClient = useQueryClient();

  const {
    data: subscriptions = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['subscriptions'],
    queryFn: () => subscriptionsApi.getPlans(),
    // select убрано,
  });

  const createSubscriptionPlanMutation = useMutation({
    mutationFn: subscriptionsApi.createSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });

  const cancelSubscriptionPlanMutation = useMutation({
    mutationFn: subscriptionsApi.cancelSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });

  // Реактивация удалена - метод не существует

  // createCheckoutSession удален - используется createSubscription выше

  return {
    subscriptions,
    isLoading,
    error,
    refetch,
    createSubscription: createSubscriptionPlanMutation.mutateAsync,
    cancelSubscription: cancelSubscriptionPlanMutation.mutateAsync,
    // Реактивация и checkout удалены
    isCreating: createSubscriptionPlanMutation.isLoading,
    isCancelling: cancelSubscriptionPlanMutation.isLoading,
    // isCreatingCheckout удален
  };
};

export const useSubscriptionPlan = (id: string) => {
  const { subscriptions, isLoading, error } = useSubscriptions();
  
  const subscription = subscriptions.find(plan => plan.id === id);

  return {
    subscription,
    isLoading,
    error,
  };
};

export const usePricingPlans = () => {
  // Просто переиспользуем главный хук
  return useSubscriptions();
};
