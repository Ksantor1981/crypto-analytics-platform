import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  TrendingUp,
  User,
  Settings,
  Bell,
  Shield,
  CreditCard,
  Eye,
  EyeOff,
  Save,
  Edit2,
  Camera,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Award,
  TrendingDown,
  BarChart3,
  DollarSign,
  Target,
  Clock,
  CheckCircle,
  AlertCircle,
  Info,
} from 'lucide-react';

// Mock user data
const mockUser = {
  id: 1,
  name: 'Алексей Иванов',
  email: 'aleksey.ivanov@email.com',
  username: '@crypto_trader_alex',
  avatar: '👨‍💼',
  joinDate: '2023-03-15',
  plan: 'Premium',
  status: 'verified',
  stats: {
    totalSignals: 1247,
    successRate: 87.5,
    totalProfit: 24.3,
    channelsFollowed: 12,
    alertsReceived: 356,
    daysActive: 298,
  },
  settings: {
    emailNotifications: true,
    pushNotifications: true,
    telegramAlerts: false,
    weeklyReports: true,
    darkMode: false,
    language: 'ru',
    timezone: 'Europe/Moscow',
  },
  subscription: {
    plan: 'Premium',
    price: 990,
    nextBilling: '2024-02-15',
    status: 'active',
  },
};

