import { useState, useEffect } from 'react';

import { apiClient } from '@/lib/api';

export interface UserPlan {
  name: 'Free' | 'Premium' | 'Pro';
  channelsLimit: number;
  ratingsLimit: number;
  hasAntiRating: boolean;
  hasAdvancedAnalytics: boolean;
  hasAPIAccess: boolean;
  price: number;
}

export const PLANS: Record<string, UserPlan> = {
  Free: {
    name: 'Free',
    channelsLimit: 3,
    ratingsLimit: 10,
    hasAntiRating: true, // Hook для конверсии
    hasAdvancedAnalytics: false,
    hasAPIAccess: false,
    price: 0,
  },
  Premium: {
    name: 'Premium',
    channelsLimit: 15,
    ratingsLimit: 50,
    hasAntiRating: true,
    hasAdvancedAnalytics: true,
    hasAPIAccess: false,
    price: 990,
  },
  Pro: {
    name: 'Pro',
    channelsLimit: -1, // Unlimited
    ratingsLimit: -1, // Unlimited
    hasAntiRating: true,
    hasAdvancedAnalytics: true,
    hasAPIAccess: true,
    price: 2990,
  },
};

export interface UserLimits {
  channelsUsed: number;
  channelsLimit: number;
  canAddChannel: boolean;
  ratingsViewed: number;
  ratingsLimit: number;
  canViewMoreRatings: boolean;
  plan: UserPlan;
}

export function useUserLimits() {
  const [limits, setLimits] = useState<UserLimits | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchLimits = async () => {
    try {
      const data = await apiClient.getLimits();
      const planKey = data.plan as keyof typeof PLANS;
      const userPlan = planKey in PLANS ? PLANS[planKey] : PLANS.Free;
      setLimits({
        channelsUsed: data.channels_used,
        channelsLimit: data.channels_limit,
        canAddChannel: data.can_add_channel,
        ratingsViewed: data.ratings_viewed,
        ratingsLimit: data.ratings_limit,
        canViewMoreRatings: data.can_view_more_ratings,
        plan: userPlan,
      });
    } catch {
      const userPlan = PLANS.Free;
      setLimits({
        channelsUsed: 0,
        channelsLimit: userPlan.channelsLimit,
        canAddChannel: true,
        ratingsViewed: 0,
        ratingsLimit: userPlan.ratingsLimit,
        canViewMoreRatings: true,
        plan: userPlan,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    void fetchLimits();
  }, []);

  const checkChannelLimit = (): boolean => {
    if (!limits) return false;
    return limits.canAddChannel;
  };

  const checkRatingsLimit = (): boolean => {
    if (!limits) return false;
    return limits.canViewMoreRatings;
  };

  const incrementChannelsUsed = () => {
    if (!limits) return;
    setLimits({
      ...limits,
      channelsUsed: limits.channelsUsed + 1,
      canAddChannel:
        limits.channelsLimit === -1 ||
        limits.channelsUsed + 1 < limits.channelsLimit,
    });
  };

  const incrementRatingsViewed = () => {
    if (!limits) return;
    setLimits({
      ...limits,
      ratingsViewed: limits.ratingsViewed + 1,
      canViewMoreRatings:
        limits.ratingsLimit === -1 ||
        limits.ratingsViewed + 1 < limits.ratingsLimit,
    });
  };

  return {
    limits,
    loading,
    refetch: fetchLimits,
    checkChannelLimit,
    checkRatingsLimit,
    incrementChannelsUsed,
    incrementRatingsViewed,
  };
}
