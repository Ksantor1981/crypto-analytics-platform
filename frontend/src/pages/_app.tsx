import '@/styles/globals.css';
import type { AppProps } from 'next/app';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ToastProvider } from '@/contexts/ToastContext';
import { NotificationProvider } from '@/contexts/NotificationContext';
import { AppNavbar } from '@/components/layout/AppNavbar';
import { GoogleAnalytics } from '@/components/analytics/GoogleAnalytics';

export default function App({ Component, pageProps }: AppProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 60 * 1000,
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <GoogleAnalytics />
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>
            <NotificationProvider>
              <AppNavbar />
              <Component {...pageProps} />
            </NotificationProvider>
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
