import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Channel } from '@/types';

interface ChannelActionsProps {
  channel: Channel;
  onDelete?: (channelId: string) => Promise<void>;
  onActivate?: (channelId: string) => Promise<void>;
  onDeactivate?: (channelId: string) => Promise<void>;
}

export function ChannelActions({ 
  channel, 
  onDelete, 
  onActivate, 
  onDeactivate 
}: ChannelActionsProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'delete' | 'activate' | 'deactivate' | null>(null);

  const handleAction = async () => {
    try {
      switch (actionType) {
        case 'delete':
          await onDelete?.(channel.id);
          break;
        case 'activate':
          await onActivate?.(channel.id);
          break;
        case 'deactivate':
          await onDeactivate?.(channel.id);
          break;
      }
      setIsDialogOpen(false);
    } catch (error) {
      console.error(`Error performing ${actionType} action:`, error);
    }
  };

  return (
    <div className="flex space-x-2">
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogTrigger asChild>
          <Button 
            variant="destructive" 
            size="sm" 
            onClick={() => {
              setActionType('delete');
              setIsDialogOpen(true);
            }}
          >
            Удалить
          </Button>
        </DialogTrigger>
        
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Подтвердите действие</DialogTitle>
            <DialogDescription>
              {actionType === 'delete' && 'Вы уверены, что хотите удалить этот канал?'}
              {actionType === 'activate' && 'Вы уверены, что хотите активировать этот канал?'}
              {actionType === 'deactivate' && 'Вы уверены, что хотите деактивировать этот канал?'}
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex justify-end space-x-2">
            <Button 
              variant="outline" 
              onClick={() => setIsDialogOpen(false)}
            >
              Отмена
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleAction}
            >
              Подтвердить
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {channel.status === 'inactive' && (
        <Button 
          variant="default" 
          size="sm" 
          onClick={() => {
            setActionType('activate');
            setIsDialogOpen(true);
          }}
        >
          Активировать
        </Button>
      )}

      {channel.status === 'active' && (
        <Button 
          variant="secondary" 
          size="sm" 
          onClick={() => {
            setActionType('deactivate');
            setIsDialogOpen(true);
          }}
        >
          Деактивировать
        </Button>
      )}
    </div>
  );
}

