import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import {
  X,
  Home,
  BarChart3,
  Users,
  User,
  Settings,
  Bell,
  LogOut,
  TrendingUp,
  Award,
  Shield,
  CreditCard,
  AlertTriangle,
  Zap,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { useNotifications } from '@/contexts/NotificationContext';
import useRealTimeNotifications from '@/hooks/useRealTimeNotifications';
import { useAuth } from '@/contexts/AuthContext';

const navigationItems = [
  {
    name: 'Главная',
    href: '/',
    icon: Home,
    description: 'Главная страница',
  },
  {
    name: 'Панель',
    href: '/dashboard',
    icon: BarChart3,
    description: 'Основная панель управления',
  },
  {
    name: 'Каналы',
    href: '/channels',
    icon: Users,
    description: 'Просмотр всех каналов',
  },
  {
    name: 'Сигналы',
    href: '/signals',
    icon: Zap,
    description: 'Торговые сигналы',
  },
  {
    name: 'Рейтинги',
    href: '/ratings',
    icon: Award,
    description: 'Топ каналов и антирейтинг',
  },
  {
    name: 'Профиль',
    href: '/profile',
    icon: User,
    description: 'Настройки профиля',
  },
];

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenNotifications?: () => void;
}

export function MobileMenu({
  isOpen,
  onClose,
  onOpenNotifications,
}: MobileMenuProps) {
  const router = useRouter();
  const [activeSection, setActiveSection] = useState<'main' | 'actions'>(
    'main'
  );
  const { state } = useNotifications();
  const { isConnected } = useRealTimeNotifications();
  const { user, logout } = useAuth();

  const quickActions = [
    {
      name: 'Уведомления',
      icon: Bell,
      action: 'notifications',
      description: 'Центр уведомлений',
      count: state.unreadCount,
      highlight: state.unreadCount > 0,
    },
    {
      name: 'Алерты',
      icon: Shield,
      action: 'alerts',
      description: 'Управление алертами',
      count: 0,
      highlight: false,
    },
    {
      name: 'Настройки',
      icon: Settings,
      action: 'settings',
      description: 'Настройки профиля',
      count: 0,
      highlight: false,
    },
    {
      name: 'Подписка',
      icon: CreditCard,
      action: 'subscription',
      description: 'Управление подпиской',
      count: 0,
      highlight: false,
    },
  ];

  const handleNavigation = (href: string) => {
    void router.push(href);
    onClose();
  };

  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'notifications':
        onOpenNotifications?.();
        onClose();
        break;
      case 'alerts':
        void router.push('/alerts');
        onClose();
        break;
      case 'settings':
        void router.push('/profile?tab=settings');
        onClose();
        break;
      case 'subscription':
        void router.push('/profile?tab=subscription');
        onClose();
        break;
    }
  };

  const handleLogout = async () => {
    onClose();
    await logout();
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Закрыть меню"
        className="fixed inset-0 bg-black/50 z-40 lg:hidden"
        onClick={onClose}
        onKeyDown={e => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onClose();
          }
        }}
      />

      {/* Mobile Menu */}
      <div className="fixed top-0 left-0 w-80 h-full bg-white shadow-xl z-50 lg:hidden transform transition-transform duration-300 ease-in-out">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <Link href="/" className="flex items-center" onClick={onClose}>
              <TrendingUp className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold gradient-text">
                CryptoAnalytics
              </span>
            </Link>

            <div className="flex items-center space-x-2">
              {/* Статус подключения */}
              <div
                className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}
                title={isConnected ? 'Подключено' : 'Отключено'}
              />

              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="h-6 w-6" />
              </Button>
            </div>
          </div>

          {/* User Info */}
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-xl">👨‍💼</span>
              </div>
              <div className="flex-1">
                <p className="font-medium text-gray-900">
                  {user?.name || user?.email || 'Гость'}
                </p>
                <p className="text-sm text-gray-600">
                  {user?.subscription.plan
                    ? `${user.subscription.plan} план`
                    : 'Войдите для полного доступа'}
                </p>
              </div>

              {/* Быстрая кнопка уведомлений */}
              <button
                onClick={() => handleQuickAction('notifications')}
                className="relative p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              >
                <Bell className="h-5 w-5" />
                {state.unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">
                    {state.unreadCount > 9 ? '9+' : state.unreadCount}
                  </span>
                )}
              </button>
            </div>
          </div>

          {/* Real-time Status Banner */}
          {!isConnected && (
            <div className="mx-4 mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                <span className="text-sm text-yellow-800">
                  Нет подключения к серверу
                </span>
              </div>
            </div>
          )}

          {/* Urgent Notifications */}
          {state.notifications.filter(n => !n.read && n.urgent).length > 0 && (
            <div className="mx-4 mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Zap className="h-4 w-4 text-red-600" />
                  <span className="text-sm font-medium text-red-800">
                    {
                      state.notifications.filter(n => !n.read && n.urgent)
                        .length
                    }{' '}
                    срочных уведомлений
                  </span>
                </div>
                <button
                  onClick={() => handleQuickAction('notifications')}
                  className="text-xs text-red-600 font-medium hover:text-red-700"
                >
                  Смотреть
                </button>
              </div>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveSection('main')}
              className={`flex-1 py-3 px-4 text-sm font-medium text-center transition-colors ${
                activeSection === 'main'
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Навигация
            </button>
            <button
              onClick={() => setActiveSection('actions')}
              className={`flex-1 py-3 px-4 text-sm font-medium text-center transition-colors relative ${
                activeSection === 'actions'
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Действия
              {state.unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full"></span>
              )}
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto">
            {activeSection === 'main' ? (
              /* Main Navigation */
              <div className="p-4 space-y-2">
                {navigationItems.map(item => {
                  const IconComponent = item.icon;
                  const isActive = router.pathname === item.href;

                  return (
                    <button
                      key={item.name}
                      onClick={() => handleNavigation(item.href)}
                      className={`w-full flex items-center space-x-3 p-3 rounded-lg text-left transition-colors ${
                        isActive
                          ? 'bg-blue-100 text-blue-600 border border-blue-200'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <IconComponent
                        className={`h-5 w-5 ${isActive ? 'text-blue-600' : 'text-gray-500'}`}
                      />
                      <div>
                        <p className="font-medium">{item.name}</p>
                        <p className="text-xs text-gray-500">
                          {item.description}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
            ) : (
              /* Quick Actions */
              <div className="p-4 space-y-2">
                {quickActions.map(action => {
                  const IconComponent = action.icon;

                  return (
                    <button
                      key={action.name}
                      onClick={() => handleQuickAction(action.action)}
                      className={`w-full flex items-center justify-between p-3 rounded-lg text-left transition-colors ${
                        action.highlight
                          ? 'bg-red-50 text-red-700 border border-red-200'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <IconComponent
                          className={`h-5 w-5 ${action.highlight ? 'text-red-600' : 'text-gray-500'}`}
                        />
                        <div>
                          <p className="font-medium">{action.name}</p>
                          <p className="text-xs text-gray-500">
                            {action.description}
                          </p>
                        </div>
                      </div>

                      {action.count > 0 && (
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            action.highlight
                              ? 'bg-red-100 text-red-800'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {action.count > 99 ? '99+' : action.count}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Bottom Actions */}
          <div className="border-t border-gray-200 p-4 space-y-2">
            {/* Connection Status */}
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Соединение:</span>
              <div className="flex items-center space-x-2">
                <div
                  className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}
                />
                <span
                  className={`font-medium ${isConnected ? 'text-green-600' : 'text-red-600'}`}
                >
                  {isConnected ? 'Онлайн' : 'Оффлайн'}
                </span>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
              <div>Уведомлений: {state.notifications.length}</div>
              <div>Непрочитанных: {state.unreadCount}</div>
            </div>

            {/* Logout */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Выйти
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}
