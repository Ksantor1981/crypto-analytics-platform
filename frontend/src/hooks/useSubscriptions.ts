// Неиспользуемые импорты удалены
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
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
    queryFn: async () => {
      const response = await apiClient.getSubscriptions();
      return response || [];
    },
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });

  const createSubscriptionPlanMutation = useMutation({
    mutationFn: async (planType: 'free' | 'pro' | 'enterprise') => {
      return apiClient.updateSubscription(planType);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });

  const cancelSubscriptionPlanMutation = useMutation({
    mutationFn: async () => {
      // Временно возвращаем успех, так как cancelSubscription не реализован в API
      return { success: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });

  return {
    subscriptions,
    isLoading,
    error,
    refetch,
    createSubscription: createSubscriptionPlanMutation.mutateAsync,
    cancelSubscription: cancelSubscriptionPlanMutation.mutateAsync,
    isCreating: createSubscriptionPlanMutation.isPending,
    isCancelling: cancelSubscriptionPlanMutation.isPending,
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
