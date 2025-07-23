import React, { useEffect, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, MessageSquare, Globe, Hash, Twitter, TrendingUp } from 'lucide-react';
import { ChannelType } from '@/types';

// Channel type configurations
const channelTypeConfigs = {
  telegram: {
    name: 'Telegram',
    icon: MessageSquare,
    urlPattern: /^https:\/\/(t\.me|telegram\.me)\/[a-zA-Z0-9_]+\/?$/,
    urlExample: 'https://t.me/channel_name',
    description: 'Telegram каналы и группы с криптосигналами'
  },
  reddit: {
    name: 'Reddit',
    icon: Globe,
    urlPattern: /^(https:\/\/(www\.)?reddit\.com\/r\/[a-zA-Z0-9_]+\/?|r\/[a-zA-Z0-9_]+|[a-zA-Z0-9_]+)$/,
    urlExample: 'https://reddit.com/r/cryptocurrency или cryptocurrency',
    description: 'Reddit сабреддиты с обсуждениями криптовалют'
  },
  rss: {
    name: 'RSS Feed',
    icon: Hash,
    urlPattern: /^https?:\/\/.+\.(xml|rss|feed)$|^https?:\/\/.+\/(rss|feed)\/?$/,
    urlExample: 'https://cointelegraph.com/rss',
    description: 'RSS ленты новостных сайтов о криптовалютах'
  },
  twitter: {
    name: 'Twitter/X',
    icon: Twitter,
    urlPattern: /^(https:\/\/(twitter\.com|x\.com)\/[a-zA-Z0-9_]+\/?|@[a-zA-Z0-9_]+|[a-zA-Z0-9_]+)$/,
    urlExample: 'https://twitter.com/username или @username',
    description: 'Twitter/X аккаунты криптоинфлюенсеров и трейдеров'
  },
  tradingview: {
    name: 'TradingView',
    icon: TrendingUp,
    urlPattern: /^(https:\/\/www\.tradingview\.com\/(u\/[a-zA-Z0-9_]+|symbols\/[A-Z]+|ideas\/(crypto|forex)?)\/?|[a-zA-Z0-9_]+)$/,
    urlExample: 'https://tradingview.com/u/username или BTCUSD',
    description: 'TradingView идеи и анализ от трейдеров'
  }
};

// Dynamic schema based on channel type
const createChannelSchema = (channelType: ChannelType) => {
  const config = channelTypeConfigs[channelType];
  
  return z.object({
    name: z.string().min(3, { message: 'Название должно содержать минимум 3 символа' }),
    type: z.enum(['telegram', 'reddit', 'rss', 'twitter', 'tradingview'] as const),
    url: z.string().min(1, { message: 'URL обязателен' }).refine(url => {
      if (channelType === 'rss') {
        // For RSS, allow any valid URL
        try {
          new URL(url);
          return true;
        } catch {
          return false;
        }
      }
      return config.urlPattern.test(url);
    }, {
      message: `Введите корректный URL для ${config.name}. Пример: ${config.urlExample}`
    }),
    description: z.string().max(500, { message: 'Описание не должно превышать 500 символов' }).optional(),
    category: z.string().optional(),
    // Parser-specific configs
    bearer_token: z.string().optional(), // For Twitter
    client_id: z.string().optional(), // For Reddit
    client_secret: z.string().optional(), // For Reddit
    allowed_symbols: z.string().optional(), // Comma-separated symbols
    min_confidence: z.number().min(0).max(1).optional(),
  });
};

// Type for form data, exported for use in other components
export type ChannelFormData = {
  name: string;
  type: ChannelType;
  url: string;
  description?: string;
  category?: string;
  bearer_token?: string;
  client_id?: string;
  client_secret?: string;
  allowed_symbols?: string;
  min_confidence?: number;
};

interface AddChannelModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (data: ChannelFormData) => Promise<void>;
}

