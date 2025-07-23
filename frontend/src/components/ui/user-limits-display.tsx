import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Crown,
  Users,
  BarChart3,
  Zap,
  AlertTriangle,
  ArrowUpRight,
} from 'lucide-react';
import { UserLimits } from '@/hooks/useUserLimits';

interface UserLimitsDisplayProps {
  limits: UserLimits;
  onUpgradeClick: () => void;
  showUpgradeButton?: boolean;
}

export function UserLimitsDisplay({
  limits,
  onUpgradeClick,
  showUpgradeButton = true,
}: UserLimitsDisplayProps) {
  const getProgressColor = (used: number, limit: number) => {
    if (limit === -1) return 'bg-green-500'; // Unlimited
    const percentage = (used / limit) * 100;
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  const getProgressPercentage = (used: number, limit: number) => {
    if (limit === -1) return 0; // Don't show progress for unlimited
    return Math.min((used / limit) * 100, 100);
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Crown className="h-5 w-5 text-yellow-600" />
            Тариф {limits.plan.name}
          </CardTitle>
          <Badge
            variant={limits.plan.name === 'Free' ? 'secondary' : 'default'}
            className={
              limits.plan.name === 'Free'
                ? 'bg-gray-100 text-gray-700'
                : limits.plan.name === 'Premium'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-purple-100 text-purple-700'
            }
          >
            {limits.plan.name}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Лимит каналов */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-gray-600" />
              <span>Отслеживаемые каналы</span>
            </div>
            <span className="font-medium">
              {limits.channelsUsed}
              {limits.channelsLimit === -1
                ? ' / ∞'
                : ` / ${limits.channelsLimit}`}
            </span>
          </div>
          {limits.channelsLimit !== -1 && (
            <div className="space-y-1">
              <Progress
                value={getProgressPercentage(
                  limits.channelsUsed,
                  limits.channelsLimit
                )}
                className="h-2"
              />
              {!limits.canAddChannel && (
                <div className="flex items-center gap-1 text-xs text-red-600">
                  <AlertTriangle className="h-3 w-3" />
                  <span>Лимит достигнут</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Лимит рейтингов */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-gray-600" />
              <span>Просмотр рейтингов</span>
            </div>
            <span className="font-medium">
              {limits.ratingsViewed}
              {limits.ratingsLimit === -1
                ? ' / ∞'
                : ` / ${limits.ratingsLimit}`}
            </span>
          </div>
          {limits.ratingsLimit !== -1 && (
            <div className="space-y-1">
              <Progress
                value={getProgressPercentage(
                  limits.ratingsViewed,
                  limits.ratingsLimit
                )}
                className="h-2"
              />
              {!limits.canViewMoreRatings && (
                <div className="flex items-center gap-1 text-xs text-red-600">
                  <AlertTriangle className="h-3 w-3" />
                  <span>Лимит достигнут</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Доступные функции */}
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-700">
            Доступные функции:
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Антирейтинг</span>
            </div>
            <div className="flex items-center gap-1">
              <div
                className={`w-2 h-2 rounded-full ${limits.plan.hasAdvancedAnalytics ? 'bg-green-500' : 'bg-gray-300'}`}
              ></div>
              <span
                className={
                  limits.plan.hasAdvancedAnalytics ? '' : 'text-gray-400'
                }
              >
                ML-аналитика
              </span>
            </div>
            <div className="flex items-center gap-1">
              <div
                className={`w-2 h-2 rounded-full ${limits.plan.hasAPIAccess ? 'bg-green-500' : 'bg-gray-300'}`}
              ></div>
              <span className={limits.plan.hasAPIAccess ? '' : 'text-gray-400'}>
                API доступ
              </span>
            </div>
          </div>
        </div>

        {/* Кнопка обновления */}
        {showUpgradeButton && limits.plan.name === 'Free' && (
          <Button
            onClick={onUpgradeClick}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            size="sm"
          >
            <Zap className="h-4 w-4 mr-2" />
            Обновить план
            <ArrowUpRight className="h-4 w-4 ml-2" />
          </Button>
        )}

        {limits.plan.name !== 'Free' && (
          <div className="text-center text-xs text-gray-500">
            💎 Спасибо за использование {limits.plan.name} тарифа!
          </div>
        )}
      </CardContent>
    </Card>
  );
}


