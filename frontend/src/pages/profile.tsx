import React, { useState } from 'react';
import Head from 'next/head';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { formatDate } from '@/lib/utils';

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
    telegram_username: user?.telegram_username || '',
    notification_settings: {
      email_notifications: true,
      telegram_notifications: true,
      signal_alerts: true,
      weekly_reports: true
    }
  });

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleNotificationChange = (setting: string, value: boolean) => {
    setFormData(prev => ({
      ...prev,
      notification_settings: {
        ...prev.notification_settings,
        [setting]: value
      }
    }));
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await updateUser(formData);
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating profile:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      full_name: user?.full_name || '',
      email: user?.email || '',
      telegram_username: user?.telegram_username || '',
      notification_settings: {
        email_notifications: true,
        telegram_notifications: true,
        signal_alerts: true,
        weekly_reports: true
      }
    });
    setIsEditing(false);
  };

  return (
    <>
      <Head>
        <title>Профиль - Crypto Analytics Platform</title>
        <meta name="description" content="Настройки профиля пользователя" />
      </Head>

      <DashboardLayout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Профиль</h1>
              <p className="text-gray-600">
                Управление настройками аккаунта
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button
                variant="outline"
                onClick={toggleTheme}
              >
                {theme === 'light' ? '🌙' : '☀️'} 
                {theme === 'light' ? 'Темная тема' : 'Светлая тема'}
              </Button>
              {!isEditing ? (
                <Button
                  variant="primary"
                  onClick={() => setIsEditing(true)}
                >
                  ✏️ Редактировать
                </Button>
              ) : (
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    onClick={handleCancel}
                  >
                    Отмена
                  </Button>
                  <Button
                    variant="primary"
                    onClick={handleSave}
                    disabled={isLoading}
                  >
                    {isLoading ? 'Сохранение...' : 'Сохранить'}
                  </Button>
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Profile info */}
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Основная информация
                  </h3>
                </CardHeader>
                <CardBody className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Полное имя
                    </label>
                    {isEditing ? (
                      <Input
                        value={formData.full_name}
                        onChange={(e) => handleInputChange('full_name', e.target.value)}
                        placeholder="Введите ваше имя"
                      />
                    ) : (
                      <p className="text-gray-900">{user?.full_name || 'Не указано'}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email
                    </label>
                    {isEditing ? (
                      <Input
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        placeholder="your@email.com"
                      />
                    ) : (
                      <p className="text-gray-900">{user?.email}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Telegram username
                    </label>
                    {isEditing ? (
                      <Input
                        value={formData.telegram_username}
                        onChange={(e) => handleInputChange('telegram_username', e.target.value)}
                        placeholder="@username"
                      />
                    ) : (
                      <p className="text-gray-900">
                        {user?.telegram_username || 'Не указано'}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Дата регистрации
                    </label>
                    <p className="text-gray-900">
                      {user?.created_at ? formatDate(user.created_at) : 'Не указано'}
                    </p>
                  </div>
                </CardBody>
              </Card>

              {/* Notification settings */}
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Настройки уведомлений
                  </h3>
                </CardHeader>
                <CardBody className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">Email уведомления</h4>
                      <p className="text-sm text-gray-600">
                        Получать уведомления на email
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.notification_settings.email_notifications}
                        onChange={(e) => handleNotificationChange('email_notifications', e.target.checked)}
                        className="sr-only peer"
                        disabled={!isEditing}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">Telegram уведомления</h4>
                      <p className="text-sm text-gray-600">
                        Получать уведомления в Telegram
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.notification_settings.telegram_notifications}
                        onChange={(e) => handleNotificationChange('telegram_notifications', e.target.checked)}
                        className="sr-only peer"
                        disabled={!isEditing}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">Уведомления о сигналах</h4>
                      <p className="text-sm text-gray-600">
                        Получать уведомления о новых сигналах
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.notification_settings.signal_alerts}
                        onChange={(e) => handleNotificationChange('signal_alerts', e.target.checked)}
                        className="sr-only peer"
                        disabled={!isEditing}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">Еженедельные отчеты</h4>
                      <p className="text-sm text-gray-600">
                        Получать еженедельную аналитику
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.notification_settings.weekly_reports}
                        onChange={(e) => handleNotificationChange('weekly_reports', e.target.checked)}
                        className="sr-only peer"
                        disabled={!isEditing}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </CardBody>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Account status */}
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Статус аккаунта
                  </h3>
                </CardHeader>
                <CardBody className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Статус</span>
                    <Badge variant="success">Активен</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Подписка</span>
                    <Badge variant="warning">Базовая</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Каналов</span>
                    <span className="font-medium">3</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Сигналов</span>
                    <span className="font-medium">127</span>
                  </div>
                </CardBody>
              </Card>

              {/* Quick actions */}
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Быстрые действия
                  </h3>
                </CardHeader>
                <CardBody className="space-y-3">
                  <Button variant="outline" className="w-full justify-start">
                    🔐 Изменить пароль
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    📊 Экспорт данных
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    🎯 Настройки API
                  </Button>
                  <Button variant="outline" className="w-full justify-start text-red-600 hover:text-red-700">
                    🗑️ Удалить аккаунт
                  </Button>
                </CardBody>
              </Card>

              {/* Security */}
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Безопасность
                  </h3>
                </CardHeader>
                <CardBody className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">2FA</span>
                    <Badge variant="secondary">Отключено</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Последний вход</span>
                    <span className="text-sm text-gray-500">Сегодня</span>
                  </div>
                  <Button variant="outline" className="w-full">
                    Настроить 2FA
                  </Button>
                </CardBody>
              </Card>
            </div>
          </div>
        </div>
      </DashboardLayout>
    </>
  );
} 