export const AddChannelModal: React.FC<AddChannelModalProps> = ({ isOpen, onClose, onAdd }) => {
  const [selectedType, setSelectedType] = useState<ChannelType>('telegram');
  
  const {
    control,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<ChannelFormData>({
    resolver: zodResolver(createChannelSchema(selectedType)),
    defaultValues: {
      name: '',
      type: 'telegram',
      url: '',
      description: '',
      category: 'general',
    },
  });
  
  const watchedType = watch('type');

  // Reset form when modal opens or closes
  useEffect(() => {
    if (isOpen) {
      reset({
        name: '',
        type: 'telegram',
        url: '',
        description: '',
        category: 'general',
      });
      setSelectedType('telegram');
    }
  }, [isOpen, reset]);
  
  // Update selected type when form type changes
  useEffect(() => {
    if (watchedType && watchedType !== selectedType) {
      setSelectedType(watchedType);
    }
  }, [watchedType, selectedType]);

  const onSubmit = async (data: ChannelFormData) => {
    await onAdd(data);
    onClose(); // Close modal on successful submission
  };

  const currentConfig = channelTypeConfigs[selectedType];
  const IconComponent = currentConfig.icon;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Добавить новый канал</DialogTitle>
          <DialogDescription>
            Выберите тип источника и настройте канал для отслеживания криптосигналов.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="grid gap-6 py-4">
          {/* Channel Type Selection */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="type" className="text-right">
              Тип источника
            </Label>
            <div className="col-span-3">
              <Controller
                name="type"
                control={control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={(value: string) => {
                    field.onChange(value);
                    setValue('url', ''); // Clear URL when type changes
                  }}>
                    <SelectTrigger>
                      <SelectValue placeholder="Выберите тип источника" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(channelTypeConfigs).map(([key, config]) => {
                        const Icon = config.icon;
                        return (
                          <SelectItem key={key} value={key}>
                            <div className="flex items-center gap-2">
                              <Icon className="h-4 w-4" />
                              <span>{config.name}</span>
                            </div>
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                )}
              />
              {errors.type && <p className="text-red-500 text-sm mt-1">{errors.type.message}</p>}
            </div>
          </div>

          {/* Channel Type Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <div className="flex items-center gap-2 mb-2">
              <IconComponent className="h-5 w-5 text-blue-600" />
              <span className="font-medium text-blue-800">{currentConfig.name}</span>
            </div>
            <p className="text-sm text-blue-700">{currentConfig.description}</p>
            <p className="text-xs text-blue-600 mt-1">
              Пример: {currentConfig.urlExample}
            </p>
          </div>

          {/* Channel Name */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">
              Название
            </Label>
            <div className="col-span-3">
              <Controller
                name="name"
                control={control}
                render={({ field }) => <Input id="name" {...field} placeholder="Введите название канала" />}
              />
              {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>}
            </div>
          </div>

          {/* Channel URL */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="url" className="text-right">
              URL/Идентификатор
            </Label>
            <div className="col-span-3">
              <Controller
                name="url"
                control={control}
                render={({ field }) => (
                  <Input 
                    id="url" 
                    {...field} 
                    placeholder={currentConfig.urlExample}
                  />
                )}
              />
              {errors.url && <p className="text-red-500 text-sm mt-1">{errors.url.message}</p>}
            </div>
          </div>

          {/* Description */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="description" className="text-right">
              Описание
            </Label>
            <div className="col-span-3">
              <Controller
                name="description"
                control={control}
                render={({ field }) => (
                  <Textarea
                    id="description"
                    {...field}
                    placeholder="Описание канала (опционально)"
                    className="resize-none"
                    rows={3}
                  />
                )}
              />
              {errors.description && (
                <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>
              )}
            </div>
          </div>

          {/* API Configuration for Twitter */}
          {selectedType === 'twitter' && (
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="bearer_token" className="text-right">
                Bearer Token
              </Label>
              <div className="col-span-3">
                <Controller
                  name="bearer_token"
                  control={control}
                  render={({ field }) => (
                    <Input 
                      id="bearer_token" 
                      {...field} 
                      type="password"
                      placeholder="Twitter API Bearer Token"
                    />
                  )}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Нужен для доступа к Twitter API
                </p>
              </div>
            </div>
          )}

          {/* API Configuration for Reddit */}
          {selectedType === 'reddit' && (
            <>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="client_id" className="text-right">
                  Client ID
                </Label>
                <div className="col-span-3">
                  <Controller
                    name="client_id"
                    control={control}
                    render={({ field }) => (
                      <Input 
                        id="client_id" 
                        {...field} 
                        placeholder="Reddit API Client ID"
                      />
                    )}
                  />
                </div>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="client_secret" className="text-right">
                  Client Secret
                </Label>
                <div className="col-span-3">
                  <Controller
                    name="client_secret"
                    control={control}
                    render={({ field }) => (
                      <Input 
                        id="client_secret" 
                        {...field} 
                        type="password"
                        placeholder="Reddit API Client Secret"
                      />
                    )}
                  />
                </div>
              </div>
            </>
          )}

          {/* Advanced Settings */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="allowed_symbols" className="text-right">
              Разрешенные символы
            </Label>
            <div className="col-span-3">
              <Controller
                name="allowed_symbols"
                control={control}
                render={({ field }) => (
                  <Input 
                    id="allowed_symbols" 
                    {...field} 
                    placeholder="BTC,ETH,ADA (через запятую, опционально)"
                  />
                )}
              />
              <p className="text-xs text-gray-500 mt-1">
                Оставьте пустым для отслеживания всех символов
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Отмена
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Добавить канал
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};


