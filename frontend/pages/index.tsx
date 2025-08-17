import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';

export default function HomeNew() {
  const router = useRouter();
  const [timestamp, setTimestamp] = useState<string>('');
  
  useEffect(() => {
    setTimestamp(Date.now().toString());
  }, []);

  return (
    <>
      <Head>
        <title>CryptoAnalytics - AI-Powered Crypto Signal Analysis</title>
        <meta name="description" content="Discover hidden 100x cryptocurrencies with advanced AI insights. Get real-time trading signals, channel ratings, and market analysis with 87.2% accuracy." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
        <meta httpEquiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
        <meta httpEquiv="Pragma" content="no-cache" />
        <meta httpEquiv="Expires" content="0" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        {/* Хедер с версионированием */}
        <header className="relative z-50 bg-black/20 backdrop-blur-xl border-b border-purple-500/20">
          <div className="container mx-auto px-6 py-4">
            <nav className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  CryptoAnalytics
                </div>
                <span className="text-xs text-purple-300 bg-purple-500/20 px-2 py-1 rounded">
                  v2.0.{timestamp}
                </span>
              </div>
              
              <div className="hidden md:flex items-center space-x-8">
                <a href="#features" className="text-purple-200 hover:text-purple-400 transition-colors">
                  Features
                </a>
                <a href="#pricing" className="text-purple-200 hover:text-purple-400 transition-colors">
                  Pricing
                </a>
                <button 
                  onClick={() => router.push('/auth/login')}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 px-6 py-2 rounded-lg text-white hover:shadow-lg hover:shadow-purple-500/25 transition-all"
                >
                  Get Started
                </button>
              </div>
            </nav>
          </div>
        </header>

        {/* Hero Section - ОБНОВЛЕННЫЙ ДИЗАЙН */}
        <section className="relative py-20 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 to-pink-500/10"></div>
          
          <div className="container mx-auto px-6 relative z-10">
            <div className="text-center max-w-4xl mx-auto">
              <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-white via-purple-200 to-pink-200 bg-clip-text text-transparent">
                AI-Powered Crypto
                <span className="block bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  Signal Analytics
                </span>
              </h1>
              
              <p className="text-xl text-purple-200 mb-8 max-w-2xl mx-auto leading-relaxed">
                Анализируйте криптовалютные сигналы с помощью машинного обучения. 
                87.2% точность предсказаний для максимальной прибыли.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
                <button 
                  onClick={() => router.push('/auth/register')}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 px-8 py-4 rounded-xl text-white font-semibold text-lg hover:shadow-2xl hover:shadow-purple-500/25 transform hover:scale-105 transition-all"
                >
                  Начать бесплатно
                </button>
                <button 
                  onClick={() => router.push('/demo')}
                  className="border-2 border-purple-400 text-purple-300 px-8 py-4 rounded-xl font-semibold text-lg hover:bg-purple-400/10 transition-all"
                >
                  Посмотреть демо
                </button>
              </div>

              {/* Статистики */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
                <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-purple-500/20">
                  <div className="text-3xl font-bold text-purple-400 mb-2">87.2%</div>
                  <div className="text-purple-200">Точность ML модели</div>
                </div>
                <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-purple-500/20">
                  <div className="text-3xl font-bold text-pink-400 mb-2">110+</div>
                  <div className="text-purple-200">Аналитических признаков</div>
                </div>
                <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-purple-500/20">
                  <div className="text-3xl font-bold text-purple-400 mb-2">&lt;0.3s</div>
                  <div className="text-purple-200">Время отклика API</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section - НОВЫЙ ДИЗАЙН */}
        <section id="features" className="py-20 bg-black/20">
          <div className="container mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                Возможности платформы
              </h2>
              <p className="text-purple-200 text-lg max-w-2xl mx-auto">
                Используйте силу искусственного интеллекта для анализа криптовалютных сигналов
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {/* Feature 1 */}
              <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-lg rounded-2xl p-8 border border-purple-500/20 hover:border-purple-400/40 transition-all">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-6">
                  <span className="text-2xl">🤖</span>
                </div>
                <h3 className="text-xl font-semibold text-white mb-4">AI-анализ сигналов</h3>
                <p className="text-purple-200">
                  Ensemble модели машинного обучения анализируют сигналы с точностью 87.2%
                </p>
              </div>

              {/* Feature 2 */}
              <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-lg rounded-2xl p-8 border border-purple-500/20 hover:border-purple-400/40 transition-all">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-6">
                  <span className="text-2xl">📊</span>
                </div>
                <h3 className="text-xl font-semibold text-white mb-4">Real-time данные</h3>
                <p className="text-purple-200">
                  Актуальные данные с бирж Binance и Bybit в реальном времени
                </p>
              </div>

              {/* Feature 3 */}
              <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-lg rounded-2xl p-8 border border-purple-500/20 hover:border-purple-400/40 transition-all">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-6">
                  <span className="text-2xl">🎯</span>
                </div>
                <h3 className="text-xl font-semibold text-white mb-4">Антирейтинг каналов</h3>
                <p className="text-purple-200">
                  Инновационная система оценки качества криптовалютных каналов
                </p>
              </div>

              {/* Feature 4 */}
              <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-lg rounded-2xl p-8 border border-purple-500/20 hover:border-purple-400/40 transition-all">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-6">
                  <span className="text-2xl">⚡</span>
                </div>
                <h3 className="text-xl font-semibold text-white mb-4">Высокая производительность</h3>
                <p className="text-purple-200">
                  API отвечает менее чем за 0.3 секунды, 99.9% uptime
                </p>
              </div>

              {/* Feature 5 */}
              <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-lg rounded-2xl p-8 border border-purple-500/20 hover:border-purple-400/40 transition-all">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-6">
                  <span className="text-2xl">🔒</span>
                </div>
                <h3 className="text-xl font-semibold text-white mb-4">Безопасность</h3>
                <p className="text-purple-200">
                  JWT аутентификация, RBAC система, защита от DDoS атак
                </p>
              </div>

              {/* Feature 6 */}
              <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-lg rounded-2xl p-8 border border-purple-500/20 hover:border-purple-400/40 transition-all">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-6">
                  <span className="text-2xl">🚀</span>
                </div>
                <h3 className="text-xl font-semibold text-white mb-4">Auto-trading (скоро)</h3>
                <p className="text-purple-200">
                  Автоматическая торговля на основе AI-анализа сигналов
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="py-20">
          <div className="container mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                Тарифные планы
              </h2>
              <p className="text-purple-200 text-lg">
                Выберите подходящий план для ваших потребностей
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              {/* Free Plan */}
              <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-purple-500/20">
                <h3 className="text-2xl font-bold text-white mb-4">Free</h3>
                <div className="text-4xl font-bold text-purple-400 mb-6">
                  $0<span className="text-lg text-purple-200">/мес</span>
                </div>
                <ul className="space-y-3 mb-8">
                  <li className="flex items-center text-purple-200">
                    <span className="text-green-400 mr-3">✓</span>
                    5 каналов
                  </li>
                  <li className="flex items-center text-purple-200">
                    <span className="text-green-400 mr-3">✓</span>
                    Базовая аналитика
                  </li>
                  <li className="flex items-center text-purple-200">
                    <span className="text-green-400 mr-3">✓</span>
                    Email поддержка
                  </li>
                </ul>
                <button className="w-full bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg transition-colors">
                  Начать бесплатно
                </button>
              </div>

              {/* Pro Plan */}
              <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-lg rounded-2xl p-8 border-2 border-purple-400 relative">
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-2 rounded-full text-sm font-semibold">
                  Популярный
                </div>
                <h3 className="text-2xl font-bold text-white mb-4">Pro</h3>
                <div className="text-4xl font-bold text-purple-400 mb-6">
                  $29<span className="text-lg text-purple-200">/мес</span>
                </div>
                <ul className="space-y-3 mb-8">
                  <li className="flex items-center text-purple-200">
                    <span className="text-green-400 mr-3">✓</span>
                    50 каналов
                  </li>
                  <li className="flex items-center text-purple-200">
                    <span className="text-green-400 mr-3">✓</span>
                    Расширенная аналитика
                  </li>
                  <li className="flex items-center text-purple-200">
                    <span className="text-green-400 mr-3">✓</span>
                    ML предсказания
                  </li>
                  <li className="flex items-center text-purple-200">
                    <span className="text-green-400 mr-3">✓</span>
                    Приоритетная поддержка
                  </li>
                </ul>
                <button className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 rounded-lg hover:shadow-lg transition-all">
                  Выбрать Pro
                </button>
              </div>

              {/* Enterprise Plan */}
              <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-purple-500/20">
                <h3 className="text-2xl font-bold text-white mb-4">Enterprise</h3>
                <div className="text-4xl font-bold text-purple-400 mb-6">
                  $99<span className="text-lg text-purple-200">/мес</span>
                </div>
                <ul className="space-y-3 mb-8">
                  <li className="flex items-center text-purple-200">
                    <span className="text-green-400 mr-3">✓</span>
                    Безлимит каналов
                  </li>
                  <li className="flex items-center text-purple-200">
                    <span className="text-green-400 mr-3">✓</span>
                    API доступ
                  </li>
                  <li className="flex items-center text-purple-200">
                    <span className="text-green-400 mr-3">✓</span>
                    Персональный менеджер
                  </li>
                  <li className="flex items-center text-purple-200">
                    <span className="text-green-400 mr-3">✓</span>
                    SLA 99.9%
                  </li>
                </ul>
                <button className="w-full bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg transition-colors">
                  Связаться с нами
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-black/40 backdrop-blur-lg border-t border-purple-500/20 py-12">
          <div className="container mx-auto px-6">
            <div className="text-center">
              <div className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-4">
                CryptoAnalytics
              </div>
              <p className="text-purple-300 mb-6">
                Анализ криптовалютных сигналов с помощью искусственного интеллекта
              </p>
              <div className="text-purple-400 text-sm">
                © 2025 CryptoAnalytics. Все права защищены. v2.0.{timestamp}
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
