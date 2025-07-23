import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Home, BarChart3, Users, Award, User, Bell, Plus } from 'lucide-react';
import { useNotifications } from '@/contexts/NotificationContext';

interface ResponsiveNavigationProps {
  onOpenNotifications?: () => void;
}

const navigationItems = [
  {
    name: 'Главная',
    href: '/',
    icon: Home,
    shortName: 'Дом',
  },
  {
    name: 'Панель',
    href: '/dashboard',
    icon: BarChart3,
    shortName: 'Панель',
  },
  {
    name: 'Каналы',
    href: '/channels',
    icon: Users,
    shortName: 'Каналы',
  },
  {
    name: 'Рейтинги',
    href: '/ratings',
    icon: Award,
    shortName: 'Топ',
  },
  {
    name: 'Профиль',
    href: '/profile',
    icon: User,
    shortName: 'Я',
  },
];

export function ResponsiveNavigation({
  onOpenNotifications,
}: ResponsiveNavigationProps) {
  const router = useRouter();
  const { state } = useNotifications();
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  // Скрытие навигации при прокрутке вниз
  useEffect(() => {
    const controlNavbar = () => {
      const currentScrollY = window.scrollY;

      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        setIsVisible(false); // Скрываем при прокрутке вниз
      } else {
        setIsVisible(true); // Показываем при прокрутке вверх
      }

      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', controlNavbar);
    return () => window.removeEventListener('scroll', controlNavbar);
  }, [lastScrollY]);

  return (
    <div
      className={`
      fixed bottom-0 left-0 right-0 z-40 lg:hidden
      bg-white border-t border-gray-200 shadow-lg
      transform transition-transform duration-300 ease-in-out
      ${isVisible ? 'translate-y-0' : 'translate-y-full'}
    `}
    >
      <div className="flex items-center justify-around py-2 px-4 max-w-md mx-auto">
        {navigationItems.map(item => {
          const IconComponent = item.icon;
          const isActive = router.pathname === item.href;

          return (
            <button
              key={item.name}
              onClick={() => router.push(item.href)}
              className={`
                flex flex-col items-center justify-center p-2 rounded-lg
                min-w-[60px] transition-all duration-200 ease-in-out
                ${
                  isActive
                    ? 'text-blue-600 bg-blue-50 scale-105'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50 active:scale-95'
                }
              `}
            >
              <IconComponent
                className={`h-5 w-5 mb-1 ${isActive ? 'text-blue-600' : 'text-gray-500'}`}
              />
              <span
                className={`text-xs font-medium truncate ${isActive ? 'text-blue-600' : 'text-gray-600'}`}
              >
                {item.shortName}
              </span>
            </button>
          );
        })}

        {/* Floating Action Button для уведомлений */}
        <button
          onClick={onOpenNotifications}
          className={`
            relative flex flex-col items-center justify-center p-2 rounded-lg
            min-w-[60px] transition-all duration-200 ease-in-out
            text-gray-600 hover:text-blue-600 hover:bg-blue-50 active:scale-95
            ${state.unreadCount > 0 ? 'animate-pulse' : ''}
          `}
        >
          <Bell className="h-5 w-5 mb-1" />
          <span className="text-xs font-medium">Алерты</span>

          {state.unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">
              {state.unreadCount > 9 ? '9+' : state.unreadCount}
            </span>
          )}
        </button>
      </div>
    </div>
  );
}

// Floating Action Button для быстрых действий
export function FloatingActionButton() {
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();

  const actions = [
    {
      name: 'Новый алерт',
      icon: Bell,
      action: () => router.push('/alerts'),
      color: 'bg-blue-500 hover:bg-blue-600',
    },
    {
      name: 'Добавить канал',
      icon: Plus,
      action: () => router.push('/channels?action=add'),
      color: 'bg-green-500 hover:bg-green-600',
    },
  ];

  return (
    <div className="fixed bottom-20 right-4 z-30 lg:hidden">
      {/* Action Items */}
      {isOpen && (
        <div className="mb-4 space-y-2">
          {actions.map((action, index) => (
            <div
              key={action.name}
              className={`
                flex items-center space-x-3 transform transition-all duration-300 ease-out
                ${isOpen ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'}
              `}
              style={{ transitionDelay: `${index * 50}ms` }}
            >
              <span className="bg-black/75 text-white text-xs px-2 py-1 rounded-lg whitespace-nowrap">
                {action.name}
              </span>
              <button
                onClick={() => {
                  action.action();
                  setIsOpen(false);
                }}
                className={`
                  w-12 h-12 rounded-full shadow-lg text-white
                  flex items-center justify-center transition-transform
                  ${action.color} active:scale-95
                `}
              >
                <action.icon className="h-5 w-5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Main FAB */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg
          flex items-center justify-center transition-all duration-300
          ${isOpen ? 'rotate-45 scale-110' : 'rotate-0 scale-100'}
          active:scale-95
        `}
      >
        <Plus className="h-6 w-6" />
      </button>
    </div>
  );
}

// Pull-to-refresh компонент
export function PullToRefresh({
  onRefresh,
  children,
}: {
  onRefresh: () => Promise<void>;
  children: React.ReactNode;
}) {
  const [isPulling, setIsPulling] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  let startY = 0;
  const threshold = 80;

  const handleTouchStart = (e: React.TouchEvent) => {
    startY = e.touches[0].clientY;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (window.scrollY === 0) {
      const currentY = e.touches[0].clientY;
      const distance = Math.max(0, currentY - startY);

      if (distance > 0) {
        setIsPulling(true);
        setPullDistance(Math.min(distance, threshold * 1.5));
      }
    }
  };

  const handleTouchEnd = async () => {
    if (pullDistance >= threshold) {
      setIsRefreshing(true);
      try {
        await onRefresh();
      } finally {
        setIsRefreshing(false);
      }
    }

    setIsPulling(false);
    setPullDistance(0);
  };

  return (
    <div
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      className="relative"
    >
      {/* Pull indicator */}
      {(isPulling || isRefreshing) && (
        <div
          className="absolute top-0 left-0 right-0 flex items-center justify-center py-4 z-50"
          style={{
            transform: `translateY(${isRefreshing ? 60 : Math.max(0, pullDistance - 20)}px)`,
            transition: isRefreshing ? 'transform 0.3s ease' : 'none',
          }}
        >
          <div
            className={`
            flex items-center space-x-2 px-4 py-2 bg-white rounded-full shadow-lg border
            ${pullDistance >= threshold ? 'text-blue-600 border-blue-200' : 'text-gray-500 border-gray-200'}
          `}
          >
            <div
              className={`
              w-4 h-4 border-2 border-current border-t-transparent rounded-full
              ${isRefreshing ? 'animate-spin' : ''}
            `}
            />
            <span className="text-sm font-medium">
              {isRefreshing
                ? 'Обновление...'
                : pullDistance >= threshold
                  ? 'Отпустите для обновления'
                  : 'Потяните для обновления'}
            </span>
          </div>
        </div>
      )}

      <div
        style={{
          transform: `translateY(${isPulling || isRefreshing ? pullDistance : 0}px)`,
          transition: isPulling ? 'none' : 'transform 0.3s ease',
        }}
      >
        {children}
      </div>
    </div>
  );
}

export default ResponsiveNavigation;
