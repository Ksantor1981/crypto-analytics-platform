import { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { Menu } from 'lucide-react';

import { useAuth } from '@/contexts/AuthContext';
import { MobileMenu } from '@/components/layout/MobileMenu';
import { Button } from '@/components/ui/button';

const PUBLIC_PAGES = [
  '/',
  '/auth/login',
  '/auth/register',
  '/auth/forgot-password',
  '/auth/reset-password',
  '/pricing',
  '/demo',
  '/feedback',
];

export function AppNavbar() {
  const router = useRouter();
  const { user, logout, isAuthenticated } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  if (PUBLIC_PAGES.includes(router.pathname)) return null;

  const navItems = [
    { href: '/dashboard', label: 'Панель' },
    { href: '/channels', label: 'Каналы' },
    { href: '/signals', label: 'Сигналы' },
    { href: '/ratings', label: 'Рейтинги' },
    ...(user?.role === 'admin'
      ? [{ href: '/admin/review', label: 'Review' as const }]
      : []),
  ];

  return (
    <>
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
          <div className="flex justify-between h-14">
            <div className="flex items-center gap-2 sm:gap-6">
              <Button
                variant="ghost"
                size="sm"
                className="md:hidden p-2"
                onClick={() => setIsMobileMenuOpen(true)}
                aria-label="Меню"
              >
                <Menu className="h-6 w-6" />
              </Button>
              <Link
                href="/"
                className="flex items-center gap-2 font-bold text-lg text-blue-600 shrink-0"
              >
                CryptoAnalytics
              </Link>
              <div className="hidden md:flex gap-6">
                {navItems.map(item => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`text-sm font-medium transition-colors ${
                      router.pathname === item.href
                        ? 'text-blue-600 border-b-2 border-blue-600 pb-[15px]'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-2 sm:gap-3">
              {isAuthenticated ? (
                <>
                  <Link
                    href="/profile"
                    className="hidden sm:block text-sm text-gray-600 hover:text-gray-900"
                  >
                    {user?.name || user?.email || 'Профиль'}
                  </Link>
                  <button
                    type="button"
                    onClick={() => {
                      void logout();
                    }}
                    className="text-sm text-gray-500 hover:text-red-600"
                  >
                    Выйти
                  </button>
                </>
              ) : (
                <Link
                  href="/auth/login"
                  className="text-sm font-medium text-blue-600 hover:text-blue-700"
                >
                  Войти
                </Link>
              )}
            </div>
          </div>
        </div>
      </nav>
      <MobileMenu
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
      />
    </>
  );
}
