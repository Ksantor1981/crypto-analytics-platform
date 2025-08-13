import React, { useState, useEffect, Suspense } from 'react';
import { GetServerSideProps } from 'next';
import Head from 'next/head';
import dynamic from 'next/dynamic';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { SectionLoading, EmptyState } from '@/components/ui/Loading';
import { useAuth } from '@/contexts/AuthContext';
import { useSignals } from '@/hooks/useSignals';
import { useDebounced } from '@/lib/performance';
import { Signal, SignalFilters } from '@/types';

// Lazy loading компонентов
const OptimizedSignalsList = dynamic(
  () =>
    import('@/components/signals/OptimizedSignalsList').then(mod => ({
      default: mod.OptimizedSignalsList,
    })),
  {
    loading: () => <SectionLoading message="Загрузка списка сигналов..." />,
    ssr: false,
  }
);

const SignalsStats = dynamic(
  () =>
    import('@/components/signals').then(mod => ({ default: mod.SignalsStats })),
  {
    loading: () => <SectionLoading height="h-32" />,
    ssr: false,
  }
);

const SignalsFilter = dynamic(
  () =>
    import('@/components/signals').then(mod => ({
      default: mod.SignalsFilter,
    })),
  {
    loading: () => <SectionLoading height="h-40" />,
    ssr: false,
  }
);

interface OptimizedSignalsPageProps {
  initialSignals: Signal[];
}

export default function OptimizedSignalsPage({
  initialSignals,
}: OptimizedSignalsPageProps) {
  const { user } = useAuth();
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState<SignalFilters>({});
  const [showFilters, setShowFilters] = useState(false);

  // Debounced search для оптимизации
  const debouncedSearchTerm = useDebounced(searchTerm, 300);

  // Объединяем поисковый запрос с фильтрами
  const combinedFilters = {
    ...filters,
    search: debouncedSearchTerm,
  };

  const { signals, isLoading, error, refetch, analyzeSignal, isAnalyzing } =
    useSignals(combinedFilters);

  // Используем начальные данные, если еще не загружены новые
  const displaySignals = signals.length > 0 ? signals : initialSignals;

  const handleFiltersChange = (newFilters: SignalFilters) => {
    setFilters(newFilters);
  };

  const handleResetFilters = () => {
    setFilters({});
    setSearchTerm('');
  };

  const handleAnalyzeSignal = async (signal: Signal) => {
    try {
      await analyzeSignal(signal.id);
    } catch (error) {
      console.error('Error analyzing signal:', error);
    }
  };

  const handleRefresh = () => {
    refetch();
  };

  return (
    <>
      <Head>
        <title>Сигналы - Crypto Analytics Platform</title>
        <meta name="description" content="Торговые сигналы криптовалют" />
        <link rel="prefetch" href="/api/signals" />
      </Head>

      <DashboardLayout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Сигналы</h1>
              <p className="text-gray-600">
                Торговые сигналы от проверенных каналов
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <div className="flex items-center bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-3 py-1 rounded-md text-sm transition-colors ${
                    viewMode === 'list'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  📋 Список
                </button>
                <button
                  onClick={() => setViewMode('grid')}
                  className={`px-3 py-1 rounded-md text-sm transition-colors ${
                    viewMode === 'grid'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  🔲 Сетка
                </button>
              </div>
              <Button
                variant="outline"
                onClick={handleRefresh}
                disabled={isLoading}
              >
                🔄 {isLoading ? 'Обновление...' : 'Обновить'}
              </Button>
            </div>
          </div>

          {/* Search and quick filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <Input
                    placeholder="Поиск по активу, статусу или направлению..."
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    className="w-full"
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    onClick={() => setShowFilters(!showFilters)}
                  >
                    🔍 Фильтры
                    {Object.keys(filters).length > 0 && (
                      <span className="ml-2 bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                        {Object.keys(filters).length}
                      </span>
                    )}
                  </Button>
                  {(Object.keys(filters).length > 0 || searchTerm) && (
                    <Button variant="outline" onClick={handleResetFilters}>
                      ✕ Сбросить
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Statistics - lazy loaded */}
          <Suspense fallback={<SectionLoading height="h-32" />}>
            <SignalsStats signals={displaySignals} />
          </Suspense>

          {/* Advanced filters - lazy loaded and conditional */}
          {showFilters && (
            <Suspense fallback={<SectionLoading height="h-40" />}>
              <SignalsFilter
                filters={filters}
                onFiltersChange={handleFiltersChange}
                onReset={handleResetFilters}
              />
            </Suspense>
          )}

          {/* Results count */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                  Найдено сигналов: {displaySignals.length}
                </h2>
                <div className="text-sm text-gray-600">
                  {isLoading ? (
                    <span className="flex items-center">
                      <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full mr-2"></div>
                      Загрузка...
                    </span>
                  ) : (
                    'Последнее обновление: только что'
                  )}
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Signals display */}
          {error ? (
            <Card>
              <CardContent className="text-center py-12">
                <div className="text-red-400 text-6xl mb-4">⚠️</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Ошибка загрузки
                </h3>
                <p className="text-gray-600 mb-4">
                  Не удалось загрузить сигналы. Попробуйте еще раз.
                </p>
                <Button variant="default" onClick={handleRefresh}>
                  Попробовать снова
                </Button>
              </CardContent>
            </Card>
          ) : displaySignals.length === 0 && !isLoading ? (
            <EmptyState
              icon="⚡"
              title="Нет сигналов"
              description="Попробуйте изменить фильтры или подключить новые каналы"
              action={{
                label: 'Перейти к каналам',
                onClick: () => (window.location.href = '/channels'),
              }}
            />
          ) : (
            <Suspense fallback={<SectionLoading height="h-96" />}>
              {viewMode === 'list' ? (
                <OptimizedSignalsList
                  signals={displaySignals}
                  isLoading={isLoading}
                  onSignalSelect={handleAnalyzeSignal}
                  showChannel={true}
                  searchTerm={debouncedSearchTerm}
                />
              ) : (
                // Grid view - можно также оптимизировать
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {displaySignals.map(signal => (
                    <div key={signal.id}>
                      {/* Здесь будет оптимизированный SignalCard */}
                      <div className="bg-white rounded-lg shadow p-4">
                        <div className="font-medium">{signal.asset}</div>
                        <div className="text-sm text-gray-600">
                          {signal.direction}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Suspense>
          )}
        </div>
      </DashboardLayout>
    </>
  );
}

export const getServerSideProps: GetServerSideProps = async context => {
  try {
    // В реальном приложении здесь будет запрос к API с кэшированием
    const initialSignals: Signal[] = [
      {
        id: '1',
        channel_id: '1',
        pair: 'BTC/USDT',
        asset: 'BTC/USDT',
        direction: 'long',
        entry_price: 45000,
        target_price: 48000,
        stop_loss: 43000,
        status: 'active',
        pnl: 2.5,
        confidence: 0.85,
        description: 'Пробой сопротивления, хорошая точка входа',
        created_at: new Date().toISOString(),
        channel: {
          id: '1',
          name: 'Crypto Signals Pro',
        },
      },
    ];

    return {
      props: {
        initialSignals,
      },
    };
  } catch (error) {
    console.error('Error fetching signals:', error);
    return {
      props: {
        initialSignals: [],
      },
    };
  }
};



