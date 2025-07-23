import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import {
  MoreVertical,
  Play,
  Pause,
  Trash2,
  Settings,
  RefreshCw,
  Eye,
  EyeOff,
  AlertTriangle,
} from 'lucide-react';
import { ChannelStatus } from './StatusBadge';

interface Channel {
  id: string;
  name: string;
  status: ChannelStatus;
  url: string;
}

interface ChannelActionsProps {
  channel: Channel;
  onActivate?: (channelId: string) => Promise<void>;
  onDeactivate?: (channelId: string) => Promise<void>;
  onDelete?: (channelId: string) => Promise<void>;
  onRefresh?: (channelId: string) => Promise<void>;
  onEdit?: (channelId: string) => void;
  onView?: (channelId: string) => void;
  disabled?: boolean;
}

type ActionType = 'delete' | 'deactivate' | null;

export const ChannelActions: React.FC<ChannelActionsProps> = ({
  channel,
  onActivate,
  onDeactivate,
  onDelete,
  onRefresh,
  onEdit,
  onView,
  disabled = false,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [confirmAction, setConfirmAction] = useState<ActionType>(null);

  const handleAction = async (action: () => Promise<void>) => {
    setIsLoading(true);
    try {
      await action();
    } catch (error) {
      console.error('Action failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmAction = async () => {
    if (confirmAction === 'delete' && onDelete) {
      await handleAction(() => onDelete(channel.id));
    } else if (confirmAction === 'deactivate' && onDeactivate) {
      await handleAction(() => onDeactivate(channel.id));
    }
    setConfirmAction(null);
  };

  const canActivate = ['inactive', 'paused', 'error', 'failed'].includes(channel.status);
  const canDeactivate = ['active', 'processing'].includes(channel.status);
  const canRefresh = ['error', 'failed'].includes(channel.status);

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            disabled={disabled || isLoading}
          >
            <MoreVertical className="h-4 w-4" />
            <span className="sr-only">Открыть меню</span>
          </Button>
        </DropdownMenuTrigger>
        
        <DropdownMenuContent align="end" className="w-48">
          {/* Просмотр канала */}
          {onView && (
            <DropdownMenuItem onClick={() => onView(channel.id)}>
              <Eye className="mr-2 h-4 w-4" />
              Просмотреть
            </DropdownMenuItem>
          )}

          {/* Редактирование */}
          {onEdit && (
            <DropdownMenuItem onClick={() => onEdit(channel.id)}>
              <Settings className="mr-2 h-4 w-4" />
              Редактировать
            </DropdownMenuItem>
          )}

          <DropdownMenuSeparator />

          {/* Активация */}
          {canActivate && onActivate && (
            <DropdownMenuItem
              onClick={() => handleAction(() => onActivate(channel.id))}
              disabled={isLoading}
            >
              <Play className="mr-2 h-4 w-4" />
              Активировать
            </DropdownMenuItem>
          )}

          {/* Деактивация */}
          {canDeactivate && onDeactivate && (
            <DropdownMenuItem
              onClick={() => setConfirmAction('deactivate')}
              disabled={isLoading}
            >
              <Pause className="mr-2 h-4 w-4" />
              Приостановить
            </DropdownMenuItem>
          )}

          {/* Обновление */}
          {canRefresh && onRefresh && (
            <DropdownMenuItem
              onClick={() => handleAction(() => onRefresh(channel.id))}
              disabled={isLoading}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Повторить попытку
            </DropdownMenuItem>
          )}

          <DropdownMenuSeparator />

          {/* Удаление */}
          {onDelete && (
            <DropdownMenuItem
              onClick={() => setConfirmAction('delete')}
              disabled={isLoading}
              className="text-red-600 focus:text-red-600"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Удалить
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Диалог подтверждения удаления */}
      <AlertDialog open={confirmAction === 'delete'} onOpenChange={() => setConfirmAction(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <span>Удалить канал?</span>
            </AlertDialogTitle>
            <AlertDialogDescription>
              Вы уверены, что хотите удалить канал <strong>"{channel.name}"</strong>?
              <br />
              <br />
              Это действие нельзя отменить. Все данные о сигналах и статистике канала будут удалены.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmAction}
              className="bg-red-600 hover:bg-red-700"
            >
              Удалить канал
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Диалог подтверждения деактивации */}
      <AlertDialog open={confirmAction === 'deactivate'} onOpenChange={() => setConfirmAction(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Приостановить канал?</AlertDialogTitle>
            <AlertDialogDescription>
              Вы уверены, что хотите приостановить мониторинг канала <strong>"{channel.name}"</strong>?
              <br />
              <br />
              Канал перестанет отслеживаться, но все данные сохранятся. Вы сможете возобновить мониторинг в любое время.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmAction}>
              Приостановить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

// Компонент для быстрых действий (без dropdown)
interface QuickActionsProps {
  channel: Channel;
  onActivate?: (channelId: string) => Promise<void>;
  onDeactivate?: (channelId: string) => Promise<void>;
  onRefresh?: (channelId: string) => Promise<void>;
  disabled?: boolean;
}

export const QuickActions: React.FC<QuickActionsProps> = ({
  channel,
  onActivate,
  onDeactivate,
  onRefresh,
  disabled = false,
}) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleAction = async (action: () => Promise<void>) => {
    setIsLoading(true);
    try {
      await action();
    } catch (error) {
      console.error('Action failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const canActivate = ['inactive', 'paused', 'error', 'failed'].includes(channel.status);
  const canDeactivate = ['active', 'processing'].includes(channel.status);
  const canRefresh = ['error', 'failed'].includes(channel.status);

  return (
    <div className="flex items-center space-x-1">
      {/* Активация/Деактивация */}
      {canActivate && onActivate && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleAction(() => onActivate(channel.id))}
          disabled={disabled || isLoading}
        >
          <Play className="h-4 w-4 mr-1" />
          Активировать
        </Button>
      )}

      {canDeactivate && onDeactivate && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleAction(() => onDeactivate(channel.id))}
          disabled={disabled || isLoading}
        >
          <Pause className="h-4 w-4 mr-1" />
          Приостановить
        </Button>
      )}

      {/* Обновление */}
      {canRefresh && onRefresh && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleAction(() => onRefresh(channel.id))}
          disabled={disabled || isLoading}
        >
          <RefreshCw className="h-4 w-4 mr-1" />
          Повторить
        </Button>
      )}
    </div>
  );
};