const planFeatures = {
  Free: ['До 3 каналов', 'Базовая аналитика', 'Email поддержка'],
  Premium: [
    'До 15 каналов',
    'Продвинутая аналитика',
    'Push уведомления',
    'Приоритетная поддержка',
  ],
  Pro: [
    'Безлимит каналов',
    'ML предсказания',
    'Все уведомления',
    'VIP поддержка',
    'API доступ',
  ],
};

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState('profile');
  const [isEditing, setIsEditing] = useState(false);
  const [user, setUser] = useState(mockUser);
  const [showEmail, setShowEmail] = useState(false);

  const handleSave = () => {
    setIsEditing(false);
    // Здесь будет сохранение данных
  };

  const tabs = [
    { id: 'profile', label: 'Профиль', icon: User },
    { id: 'settings', label: 'Настройки', icon: Settings },
    { id: 'notifications', label: 'Уведомления', icon: Bell },
    { id: 'security', label: 'Безопасность', icon: Shield },
    { id: 'subscription', label: 'Подписка', icon: CreditCard },
  ];

  const getPlanColor = (plan: string) => {
    switch (plan) {
      case 'Free':
        return 'text-gray-600 bg-gray-100';
      case 'Premium':
        return 'text-blue-600 bg-blue-100';
      case 'Pro':
        return 'text-purple-600 bg-purple-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <>
      <Head>
        <title>Профиль - CryptoAnalytics</title>
        <meta
          name="description"
          content="Управление профилем и настройками аккаунта"
        />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Link href="/" className="flex items-center">
                  <TrendingUp className="h-8 w-8 text-blue-600" />
                  <span className="ml-2 text-xl font-bold gradient-text">
                    CryptoAnalytics
                  </span>
                </Link>
                <div className="ml-8 flex space-x-4">
                  <Link
                    href="/dashboard"
                    className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium"
                  >
                    Панель
                  </Link>
                  <Link
                    href="/channels"
                    className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium"
                  >
                    Каналы
                  </Link>
                  <Link
                    href="/ratings"
                    className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium"
                  >
                    Рейтинги
                  </Link>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">Demo User</span>
                <Button variant="ghost" size="sm">
                  Выйти
                </Button>
              </div>
            </div>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Профиль пользователя
            </h1>
            <p className="text-gray-600">
              Управление настройками аккаунта и подписками
            </p>
          </div>

          {/* Profile Summary Card */}
          <Card className="mb-8">
            <CardContent className="p-6">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                <div className="flex items-center space-x-4 mb-4 md:mb-0">
                  <div className="relative">
                    <div className="w-20 h-20 text-4xl flex items-center justify-center bg-blue-100 rounded-full">
                      {user.avatar}
                    </div>
                    <button className="absolute -bottom-1 -right-1 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white hover:bg-blue-700">
                      <Camera className="h-3 w-3" />
                    </button>
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">
                      {user.name}
                    </h2>
                    <p className="text-gray-600">{user.username}</p>
                    <div className="flex items-center space-x-3 mt-1">
                      <span
                        className={`text-xs px-2 py-1 rounded ${getPlanColor(user.plan)}`}
                      >
                        {user.plan}
                      </span>
                      <span className="flex items-center text-xs text-green-600">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Верифицирован
                      </span>
                      <span className="text-xs text-gray-500">
                        Активен с{' '}
                        {new Date(user.joinDate).toLocaleDateString('ru-RU')}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-lg font-bold text-blue-600">
                      {user.stats.channelsFollowed}
                    </div>
                    <div className="text-xs text-gray-600">Каналов</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-green-600">
                      {user.stats.successRate}%
                    </div>
                    <div className="text-xs text-gray-600">Успешность</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-purple-600">
                      +{user.stats.totalProfit}%
                    </div>
                    <div className="text-xs text-gray-600">Прибыль</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tabs */}
          <div className="mb-8">
            <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
              {tabs.map(tab => {
                const IconComponent = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <IconComponent className="h-4 w-4 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Tab Content */}
          {activeTab === 'profile' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Личная информация</CardTitle>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsEditing(!isEditing)}
                    >
                      <Edit2 className="h-4 w-4 mr-2" />
                      {isEditing ? 'Отмена' : 'Редактировать'}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Полное имя
                    </label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={user.name}
                        className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        onChange={e =>
                          setUser({ ...user, name: e.target.value })
                        }
                      />
                    ) : (
                      <p className="mt-1 text-gray-900">{user.name}</p>
                    )}
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Email
                    </label>
                    <div className="flex items-center mt-1">
                      {showEmail ? (
                        <p className="text-gray-900">{user.email}</p>
                      ) : (
                        <p className="text-gray-900">alex***@email.com</p>
                      )}
                      <button
                        onClick={() => setShowEmail(!showEmail)}
                        className="ml-2 text-gray-400 hover:text-gray-600"
                      >
                        {showEmail ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Telegram
                    </label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={user.username}
                        className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        onChange={e =>
                          setUser({ ...user, username: e.target.value })
                        }
                      />
                    ) : (
                      <p className="mt-1 text-gray-900">{user.username}</p>
                    )}
                  </div>

                  {isEditing && (
                    <Button onClick={handleSave} className="w-full">
                      <Save className="h-4 w-4 mr-2" />
                      Сохранить изменения
                    </Button>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Статистика аккаунта</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-blue-50 rounded-md">
                      <BarChart3 className="h-6 w-6 text-blue-600 mx-auto mb-1" />
                      <div className="text-lg font-bold text-blue-600">
                        {user.stats.totalSignals}
                      </div>
                      <div className="text-xs text-gray-600">
                        Сигналов получено
                      </div>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-md">
                      <Target className="h-6 w-6 text-green-600 mx-auto mb-1" />
                      <div className="text-lg font-bold text-green-600">
                        {user.stats.successRate}%
                      </div>
                      <div className="text-xs text-gray-600">Успешность</div>
                    </div>
                    <div className="text-center p-3 bg-purple-50 rounded-md">
                      <DollarSign className="h-6 w-6 text-purple-600 mx-auto mb-1" />
                      <div className="text-lg font-bold text-purple-600">
                        +{user.stats.totalProfit}%
                      </div>
                      <div className="text-xs text-gray-600">Общая прибыль</div>
                    </div>
                    <div className="text-center p-3 bg-orange-50 rounded-md">
                      <Clock className="h-6 w-6 text-orange-600 mx-auto mb-1" />
                      <div className="text-lg font-bold text-orange-600">
                        {user.stats.daysActive}
                      </div>
                      <div className="text-xs text-gray-600">
                        Дней активности
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === 'settings' && (
            <Card>
              <CardHeader>
                <CardTitle>Настройки приложения</CardTitle>
                <CardDescription>
                  Персонализируйте ваш опыт использования
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900">
                      Темная тема
                    </label>
                    <p className="text-sm text-gray-600">
                      Включить темное оформление интерфейса
                    </p>
                  </div>
                  <button
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      user.settings.darkMode ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                    onClick={() =>
                      setUser({
                        ...user,
                        settings: {
                          ...user.settings,
                          darkMode: !user.settings.darkMode,
                        },
                      })
                    }
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        user.settings.darkMode
                          ? 'translate-x-6'
                          : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div>
                  <label className="block font-medium text-gray-900 mb-2">
                    Язык интерфейса
                  </label>
                  <select
                    value={user.settings.language}
                    onChange={e =>
                      setUser({
                        ...user,
                        settings: {
                          ...user.settings,
                          language: e.target.value,
                        },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="ru">Русский</option>
                    <option value="en">English</option>
                  </select>
                </div>

                <div>
                  <label className="block font-medium text-gray-900 mb-2">
                    Часовой пояс
                  </label>
                  <select
                    value={user.settings.timezone}
                    onChange={e =>
                      setUser({
                        ...user,
                        settings: {
                          ...user.settings,
                          timezone: e.target.value,
                        },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Europe/Moscow">Москва (UTC+3)</option>
                    <option value="Europe/Kiev">Киев (UTC+2)</option>
                    <option value="Europe/London">Лондон (UTC+0)</option>
                  </select>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'notifications' && (
            <Card>
              <CardHeader>
                <CardTitle>Настройки уведомлений</CardTitle>
                <CardDescription>
                  Управляйте способами получения уведомлений
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {[
                  {
                    key: 'emailNotifications',
                    label: 'Email уведомления',
                    desc: 'Получать уведомления на почту',
                  },
                  {
                    key: 'pushNotifications',
                    label: 'Push уведомления',
                    desc: 'Уведомления в браузере',
                  },
                  {
                    key: 'telegramAlerts',
                    label: 'Telegram алерты',
                    desc: 'Мгновенные уведомления в Telegram',
                  },
                  {
                    key: 'weeklyReports',
                    label: 'Еженедельные отчеты',
                    desc: 'Сводка активности за неделю',
                  },
                ].map(setting => (
                  <div
                    key={setting.key}
                    className="flex items-center justify-between"
                  >
                    <div>
                      <label className="font-medium text-gray-900">
                        {setting.label}
                      </label>
                      <p className="text-sm text-gray-600">{setting.desc}</p>
                    </div>
                    <button
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        user.settings[setting.key]
                          ? 'bg-blue-600'
                          : 'bg-gray-200'
                      }`}
                      onClick={() =>
                        setUser({
                          ...user,
                          settings: {
                            ...user.settings,
                            [setting.key]: !user.settings[setting.key],
                          },
                        })
                      }
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          user.settings[setting.key]
                            ? 'translate-x-6'
                            : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Безопасность аккаунта</CardTitle>
                  <CardDescription>
                    Настройки безопасности и конфиденциальности
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <div>
                        <p className="font-medium">
                          Двухфакторная аутентификация
                        </p>
                        <p className="text-sm text-gray-600">Включена</p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm">
                      Настроить
                    </Button>
                  </div>

                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <AlertCircle className="h-5 w-5 text-yellow-600" />
                      <div>
                        <p className="font-medium">Смена пароля</p>
                        <p className="text-sm text-gray-600">
                          Обновлен 30 дней назад
                        </p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm">
                      Изменить
                    </Button>
                  </div>

                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Info className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="font-medium">Активные сессии</p>
                        <p className="text-sm text-gray-600">
                          3 активных устройства
                        </p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm">
                      Просмотреть
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === 'subscription' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Текущая подписка</CardTitle>
                  <CardDescription>Управление тарифным планом</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="text-lg font-bold">
                        {user.subscription.plan}
                      </h3>
                      <p className="text-gray-600">
                        {user.subscription.price}₽/месяц
                      </p>
                    </div>
                    <span className="text-sm px-3 py-1 bg-green-100 text-green-800 rounded-full">
                      Активна
                    </span>
                  </div>

                  <div className="space-y-2 mb-6">
                    {planFeatures[user.subscription.plan].map(
                      (feature, index) => (
                        <div key={index} className="flex items-center">
                          <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                          <span className="text-sm">{feature}</span>
                        </div>
                      )
                    )}
                  </div>

                  <div className="flex space-x-3">
                    <Button variant="outline" className="flex-1">
                      Изменить план
                    </Button>
                    <Button variant="outline" className="flex-1">
                      Отменить подписку
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </>
  );
}


