'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/contexts/AuthContext';
import { Loading } from '@/components/ui/Loading';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
  fallback?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
  fallback
}) => {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      // Redirect to login if not authenticated
      router.push('/auth/login');
    }
  }, [user, isLoading, router]);

  // Show loading while checking authentication
  if (isLoading) {
    return fallback || (
      <div className="min-h-screen flex items-center justify-center">
        <Loading />
      </div>
    );
  }

  // Show nothing if not authenticated (will redirect)
  if (!user) {
    return null;
  }

  // Check role if required
  if (requiredRole && user.role !== requiredRole) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Доступ запрещен
          </h2>
          <p className="text-gray-600 mb-4">
            У вас нет прав для доступа к этой странице
          </p>
          <button
            onClick={() => router.push('/dashboard')}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            Вернуться на главную
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

// HOC для оборачивания компонентов
export const withAuth = <P extends object>(
  Component: React.ComponentType<P>,
  requiredRole?: string
) => {
  const AuthenticatedComponent = (props: P) => {
    return (
      <ProtectedRoute requiredRole={requiredRole}>
        <Component {...props} />
      </ProtectedRoute>
    );
  };

  AuthenticatedComponent.displayName = `withAuth(${Component.displayName || Component.name})`;
  
  return AuthenticatedComponent;
}; 