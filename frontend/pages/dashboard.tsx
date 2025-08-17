import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';

interface Channel {
  id: number;
  name: string;
  rating: number;
  signals: number;
  success_rate: number;
  followers: string;
  category: 'premium' | 'good' | 'avoid';
  last_signal: string;
}

interface Signal {
  id: number;
  channel: string;
  pair: string;
  direction: 'LONG' | 'SHORT';
  entry_price: number;
  target_price: number;
  stop_loss: number;
  confidence: number;
  timestamp: string;
  status: 'ACTIVE' | 'COMPLETED' | 'FAILED';
  profit_loss?: number;
}

export default function Dashboard() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    // Имитация загрузки данных
    setTimeout(() => {
      setChannels([
        {
          id: 1,
          name: "Crypto Signals Pro",
          rating: 9.2,
          signals: 156,
          success_rate: 87.2,
          followers: "45.2K",
          category: "premium",
          last_signal: "2 часа назад"
        },
        {
          id: 2,
          name: "Bitcoin Trader",
          rating: 8.7,
          signals: 89,
          success_rate: 82.1,
          followers: "23.1K",
          category: "good",
          last_signal: "5 часов назад"
        },
        {
          id: 3,
          name: "Altcoin Master",
          rating: 7.9,
          signals: 234,
          success_rate: 75.6,
          followers: "67.8K",
          category: "good",
          last_signal: "1 день назад"
        }
      ]);

      setSignals([
        {
          id: 1,
          channel: "Crypto Signals Pro",
          pair: "BTC/USDT",
          direction: "LONG",
          entry_price: 43250,
          target_price: 44500,
          stop_loss: 42500,
          confidence: 87,
          timestamp: "2025-08-17 14:30",
          status: "ACTIVE"
        },
        {
          id: 2,
          channel: "Bitcoin Trader",
          pair: "ETH/USDT",
          direction: "SHORT",
          entry_price: 2650,
          target_price: 2580,
          stop_loss: 2700,
          confidence: 82,
          timestamp: "2025-08-17 13:45",
          status: "COMPLETED",
          profit_loss: 2.6
        },
        {
          id: 3,
          channel: "Altcoin Master",
          pair: "SOL/USDT",
          direction: "LONG",
          entry_price: 98.5,
          target_price: 105.0,
          stop_loss: 95.0,
          confidence: 76,
          timestamp: "2025-08-17 12:15",
          status: "ACTIVE"
        }
      ]);

      setLoading(false);
    }, 1000);
  }, []);

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'premium': return 'text-green-600 bg-green-100';
      case 'good': return 'text-blue-600 bg-blue-100';
      case 'avoid': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getCategoryText = (category: string) => {
    switch (category) {
      case 'premium': return 'Премиум';
      case 'good': return 'Хороший';
      case 'avoid': return 'Избегать';
      default: return 'Неизвестно';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загрузка дашборда...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Дашборд - CryptoAnalytics</title>
        <meta name="description" content="Ваш персональный дашборд CryptoAnalytics" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Link href="/" className="flex items-center">
                  <svg className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                  <span className="ml-2 text-xl font-bold text-gray-900">CryptoAnalytics</span>
                </Link>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-gray-700">Добро пожаловать, Алексей!</span>
                <button className="text-gray-600 hover:text-gray-900">Выйти</button>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Активные сигналы</dt>
                      <dd className="text-lg font-medium text-gray-900">12</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Успешные сделки</dt>
                      <dd className="text-lg font-medium text-gray-900">87%</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Общая прибыль</dt>
                      <dd className="text-lg font-medium text-gray-900">+$2,450</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Отслеживаемые каналы</dt>
                      <dd className="text-lg font-medium text-gray-900">15</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="bg-white shadow rounded-lg">
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8 px-6">
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'overview'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Обзор
                </button>
                <button
                  onClick={() => setActiveTab('signals')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'signals'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Сигналы
                </button>
                <button
                  onClick={() => setActiveTab('channels')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'channels'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Каналы
                </button>
              </nav>
            </div>

            <div className="p-6">
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-medium text-gray-900">Последние сигналы</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Канал
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Пара
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Направление
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Статус
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Прибыль/Убыток
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {signals.slice(0, 5).map((signal) => (
                          <tr key={signal.id}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {signal.channel}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {signal.pair}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                signal.direction === 'LONG' 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {signal.direction}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                signal.status === 'ACTIVE' 
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : signal.status === 'COMPLETED'
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {signal.status === 'ACTIVE' ? 'Активен' : 
                                 signal.status === 'COMPLETED' ? 'Завершен' : 'Провален'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {signal.profit_loss ? (
                                <span className={signal.profit_loss > 0 ? 'text-green-600' : 'text-red-600'}>
                                  {signal.profit_loss > 0 ? '+' : ''}{signal.profit_loss}%
                                </span>
                              ) : (
                                <span className="text-gray-400">-</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {activeTab === 'signals' && (
                <div className="space-y-6">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-medium text-gray-900">Все сигналы</h3>
                    <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                      Новый сигнал
                    </button>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Канал
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Пара
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Направление
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Вход
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Цель
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Уверенность
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Статус
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {signals.map((signal) => (
                          <tr key={signal.id}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {signal.channel}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {signal.pair}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                signal.direction === 'LONG' 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {signal.direction}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              ${signal.entry_price}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              ${signal.target_price}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                  <div 
                                    className="bg-blue-600 h-2 rounded-full" 
                                    style={{ width: `${signal.confidence}%` }}
                                  ></div>
                                </div>
                                <span className="text-sm text-gray-900">{signal.confidence}%</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                signal.status === 'ACTIVE' 
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : signal.status === 'COMPLETED'
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {signal.status === 'ACTIVE' ? 'Активен' : 
                                 signal.status === 'COMPLETED' ? 'Завершен' : 'Провален'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {activeTab === 'channels' && (
                <div className="space-y-6">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-medium text-gray-900">Отслеживаемые каналы</h3>
                    <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                      Добавить канал
                    </button>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {channels.map((channel) => (
                      <div key={channel.id} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="font-semibold text-lg">{channel.name}</h4>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(channel.category)}`}>
                            {getCategoryText(channel.category)}
                          </span>
                        </div>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Рейтинг:</span>
                            <span className="font-semibold">{channel.rating}/10</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Сигналов:</span>
                            <span className="font-semibold">{channel.signals}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Успешность:</span>
                            <span className="font-semibold">{channel.success_rate}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Последний сигнал:</span>
                            <span className="text-sm text-gray-500">{channel.last_signal}</span>
                          </div>
                        </div>
                        <div className="mt-4 pt-4 border-t border-gray-200">
                          <button className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 transition-colors">
                            Отписаться
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
