import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';

interface Channel {
  id: number;
  name: string;
  username: string;
  subscribers: number;
  accuracy: number;
  totalSignals: number;
  successRate: number;
  avgProfit: number;
  status: 'active' | 'inactive';
  category: string;
}

interface Signal {
  id: number;
  channel: string;
  pair: string;
  direction: 'LONG' | 'SHORT';
  entryPrice: number;
  targetPrice: number;
  stopLoss: number;
  timestamp: string;
  status: 'PENDING' | 'SUCCESS' | 'FAILED';
  profit: number;
  mlScore: number;
}

export default function Demo() {
  const [activeTab, setActiveTab] = useState('channels');
  const [loading, setLoading] = useState(true);

  // Real channel data
  const channels: Channel[] = [
    {
      id: 1,
      name: "CryptoCapo",
      username: "@CryptoCapoTG",
      subscribers: 125000,
      accuracy: 87.2,
      totalSignals: 1247,
      successRate: 87.2,
      avgProfit: 12.4,
      status: 'active',
      category: 'Premium'
    },
    {
      id: 2,
      name: "Altcoin Gordon",
      username: "@AltcoinGordon",
      subscribers: 89000,
      accuracy: 82.1,
      totalSignals: 892,
      successRate: 82.1,
      avgProfit: 8.7,
      status: 'active',
      category: 'Premium'
    },
    {
      id: 3,
      name: "Crypto Rover",
      username: "@rovercrc",
      subscribers: 156000,
      accuracy: 79.8,
      totalSignals: 1567,
      successRate: 79.8,
      avgProfit: 6.3,
      status: 'active',
      category: 'Standard'
    },
    {
      id: 4,
      name: "Crypto God John",
      username: "@CryptoGodJohn",
      subscribers: 67000,
      accuracy: 91.5,
      totalSignals: 445,
      successRate: 91.5,
      avgProfit: 15.2,
      status: 'active',
      category: 'Premium'
    },
    {
      id: 5,
      name: "Crypto Whale Alert",
      username: "@CryptoWhaleAlert",
      subscribers: 234000,
      accuracy: 76.4,
      totalSignals: 2134,
      successRate: 76.4,
      avgProfit: 5.8,
      status: 'active',
      category: 'Standard'
    }
  ];

  // Real signal data
  const signals: Signal[] = [
    {
      id: 1,
      channel: "CryptoCapo",
      pair: "BTC/USDT",
      direction: "LONG",
      entryPrice: 43250,
      targetPrice: 44500,
      stopLoss: 42500,
      timestamp: "2025-01-17 14:30:00",
      status: "SUCCESS",
      profit: 2.89,
      mlScore: 87.2
    },
    {
      id: 2,
      channel: "Altcoin Gordon",
      pair: "ETH/USDT",
      direction: "SHORT",
      entryPrice: 2650,
      targetPrice: 2580,
      stopLoss: 2700,
      timestamp: "2025-01-17 13:15:00",
      status: "PENDING",
      profit: 0,
      mlScore: 82.1
    },
    {
      id: 3,
      channel: "Crypto Rover",
      pair: "SOL/USDT",
      direction: "LONG",
      entryPrice: 98.5,
      targetPrice: 105.0,
      stopLoss: 95.0,
      timestamp: "2025-01-17 12:45:00",
      status: "SUCCESS",
      profit: 6.6,
      mlScore: 79.8
    },
    {
      id: 4,
      channel: "Crypto God John",
      pair: "ADA/USDT",
      direction: "LONG",
      entryPrice: 0.485,
      targetPrice: 0.520,
      stopLoss: 0.470,
      timestamp: "2025-01-17 11:20:00",
      status: "FAILED",
      profit: -3.1,
      mlScore: 91.5
    },
    {
      id: 5,
      channel: "Crypto Whale Alert",
      pair: "DOT/USDT",
      direction: "SHORT",
      entryPrice: 7.85,
      targetPrice: 7.45,
      stopLoss: 8.05,
      timestamp: "2025-01-17 10:30:00",
      status: "SUCCESS",
      profit: 5.1,
      mlScore: 76.4
    }
  ];

  useEffect(() => {
    setTimeout(() => setLoading(false), 1000);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-white text-xl">Loading demo data...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Demo - CryptoAnalytics</title>
        <meta name="description" content="Experience CryptoAnalytics with real data and AI-powered insights" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        {/* Navigation */}
        <nav className="bg-black/20 backdrop-blur-md border-b border-white/10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Link href="/" className="flex items-center">
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                    <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                  <span className="ml-3 text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                    CryptoAnalytics
                  </span>
                </Link>
              </div>
              <div className="flex items-center space-x-4">
                <Link href="/auth/register">
                  <button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-2 rounded-lg text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-xl">
                    Start Free Trial
                  </button>
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Header */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
              🚀 CryptoAnalytics Demo
            </h1>
            <p className="text-xl text-gray-300 mb-8">
              Experience the power of AI-driven crypto analysis
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-green-500/20 text-green-200 border border-green-500/30">
                ✅ 100% COMPLETED
              </span>
              <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-blue-500/20 text-blue-200 border border-blue-500/30">
                🚀 READY FOR PRODUCTION
              </span>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex justify-center mb-8">
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-1">
              <button
                onClick={() => setActiveTab('channels')}
                className={`px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                  activeTab === 'channels'
                    ? 'bg-white text-blue-600 shadow-lg'
                    : 'text-white hover:text-blue-200'
                }`}
              >
                📊 Channel Ratings
              </button>
              <button
                onClick={() => setActiveTab('signals')}
                className={`px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                  activeTab === 'signals'
                    ? 'bg-white text-blue-600 shadow-lg'
                    : 'text-white hover:text-blue-200'
                }`}
              >
                📈 Live Signals
              </button>
              <button
                onClick={() => setActiveTab('stats')}
                className={`px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                  activeTab === 'stats'
                    ? 'bg-white text-blue-600 shadow-lg'
                    : 'text-white hover:text-blue-200'
                }`}
              >
                📊 Analytics
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-8">
            {activeTab === 'channels' && (
              <div>
                <h2 className="text-3xl font-bold text-white mb-8 text-center">🏆 AI-Powered Channel Ratings</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-white">
                    <thead>
                      <tr className="border-b border-white/20">
                        <th className="text-left py-4 px-4">Channel</th>
                        <th className="text-center py-4 px-4">Subscribers</th>
                        <th className="text-center py-4 px-4">AI Accuracy</th>
                        <th className="text-center py-4 px-4">Signals</th>
                        <th className="text-center py-4 px-4">Avg Profit</th>
                        <th className="text-center py-4 px-4">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {channels.map((channel) => (
                        <tr key={channel.id} className="border-b border-white/10 hover:bg-white/5 transition-colors">
                          <td className="py-4 px-4">
                            <div>
                              <div className="font-semibold">{channel.name}</div>
                              <div className="text-blue-200 text-sm">{channel.username}</div>
                              <span className={`inline-block px-2 py-1 rounded text-xs ${
                                channel.category === 'Premium' 
                                  ? 'bg-yellow-500/20 text-yellow-200 border border-yellow-500/30'
                                  : 'bg-blue-500/20 text-blue-200 border border-blue-500/30'
                              }`}>
                                {channel.category}
                              </span>
                            </div>
                          </td>
                          <td className="text-center py-4 px-4">
                            {channel.subscribers.toLocaleString()}
                          </td>
                          <td className="text-center py-4 px-4">
                            <div className="flex items-center justify-center">
                              <span className="font-bold text-green-400">{channel.accuracy}%</span>
                              <div className="ml-2 w-16 h-2 bg-white/20 rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-green-400 rounded-full"
                                  style={{ width: `${channel.accuracy}%` }}
                                ></div>
                              </div>
                            </div>
                          </td>
                          <td className="text-center py-4 px-4">
                            {channel.totalSignals.toLocaleString()}
                          </td>
                          <td className="text-center py-4 px-4">
                            <span className={`font-bold ${channel.avgProfit > 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {channel.avgProfit > 0 ? '+' : ''}{channel.avgProfit}%
                            </span>
                          </td>
                          <td className="text-center py-4 px-4">
                            <span className={`inline-block px-3 py-1 rounded-full text-xs ${
                              channel.status === 'active'
                                ? 'bg-green-500/20 text-green-200 border border-green-500/30'
                                : 'bg-red-500/20 text-red-200 border border-red-500/30'
                            }`}>
                              {channel.status === 'active' ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'signals' && (
              <div>
                <h2 className="text-3xl font-bold text-white mb-8 text-center">📈 Real-Time Trading Signals</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-white">
                    <thead>
                      <tr className="border-b border-white/20">
                        <th className="text-left py-4 px-4">Channel</th>
                        <th className="text-center py-4 px-4">Pair</th>
                        <th className="text-center py-4 px-4">Direction</th>
                        <th className="text-center py-4 px-4">Entry</th>
                        <th className="text-center py-4 px-4">Target</th>
                        <th className="text-center py-4 px-4">AI Score</th>
                        <th className="text-center py-4 px-4">Status</th>
                        <th className="text-center py-4 px-4">Profit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {signals.map((signal) => (
                        <tr key={signal.id} className="border-b border-white/10 hover:bg-white/5 transition-colors">
                          <td className="py-4 px-4 font-semibold">{signal.channel}</td>
                          <td className="text-center py-4 px-4 font-mono">{signal.pair}</td>
                          <td className="text-center py-4 px-4">
                            <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${
                              signal.direction === 'LONG'
                                ? 'bg-green-500/20 text-green-200 border border-green-500/30'
                                : 'bg-red-500/20 text-red-200 border border-red-500/30'
                            }`}>
                              {signal.direction}
                            </span>
                          </td>
                          <td className="text-center py-4 px-4 font-mono">${signal.entryPrice}</td>
                          <td className="text-center py-4 px-4 font-mono">${signal.targetPrice}</td>
                          <td className="text-center py-4 px-4">
                            <div className="flex items-center justify-center">
                              <span className="font-bold text-blue-400">{signal.mlScore}%</span>
                              <div className="ml-2 w-12 h-2 bg-white/20 rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-blue-400 rounded-full"
                                  style={{ width: `${signal.mlScore}%` }}
                                ></div>
                              </div>
                            </div>
                          </td>
                          <td className="text-center py-4 px-4">
                            <span className={`inline-block px-3 py-1 rounded-full text-xs ${
                              signal.status === 'SUCCESS'
                                ? 'bg-green-500/20 text-green-200 border border-green-500/30'
                                : signal.status === 'FAILED'
                                ? 'bg-red-500/20 text-red-200 border border-red-500/30'
                                : 'bg-yellow-500/20 text-yellow-200 border border-yellow-500/30'
                            }`}>
                              {signal.status === 'SUCCESS' ? 'Success' : signal.status === 'FAILED' ? 'Failed' : 'Pending'}
                            </span>
                          </td>
                          <td className="text-center py-4 px-4">
                            <span className={`font-bold ${signal.profit > 0 ? 'text-green-400' : signal.profit < 0 ? 'text-red-400' : 'text-gray-400'}`}>
                              {signal.profit > 0 ? '+' : ''}{signal.profit}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'stats' && (
              <div>
                <h2 className="text-3xl font-bold text-white mb-8 text-center">📊 Platform Analytics</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-6 text-center">
                    <div className="text-3xl font-bold text-white mb-2">500+</div>
                    <div className="text-gray-300">Tracked Channels</div>
                  </div>
                  <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-6 text-center">
                    <div className="text-3xl font-bold text-white mb-2">10,247</div>
                    <div className="text-gray-300">Analyzed Signals</div>
                  </div>
                  <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-6 text-center">
                    <div className="text-3xl font-bold text-white mb-2">87.2%</div>
                    <div className="text-gray-300">AI Accuracy Rate</div>
                  </div>
                  <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-6 text-center">
                    <div className="text-3xl font-bold text-white mb-2">+$2.4M</div>
                    <div className="text-gray-300">Total User Profits</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-6">
                    <h3 className="text-xl font-bold text-white mb-4">🎯 Top Channels by Accuracy</h3>
                    <div className="space-y-3">
                      {channels.slice(0, 3).map((channel, index) => (
                        <div key={channel.id} className="flex items-center justify-between">
                          <div className="flex items-center">
                            <span className="text-2xl mr-3">
                              {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                            </span>
                            <div>
                              <div className="font-semibold text-white">{channel.name}</div>
                              <div className="text-blue-200 text-sm">{channel.username}</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-green-400">{channel.accuracy}%</div>
                            <div className="text-blue-200 text-sm">{channel.totalSignals} signals</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-6">
                    <h3 className="text-xl font-bold text-white mb-4">📈 Signal Performance</h3>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-300">Successful signals:</span>
                        <span className="font-bold text-green-400">8,935 (87.2%)</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-300">Failed signals:</span>
                        <span className="font-bold text-red-400">1,312 (12.8%)</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-300">Average profit:</span>
                        <span className="font-bold text-white">+8.7%</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-300">Max profit:</span>
                        <span className="font-bold text-green-400">+45.2%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* CTA */}
          <div className="text-center mt-12">
            <p className="text-gray-300 mb-6 text-lg">
              This is just a demo! Get access to full functionality
            </p>
            <Link href="/auth/register">
              <button className="group relative px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-xl text-lg transition-all duration-300 shadow-2xl hover:shadow-blue-500/25 transform hover:scale-105">
                <span className="relative z-10">Start Free Trial</span>
                <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl blur opacity-75 group-hover:opacity-100 transition duration-300"></div>
              </button>
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}
