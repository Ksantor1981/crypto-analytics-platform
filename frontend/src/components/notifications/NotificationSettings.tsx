import React, { useState } from 'react';
import {
  Bell,
  Volume2,
  Monitor,
  AlertTriangle,
  Settings,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useNotifications } from '@/contexts/NotificationContext';

interface NotificationSettingsProps {
  onClose?: () => void;
}

export function NotificationSettings({ onClose }: NotificationSettingsProps) {
  const {
    state,
    updateSettings,
    requestNotificationPermission,
    showBrowserNotification,
  } = useNotifications();
  const [hasPermission, setHasPermission] = useState(
    Notification.permission === 'granted'
  );

  const handleBrowserNotificationToggle = async (enabled: boolean) => {
    if (enabled) {
      const permission = await requestNotificationPermission();
      setHasPermission(permission);

      if (permission) {
        updateSettings({ browserNotifications: true });
        // Показываем тестовое уведомление
        await showBrowserNotification(
          'Уведомления включены',
          'Теперь вы будете получать уведомления браузера'
        );
      }
    } else {
      updateSettings({ browserNotifications: false });
    }
  };

  const testNotification = async () => {
    await showBrowserNotification(
      'Тестовое уведомление',
      'Это пример уведомления от CryptoAnalytics'
    );
  };

  const settingsGroups = [
    {
      title: 'Основные настройки',
      icon: <Bell className="h-5 w-5" />,
      settings: [
        {
          key: 'enabled',
          label: 'Включить уведомления',
          description: 'Получать уведомления от системы',
          type: 'toggle' as const,
        },
        {
          key: 'autoMarkAsRead',
          label: 'Автоотметка как прочитанное',
          description:
            'Автоматически отмечать уведомления как прочитанные через несколько секунд',
          type: 'toggle' as const,
        },
        {
          key: 'onlyImportant',
          label: 'Только важные',
          description: 'Показывать только срочные и важные уведомления',
          type: 'toggle' as const,
        },
      ],
    },
    {
      title: 'Браузерные уведомления',
      icon: <Monitor className="h-5 w-5" />,
      settings: [
        {
          key: 'browserNotifications',
          label: 'Уведомления браузера',
          description: 'Показывать уведомления даже когда вкладка неактивна',
          type: 'toggle' as const,
          disabled: !hasPermission && !state.settings.browserNotifications,
        },
      ],
    },
    {
      title: 'Звуковые уведомления',
      icon: <Volume2 className="h-5 w-5" />,
      settings: [
        {
          key: 'soundEnabled',
          label: 'Звуковые сигналы',
          description: 'Воспроизводить звуки при получении уведомлений',
          type: 'toggle' as const,
        },
      ],
    },
  ];

  const notificationTypes = [
    {
      type: 'signal',
      label: 'Новые сигналы',
      description: 'Уведомления о новых торговых сигналах',
      enabled: true,
    },
    {
      type: 'target_reached',
      label: 'Достижение целей',
      description: 'Когда сигнал достигает Take Profit',
      enabled: true,
    },
    {
      type: 'stop_loss',
      label: 'Стоп-лоссы',
      description: 'Срабатывание стоп-лоссов',
      enabled: true,
    },
    {
      type: 'price_alert',
      label: 'Ценовые алерты',
      description: 'Пользовательские ценовые алерты',
      enabled: true,
    },
    {
      type: 'channel_update',
      label: 'Обновления каналов',
      description: 'Изменения в рейтингах и статистике каналов',
      enabled: false,
    },
    {
      type: 'system',
      label: 'Системные',
      description: 'Важные системные уведомления',
      enabled: true,
    },
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Статус разрешений */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Settings className="h-5 w-5 mr-2" />
            Статус уведомлений
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
              <div className="flex items-center space-x-3">
                <div
                  className={`w-3 h-3 rounded-full ${
                    state.isWebSocketConnected ? 'bg-green-500' : 'bg-red-500'
                  }`}
                />
                <div>
                  <p className="font-medium">Real-time подключение</p>
                  <p className="text-sm text-gray-600">
                    {state.isWebSocketConnected ? 'Подключено' : 'Отключено'}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
              <div className="flex items-center space-x-3">
                <div
                  className={`w-3 h-3 rounded-full ${
                    hasPermission ? 'bg-green-500' : 'bg-yellow-500'
                  }`}
                />
                <div>
                  <p className="font-medium">Разрешения браузера</p>
                  <p className="text-sm text-gray-600">
                    {hasPermission ? 'Разрешены' : 'Требуется разрешение'}
                  </p>
                </div>
              </div>
              {!hasPermission && (
                <Button
                  size="sm"
                  onClick={() => handleBrowserNotificationToggle(true)}
                >
                  Разрешить
                </Button>
              )}
            </div>

            <div className="flex items-center justify-between">
              <span>Непрочитанных уведомлений: {state.unreadCount}</span>
              <Button
                variant="outline"
                size="sm"
                onClick={testNotification}
                disabled={!hasPermission}
              >
                Тест уведомления
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Основные настройки */}
      {settingsGroups.map(group => (
        <Card key={group.title}>
          <CardHeader>
            <CardTitle className="flex items-center">
              {group.icon}
              <span className="ml-2">{group.title}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {group.settings.map(setting => (
                <div
                  key={setting.key}
                  className="flex items-center justify-between"
                >
                  <div className="flex-1">
                    <p className="font-medium">{setting.label}</p>
                    <p className="text-sm text-gray-600">
                      {setting.description}
                    </p>
                  </div>

                  {setting.type === 'toggle' && (
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={
                          state.settings[
                            setting.key as keyof typeof state.settings
                          ] as boolean
                        }
                        disabled={
                          'disabled' in setting ? setting.disabled : false
                        }
                        onChange={e => {
                          if (setting.key === 'browserNotifications') {
                            handleBrowserNotificationToggle(e.target.checked);
                          } else {
                            updateSettings({ [setting.key]: e.target.checked });
                          }
                        }}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                    </label>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Типы уведомлений */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2" />
            Типы уведомлений
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {notificationTypes.map(type => (
              <div
                key={type.type}
                className="flex items-center justify-between p-3 rounded-lg border"
              >
                <div className="flex-1">
                  <p className="font-medium">{type.label}</p>
                  <p className="text-sm text-gray-600">{type.description}</p>
                </div>

                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    defaultChecked={type.enabled}
                    onChange={e => {
                      // Здесь будет логика сохранения настроек типов уведомлений
                      console.log(`${type.type}: ${e.target.checked}`);
                    }}
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                </label>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Дополнительные настройки */}
      <Card>
        <CardHeader>
          <CardTitle>Дополнительные настройки</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Время тихого режима</p>
                <p className="text-sm text-gray-600">
                  Не показывать уведомления в определенные часы
                </p>
              </div>
              <div className="flex space-x-2">
                <input
                  type="time"
                  className="border rounded px-2 py-1 text-sm"
                  defaultValue="22:00"
                />
                <span className="self-center">-</span>
                <input
                  type="time"
                  className="border rounded px-2 py-1 text-sm"
                  defaultValue="08:00"
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Группировка уведомлений</p>
                <p className="text-sm text-gray-600">
                  Объединять похожие уведомления
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  defaultChecked={true}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Кнопки действий */}
      <div className="flex justify-between space-x-4">
        <Button variant="outline" onClick={onClose}>
          Закрыть
        </Button>
        <div className="space-x-2">
          <Button variant="outline">Сбросить настройки</Button>
          <Button>Сохранить изменения</Button>
        </div>
      </div>
    </div>
  );
}

export default NotificationSettings;


