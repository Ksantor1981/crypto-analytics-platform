'use client';

import { useState, ReactNode } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import {
  Home,
  BarChart3,
  Users,
  User,
  Settings,
  Menu,
  Bell,
  LogOut,
  TrendingUp,
  Award,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import MobileMenu from '@/components/layout/MobileMenu';
import NotificationCenter from '@/components/notifications/NotificationCenter';
import { ToastContainer } from '@/components/notifications/NotificationToast';
import { useNotifications } from '@/contexts/NotificationContext';
import useRealTimeNotifications from '@/hooks/useRealTimeNotifications';
import ResponsiveNavigation from '@/components/layout/ResponsiveNavigation';
import useResponsive from '@/hooks/useResponsive';

interface DashboardLayoutProps {
  children: ReactNode;
  title?: string;
}

const navigationItems = [
  {
    name: 'Главная',
    href: '/',
    icon: Home,
  },
  {
    name: 'Панель',
    href: '/dashboard',
    icon: BarChart3,
  },
  {
    name: 'Каналы',
    href: '/channels',
    icon: Users,
  },
  {
    name: 'Рейтинги',
    href: '/ratings',
    icon: Award,
  },
  {
    name: 'Профиль',
    href: '/profile',
    icon: User,
  },
];

export function DashboardLayout({ children, title }: DashboardLayoutProps) {
  const router = useRouter();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);

  // Интеграция с системой уведомлений
  const { state } = useNotifications();
  const { isConnected } = useRealTimeNotifications();
  const { isMobile } = useResponsive();

  const handleLogout = () => {
    // Здесь будет логика выхода
    console.log('Logout');
    router.push('/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Desktop Sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex min-h-0 flex-1 flex-col bg-white border-r border-gray-200">
          {/* Logo */}
          <div className="flex h-16 flex-shrink-0 items-center px-6 border-b border-gray-200">
            <Link href="/" className="flex items-center">
              <TrendingUp className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold gradient-text">
                CryptoAnalytics
              </span>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1">
            {navigationItems.map(item => {
              const IconComponent = item.icon;
              const isActive = router.pathname === item.href;

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-100 text-blue-600'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <IconComponent
                    className={`mr-3 h-5 w-5 ${isActive ? 'text-blue-600' : 'text-gray-500'}`}
                  />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* User section */}
          <div className="flex-shrink-0 p-4 border-t border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-sm">👨‍💼</span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-700">Demo User</p>
                <p className="text-xs text-gray-500">Premium план</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="w-full mt-3 justify-start text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Выйти
            </Button>
          </div>
        </div>
      </div>

      {/* Mobile header */}
      <div className="lg:hidden">
        <div className="flex items-center justify-between h-16 px-4 bg-white border-b border-gray-200">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsMobileMenuOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </Button>

          <Link href="/" className="flex items-center">
            <TrendingUp className="h-6 w-6 text-blue-600" />
            <span className="ml-2 text-lg font-bold gradient-text">
              CryptoAnalytics
            </span>
          </Link>

          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsNotificationsOpen(true)}
              className="relative"
            >
              <Bell className="h-5 w-5" />
              {state.unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full text-xs text-white flex items-center justify-center min-w-[12px]">
                  {state.unreadCount > 9 ? '9+' : state.unreadCount}
                </span>
              )}
              {/* Индикатор подключения */}
              <div
                className={`absolute -bottom-1 -right-1 w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-400' : 'bg-red-400'
                }`}
              />
            </Button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar for desktop */}
        <div className="hidden lg:flex items-center justify-between h-16 px-6 bg-white border-b border-gray-200">
          <div>
            {title && (
              <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
            )}
          </div>

          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsNotificationsOpen(true)}
              className="relative"
            >
              <Bell className="h-5 w-5" />
              {state.unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full text-xs text-white flex items-center justify-center min-w-[12px]">
                  {state.unreadCount > 9 ? '9+' : state.unreadCount}
                </span>
              )}
              {/* Индикатор подключения */}
              <div
                className={`absolute -bottom-1 -right-1 w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-400' : 'bg-red-400'
                }`}
              />
            </Button>

            <Button variant="ghost" size="sm">
              <Settings className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* Page content */}
        <main className={`py-6 ${isMobile ? 'pb-20' : ''}`}>
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>

      {/* Mobile Menu */}
      <MobileMenu
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
        onOpenNotifications={() => setIsNotificationsOpen(true)}
      />

      {/* Notification Center */}
      <NotificationCenter
        isOpen={isNotificationsOpen}
        onClose={() => setIsNotificationsOpen(false)}
      />

      {/* Mobile Bottom Navigation */}
      <ResponsiveNavigation
        onOpenNotifications={() => setIsNotificationsOpen(true)}
      />

      {/* Toast Notifications */}
      <ToastContainer />
    </div>
  );
}

export default DashboardLayout;

