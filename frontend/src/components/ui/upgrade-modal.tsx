import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Crown,
  Star,
  Zap,
  Check,
  X,
  TrendingUp,
  BarChart3,
  Shield,
  Infinity,
} from 'lucide-react';
import { PLANS, UserPlan } from '@/hooks/useUserLimits';

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPlan: UserPlan;
  limitType: 'channels' | 'ratings' | 'analytics' | 'api';
  title?: string;
  description?: string;
}

export function UpgradeModal({
  isOpen,
  onClose,
  currentPlan,
  limitType,
  title,
  description,
}: UpgradeModalProps) {
  const [selectedPlan, setSelectedPlan] = useState<string>('Premium');

  const getLimitMessage = () => {
    switch (limitType) {
      case 'channels':
        return {
          title: title || 'Лимит каналов достигнут',
          description:
            description ||
            `Вы достигли лимита в ${currentPlan.channelsLimit} каналов для тарифа ${currentPlan.name}. Обновите план для добавления большего количества каналов.`,
          icon: <BarChart3 className="h-12 w-12 text-blue-600" />,
        };
      case 'ratings':
        return {
          title: title || 'Лимит просмотра рейтингов',
          description:
            description ||
            `Вы можете просматривать только топ-${currentPlan.ratingsLimit} каналов в тарифе ${currentPlan.name}. Обновите план для полного доступа.`,
          icon: <TrendingUp className="h-12 w-12 text-green-600" />,
        };
      case 'analytics':
        return {
          title: title || 'Расширенная аналитика недоступна',
          description:
            description ||
            'Детальная аналитика и ML-прогнозы доступны только в Premium и Pro тарифах.',
          icon: <Zap className="h-12 w-12 text-purple-600" />,
        };
      case 'api':
        return {
          title: title || 'API доступ недоступен',
          description:
            description ||
            'API доступ для интеграции с внешними системами доступен только в Pro тарифе.',
          icon: <Shield className="h-12 w-12 text-red-600" />,
        };
      default:
        return {
          title: 'Обновите план',
          description:
            'Получите больше возможностей с Premium или Pro тарифом.',
          icon: <Crown className="h-12 w-12 text-yellow-600" />,
        };
    }
  };

  const limitMessage = getLimitMessage();

  const planCards = Object.values(PLANS)
    .filter(plan => plan.name !== 'Free')
    .map(plan => (
      <Card
        key={plan.name}
        className={`cursor-pointer transition-all duration-200 ${
          selectedPlan === plan.name
            ? 'ring-2 ring-blue-500 border-blue-500'
            : 'hover:border-gray-300'
        }`}
        onClick={() => setSelectedPlan(plan.name)}
      >
        <CardHeader className="text-center pb-4">
          <div className="flex items-center justify-center mb-2">
            {plan.name === 'Premium' ? (
              <Star className="h-8 w-8 text-blue-600" />
            ) : (
              <Crown className="h-8 w-8 text-purple-600" />
            )}
          </div>
          <CardTitle className="text-xl">{plan.name}</CardTitle>
          <div className="text-3xl font-bold">
            {plan.price}₽
            <span className="text-sm font-normal text-gray-500">/месяц</span>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Check className="h-4 w-4 text-green-600" />
              <span className="text-sm">
                {plan.channelsLimit === -1
                  ? 'Неограниченно'
                  : plan.channelsLimit}{' '}
                каналов
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Check className="h-4 w-4 text-green-600" />
              <span className="text-sm">
                {plan.ratingsLimit === -1
                  ? 'Полный'
                  : `Топ-${plan.ratingsLimit}`}{' '}
                рейтинг
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Check className="h-4 w-4 text-green-600" />
              <span className="text-sm">Антирейтинг худших каналов</span>
            </div>
            {plan.hasAdvancedAnalytics ? (
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-600" />
                <span className="text-sm">Расширенная ML-аналитика</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <X className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-400">
                  Расширенная ML-аналитика
                </span>
              </div>
            )}
            {plan.hasAPIAccess ? (
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-600" />
                <span className="text-sm">API доступ</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <X className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-400">API доступ</span>
              </div>
            )}
          </div>
          {selectedPlan === plan.name && (
            <Badge className="w-full justify-center bg-blue-600">Выбрано</Badge>
          )}
        </CardContent>
      </Card>
    ));

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader className="text-center">
          <div className="flex justify-center mb-4">{limitMessage.icon}</div>
          <DialogTitle className="text-2xl">{limitMessage.title}</DialogTitle>
          <DialogDescription className="text-lg">
            {limitMessage.description}
          </DialogDescription>
        </DialogHeader>

        <div className="grid md:grid-cols-2 gap-6 mt-6">{planCards}</div>

        <div className="flex gap-4 mt-6">
          <Button variant="outline" onClick={onClose} className="flex-1">
            Остаться на Free
          </Button>
          <Button
            onClick={() => {
              // В реальном приложении здесь будет редирект на страницу оплаты
              console.log('Upgrading to:', selectedPlan);
              onClose();
            }}
            className="flex-1 bg-blue-600 hover:bg-blue-700"
          >
            Обновить до {selectedPlan}
          </Button>
        </div>

        <div className="text-center text-sm text-gray-500 mt-4">
          💳 Безопасная оплата через Stripe • 🔄 Отмена в любое время
        </div>
      </DialogContent>
    </Dialog>
  );
}


