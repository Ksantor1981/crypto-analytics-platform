import React, { useState, useEffect } from 'react';
import { GetServerSideProps } from 'next';
import Head from 'next/head';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { SignalsList, SignalsFilter, SignalsStats } from '@/components/signals';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { useAuth } from '@/contexts/AuthContext';
import { signalsApi } from '@/lib/api';
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
      const response = await signalsApi.getSignals(filters);
      setSignals(response.data);
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
      // Вызов ML API для анализа сигнала
      const prediction = await signalsApi.analyzeSignal(signal.id);
      console.log('ML Analysis:', prediction);
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
              <Button variant="primary" onClick={fetchSignals}>
                🔄 Обновить
              </Button>
            </div>
          </div>

          {/* Statistics */}
          <SignalsStats signals={signals} />

          {/* Filters */}
          <SignalsFilter
            filters={filters}
            onFiltersChange={handleFiltersChange}
            onReset={handleResetFilters}
          />

          {/* Results count */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                  Найдено сигналов: {signals.length}
                </h2>
                <div className="text-sm text-gray-600">
                  {isLoading ? 'Загрузка...' : 'Последнее обновление: только что'}
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Signals list/grid */}
          {viewMode === 'list' ? (
            <SignalsList
              signals={signals}
              isLoading={isLoading}
              onSignalSelect={handleAnalyzeSignal}
              showChannel={true}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {isLoading ? (
                // Loading skeleton for grid
                Array.from({ length: 6 }).map((_, i) => (
                  <Card key={i}>
                    <CardBody className="p-6">
                      <div className="animate-pulse">
                        <div className="flex items-center space-x-3 mb-4">
                          <div className="w-12 h-12 bg-gray-200 rounded-full"></div>
                          <div>
                            <div className="w-24 h-4 bg-gray-200 rounded mb-2"></div>
                            <div className="w-16 h-3 bg-gray-200 rounded"></div>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="w-full h-3 bg-gray-200 rounded"></div>
                          <div className="w-3/4 h-3 bg-gray-200 rounded"></div>
                          <div className="w-1/2 h-3 bg-gray-200 rounded"></div>
                        </div>
                      </div>
                    </CardBody>
                  </Card>
                ))
              ) : signals.length === 0 ? (
                <div className="col-span-full">
                  <Card>
                    <CardBody className="text-center py-12">
                      <div className="text-gray-400 text-6xl mb-4">⚡</div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        Нет сигналов
                      </h3>
                      <p className="text-gray-600">
                        Попробуйте изменить фильтры или подключить новые каналы
                      </p>
                    </CardBody>
                  </Card>
                </div>
              ) : (
                signals.map((signal) => (
                  <div key={signal.id}>
                    <SignalCard
                      signal={signal}
                      showChannel={true}
                      onAnalyze={handleAnalyzeSignal}
                    />
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </DashboardLayout>
    </>
  );
}

export const getServerSideProps: GetServerSideProps = async (context) => {
  try {
    // В реальном приложении здесь будет запрос к API
    // const response = await signalsApi.getSignals();
    
    // Пока возвращаем моковые данные
    const initialSignals: Signal[] = [
      {
        id: '1',
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
        updated_at: new Date().toISOString(),
        channel: {
          id: '1',
          name: 'Crypto Signals Pro',
          description: 'Профессиональные сигналы',
          username: '@crypto_signals_pro',
          subscribers_count: 15000,
          accuracy: 78.5,
          total_signals: 245,
          successful_signals: 192,
          avg_profit: 12.3,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          is_active: true,
          subscription_price: 50
        }
      },
      {
        id: '2',
        asset: 'ETH/USDT',
        direction: 'short',
        entry_price: 3200,
        target_price: 3000,
        stop_loss: 3350,
        status: 'completed',
        pnl: 6.25,
        confidence: 0.92,
        description: 'Медвежий флаг, ожидаем снижения',
        created_at: new Date(Date.now() - 86400000).toISOString(), // 1 день назад
        updated_at: new Date().toISOString(),
        channel: {
          id: '2',
          name: 'Technical Analysis Hub',
          description: 'Технический анализ',
          username: '@ta_hub',
          subscribers_count: 8500,
          accuracy: 82.1,
          total_signals: 156,
          successful_signals: 128,
          avg_profit: 8.7,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          is_active: true,
          subscription_price: 30
        }
      }
    ];

    return {
      props: {
        initialSignals
      }
    };
  } catch (error) {
    console.error('Error fetching signals:', error);
    return {
      props: {
        initialSignals: []
      }
    };
  }
}; 