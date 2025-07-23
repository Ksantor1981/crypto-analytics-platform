import { useState, useEffect } from 'react';

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

  useEffect(() => {
    // В реальном приложении это будет API вызов
    // Пока используем mock данные
    const mockUser = {
      plan: 'Free',
      channelsUsed: 2,
      ratingsViewed: 5,
    };

    const userPlan = PLANS[mockUser.plan];

    setLimits({
      channelsUsed: mockUser.channelsUsed,
      channelsLimit: userPlan.channelsLimit,
      canAddChannel:
        userPlan.channelsLimit === -1 ||
        mockUser.channelsUsed < userPlan.channelsLimit,
      ratingsViewed: mockUser.ratingsViewed,
      ratingsLimit: userPlan.ratingsLimit,
      canViewMoreRatings:
        userPlan.ratingsLimit === -1 ||
        mockUser.ratingsViewed < userPlan.ratingsLimit,
      plan: userPlan,
    });

    setLoading(false);
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
    checkChannelLimit,
    checkRatingsLimit,
    incrementChannelsUsed,
    incrementRatingsViewed,
  };
}
