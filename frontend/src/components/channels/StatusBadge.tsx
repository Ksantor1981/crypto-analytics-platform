import { Badge } from '@/components/ui/badge';
import { 
  CheckCircle, 
  Clock, 
  XCircle, 
  AlertTriangle, 
  Loader2,
  Pause,
  Play
} from 'lucide-react';

export type ChannelStatus = 
  | 'pending'    // Ожидает обработки
  | 'active'     // Активен и работает
  | 'error'      // Ошибка при обработке
  | 'inactive'   // Неактивен/приостановлен
  | 'processing' // В процессе обработки
  | 'failed'     // Не удалось подключиться
  | 'paused';    // Приостановлен пользователем

interface StatusBadgeProps {
  status: ChannelStatus;
  className?: string;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const statusConfig = {
  pending: {
    label: 'Ожидает',
    variant: 'secondary' as const,
    icon: Clock,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50 border-yellow-200',
  },
  active: {
    label: 'Активен',
    variant: 'default' as const,
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
  },
  error: {
    label: 'Ошибка',
    variant: 'destructive' as const,
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50 border-red-200',
  },
  inactive: {
    label: 'Неактивен',
    variant: 'outline' as const,
    icon: AlertTriangle,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50 border-gray-200',
  },
  processing: {
    label: 'Обработка',
    variant: 'secondary' as const,
    icon: Loader2,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 border-blue-200',
  },
  failed: {
    label: 'Не удалось',
    variant: 'destructive' as const,
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50 border-red-200',
  },
  paused: {
    label: 'Приостановлен',
    variant: 'outline' as const,
    icon: Pause,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50 border-orange-200',
  },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  className = '',
  showIcon = true,
  size = 'md',
}) => {
  const config = statusConfig[status];
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5',
  };

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  return (
    <Badge
      variant={config.variant}
      className={`
        inline-flex items-center space-x-1 font-medium
        ${config.bgColor} ${config.color}
        ${sizeClasses[size]}
        ${className}
      `}
    >
      {showIcon && (
        <Icon 
          className={`
            ${iconSizes[size]} 
            ${status === 'processing' ? 'animate-spin' : ''}
          `} 
        />
      )}
      <span>{config.label}</span>
    </Badge>
  );
};

// Компонент для отображения детального статуса с описанием
interface StatusDetailProps {
  status: ChannelStatus;
  message?: string;
  lastUpdated?: string;
  className?: string;
}

export const StatusDetail: React.FC<StatusDetailProps> = ({
  status,
  message,
  lastUpdated,
  className = '',
}) => {
  const config = statusConfig[status];
  const Icon = config.icon;

  const getStatusMessage = (status: ChannelStatus): string => {
    switch (status) {
      case 'pending':
        return 'Канал добавлен в очередь на обработку';
      case 'active':
        return 'Канал активен и отслеживается';
      case 'error':
        return 'Произошла ошибка при обработке канала';
      case 'inactive':
        return 'Канал временно неактивен';
      case 'processing':
        return 'Выполняется анализ канала и настройка мониторинга';
      case 'failed':
        return 'Не удалось подключиться к каналу';
      case 'paused':
        return 'Мониторинг канала приостановлен пользователем';
      default:
        return 'Неизвестный статус';
    }
  };

  return (
    <div className={`flex items-start space-x-3 p-3 rounded-lg ${config.bgColor} ${className}`}>
      <Icon 
        className={`
          h-5 w-5 mt-0.5 ${config.color}
          ${status === 'processing' ? 'animate-spin' : ''}
        `} 
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2">
          <StatusBadge status={status} size="sm" showIcon={false} />
          {lastUpdated && (
            <span className="text-xs text-gray-500">
              {lastUpdated}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-700 mt-1">
          {message || getStatusMessage(status)}
        </p>
      </div>
    </div>
  );
};

// Хук для работы со статусами каналов
export const useChannelStatus = () => {
  const getStatusPriority = (status: ChannelStatus): number => {
    const priorities = {
      error: 1,
      failed: 2,
      processing: 3,
      pending: 4,
      paused: 5,
      inactive: 6,
      active: 7,
    };
    return priorities[status] || 0;
  };

  const isStatusActionable = (status: ChannelStatus): boolean => {
    return ['error', 'failed', 'inactive', 'paused'].includes(status);
  };

  const getNextAction = (status: ChannelStatus): string => {
    switch (status) {
      case 'error':
      case 'failed':
        return 'Повторить попытку';
      case 'inactive':
        return 'Активировать';
      case 'paused':
        return 'Возобновить';
      default:
        return '';
    }
  };

  return {
    getStatusPriority,
    isStatusActionable,
    getNextAction,
  };
};
