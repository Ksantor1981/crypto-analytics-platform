import React, { useState, useEffect } from 'react';
import { GetServerSideProps } from 'next';
import Head from 'next/head';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { SignalsList, SignalsFilter, SignalsStats, SignalCard } from '@/components/signals';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import { Signal, SignalFilters } from '@/types';

interface SignalsPageProps {
  initialSignals: Signal[];
}

export default function SignalsPage({ initialSignals }: SignalsPageProps) {
  const { user } = useAuth();
  const [signals, setSignals] = useState<Signal[]>(initialSignals);
  const [isLoading, setIsLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [filters, setFilters] = useState<SignalFilters>({});

  const fetchSignals = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.getSignals();
      setSignals(response || []);
    } catch (error) {
      console.error('Error fetching signals:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, [filters]);

  const handleFiltersChange = (newFilters: SignalFilters) => {
    setFilters(newFilters);
  };

  const handleResetFilters = () => {
    setFilters({});
  };

  const handleAnalyzeSignal = async (signal: Signal) => {
    try {
      // Временно просто логируем, так как analyzeSignal не реализован в API
      console.log('ML Analysis for signal:', signal.id);
      // Здесь можно показать модальное окно с результатами анализа
    } catch (error) {
      console.error('Error analyzing signal:', error);
    }
  };

  return (
    <>
      <Head>
        <title>Сигналы - Crypto Analytics Platform</title>
        <meta name="description" content="Торговые сигналы криптовалют" />
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
                  className={`px-3 py-1 rounded-md text-sm ${
                    viewMode === 'list'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  📋 Список
                </button>
                <button
                  onClick={() => setViewMode('grid')}
                  className={`px-3 py-1 rounded-md text-sm ${
                    viewMode === 'grid'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  🔲 Сетка
                </button>
              </div>
              <Button variant="default" onClick={fetchSignals}>
                🔄 Обновить
              </Button>
            </div>
          </div>

          {/* Filters */}
          <SignalsFilter
            filters={filters}
            onFiltersChange={handleFiltersChange}
            onReset={handleResetFilters}
          />

          {/* Stats */}
          <SignalsStats signals={signals} />

          {/* Signals List */}
          <div className="bg-white rounded-lg shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">
                  Сигналы ({signals.length})
                </h2>
                <div className="text-sm text-gray-500">
                  Последнее обновление: {new Date().toLocaleString()}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : signals.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>Сигналы не найдены</p>
                </div>
              ) : viewMode === 'list' ? (
                <SignalsList
                  signals={signals}
                  isLoading={isLoading}
                  onSignalSelect={handleAnalyzeSignal}
                  showChannel={true}
                />
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {signals.map(signal => (
                    <SignalCard
                      key={signal.id}
                      signal={signal}
                      showChannel={true}
                      onAnalyze={handleAnalyzeSignal}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </div>
        </div>
      </DashboardLayout>
    </>
  );
}

export const getServerSideProps: GetServerSideProps = async () => {
  try {
    // Временно возвращаем пустой массив, так как серверный рендеринг API не настроен
    return {
      props: {
        initialSignals: [],
      },
    };
  } catch (error) {
    console.error('Error fetching initial signals:', error);
    return {
      props: {
        initialSignals: [],
      },
    };
  }
};


