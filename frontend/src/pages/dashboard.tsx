import React, { useEffect, useState } from 'react';
import Head from 'next/head';
import { DashboardLayout, StatsCard, RecentSignals } from '@/components/dashboard';
import { ProtectedRoute } from '@/components/auth';
import { PerformanceChart, DoughnutChart, BarChart } from '@/components/charts';
import { signalsApi } from '@/lib/api';
import { Signal } from '@/types';

const DashboardPage: React.FC = () => {
  const [recentSignals, setRecentSignals] = useState<Signal[]>([]);
  const [allSignals, setAllSignals] = useState<Signal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    totalSignals: 0,
    activeSignals: 0,
    successRate: 0,
    totalPnl: 0
  });

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        
        // Fetch recent signals
        const signalsResponse = await signalsApi.getSignals({
          limit: 10,
          offset: 0
        });
        
        // Fetch all signals for charts
        const allSignalsResponse = await signalsApi.getSignals({
          limit: 1000,
          offset: 0
        });
        
        setRecentSignals(signalsResponse.data.items);
        setAllSignals(allSignalsResponse.data.items);
        
        // Calculate stats
        const totalSignals = signalsResponse.data.total;
        const activeSignals = signalsResponse.data.items.filter(s => s.status === 'active').length;
        const completedSignals = signalsResponse.data.items.filter(s => s.status === 'completed');
        const successRate = completedSignals.length > 0 
          ? (completedSignals.filter(s => s.pnl && s.pnl > 0).length / completedSignals.length) * 100
          : 0;
        const totalPnl = signalsResponse.data.items.reduce((sum, s) => sum + (s.pnl || 0), 0);
        
        setStats({
          totalSignals,
          activeSignals,
          successRate,
          totalPnl
        });
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Данные для графика статусов сигналов
  const getStatusChartData = () => {
    const statusCounts = allSignals.reduce((acc, signal) => {
      acc[signal.status] = (acc[signal.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      labels: ['Активные', 'Выполненные', 'Не выполненные', 'Отмененные'],
      datasets: [{
        data: [
          statusCounts.active || 0,
          statusCounts.completed || 0,
          statusCounts.failed || 0,
          statusCounts.cancelled || 0
        ],
        backgroundColor: [
          '#fbbf24', // yellow for active
          '#10b981', // green for completed
          '#ef4444', // red for failed
          '#6b7280'  // gray for cancelled
        ],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    };
  };

  // Данные для графика по активам
  const getAssetChartData = () => {
    const assetCounts = allSignals.reduce((acc, signal) => {
      const asset = signal.asset.split('/')[0]; // BTC/USDT -> BTC
      acc[asset] = (acc[asset] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const sortedAssets = Object.entries(assetCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10); // Топ 10 активов

    return {
      labels: sortedAssets.map(([asset]) => asset),
      datasets: [{
        label: 'Количество сигналов',
        data: sortedAssets.map(([, count]) => count),
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1
      }]
    };
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Дашборд - Crypto Analytics Platform</title>
        <meta name="description" content="Дашборд платформы анализа криптовалютных сигналов" />
      </Head>
      
      <DashboardLayout>
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatsCard
              title="Всего сигналов"
              value={stats.totalSignals}
              icon="📊"
              change={{
                value: 12,
                type: 'increase'
              }}
            />
            <StatsCard
              title="Активных сигналов"
              value={stats.activeSignals}
              icon="⚡"
            />
            <StatsCard
              title="Успешность"
              value={`${stats.successRate.toFixed(1)}%`}
              icon="🎯"
              change={{
                value: 5.2,
                type: 'increase'
              }}
            />
            <StatsCard
              title="Общий P&L"
              value={`${stats.totalPnl > 0 ? '+' : ''}${stats.totalPnl.toFixed(2)}%`}
              icon="💰"
              change={{
                value: 8.1,
                type: stats.totalPnl > 0 ? 'increase' : 'decrease'
              }}
            />
          </div>

          {/* Performance Chart */}
          {allSignals.length > 0 && (
            <PerformanceChart signals={allSignals} timeRange="month" height={350} />
          )}

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Status Distribution */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Распределение по статусам</h3>
              {allSignals.length > 0 ? (
                <DoughnutChart data={getStatusChartData()} height={300} />
              ) : (
                <div className="flex items-center justify-center h-64 text-gray-500">
                  Нет данных для отображения
                </div>
              )}
            </div>

            {/* Top Assets */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Популярные активы</h3>
              {allSignals.length > 0 ? (
                <BarChart data={getAssetChartData()} height={300} />
              ) : (
                <div className="flex items-center justify-center h-64 text-gray-500">
                  Нет данных для отображения
                </div>
              )}
            </div>
          </div>

          {/* Recent Signals and Top Channels */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <RecentSignals
              signals={recentSignals}
              isLoading={isLoading}
            />
            
            {/* Top Channels */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Топ каналы</h3>
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                        <span className="text-green-600 font-semibold text-sm">#{i}</span>
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">Channel {i}</div>
                        <div className="text-sm text-gray-600">Точность: {(85 + i * 2)}%</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-green-600">+{(15 + i * 3).toFixed(1)}%</div>
                      <div className="text-xs text-gray-500">{100 + i * 20} сигналов</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Быстрые действия</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left">
                <div className="text-2xl mb-2">📡</div>
                <div className="font-medium">Добавить канал</div>
                <div className="text-sm text-gray-600">Подключить новый Telegram канал</div>
              </button>
              <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left">
                <div className="text-2xl mb-2">📊</div>
                <div className="font-medium">Анализ портфеля</div>
                <div className="text-sm text-gray-600">Просмотреть детальную статистику</div>
              </button>
              <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left">
                <div className="text-2xl mb-2">⚙️</div>
                <div className="font-medium">Настройки</div>
                <div className="text-sm text-gray-600">Настроить уведомления и фильтры</div>
              </button>
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
};

export default DashboardPage; 