import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LanguageProvider, useLanguage } from '@/contexts/LanguageContext';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

function HomeContent() {
  const router = useRouter();
  const { t } = useLanguage();

  return (
    <>
      <Head>
        <title>CryptoAnalytics - {t('hero.title')}</title>
        <meta name="description" content={t('hero.subtitle')} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-white">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <div className="text-2xl font-bold text-gray-900">
                  CryptoAnalytics
                </div>
              </div>
              
              <nav className="hidden md:flex items-center space-x-8">
                <a href="#features" className="text-gray-600 hover:text-gray-900 transition-colors">
                  {t('nav.features')}
                </a>
                <a href="#pricing" className="text-gray-600 hover:text-gray-900 transition-colors">
                  {t('nav.pricing')}
                </a>
                <LanguageSwitcher />
                <Button 
                  onClick={() => router.push('/auth/login')}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {t('nav.getStarted')}
                </Button>
              </nav>
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <section className="py-20 bg-gradient-to-br from-blue-50 to-indigo-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
                {t('hero.title')}
              </h1>
              
              <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
                {t('hero.subtitle')}
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
                <Button 
                  onClick={() => router.push('/auth/register')}
                  size="lg"
                  className="bg-blue-600 hover:bg-blue-700 text-white text-lg px-8 py-3"
                >
                  {t('hero.startTrial')}
                </Button>
                <Button 
                  onClick={() => router.push('/demo')}
                  variant="outline"
                  size="lg"
                  className="border-2 border-gray-300 text-gray-700 hover:bg-gray-50 text-lg px-8 py-3"
                >
                  {t('hero.viewDemo')}
                </Button>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600 mb-2">87.2%</div>
                  <div className="text-gray-600">{t('stats.accuracy')}</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600 mb-2">110+</div>
                  <div className="text-gray-600">{t('stats.features')}</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600 mb-2">&lt;0.3s</div>
                  <div className="text-gray-600">{t('stats.responseTime')}</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-20 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                {t('features.title')}
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                {t('features.subtitle')}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {/* Feature 1 */}
              <Card className="border border-gray-200 hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                    <span className="text-2xl">🤖</span>
                  </div>
                  <CardTitle className="text-gray-900">{t('features.ai.title')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    {t('features.ai.description')}
                  </p>
                </CardContent>
              </Card>

              {/* Feature 2 */}
              <Card className="border border-gray-200 hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                    <span className="text-2xl">📊</span>
                  </div>
                  <CardTitle className="text-gray-900">{t('features.realtime.title')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    {t('features.realtime.description')}
                  </p>
                </CardContent>
              </Card>

              {/* Feature 3 */}
              <Card className="border border-gray-200 hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                    <span className="text-2xl">🎯</span>
                  </div>
                  <CardTitle className="text-gray-900">{t('features.rating.title')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    {t('features.rating.description')}
                  </p>
                </CardContent>
              </Card>

              {/* Feature 4 */}
              <Card className="border border-gray-200 hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                    <span className="text-2xl">⚡</span>
                  </div>
                  <CardTitle className="text-gray-900">{t('features.performance.title')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    {t('features.performance.description')}
                  </p>
                </CardContent>
              </Card>

              {/* Feature 5 */}
              <Card className="border border-gray-200 hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                    <span className="text-2xl">🔒</span>
                  </div>
                  <CardTitle className="text-gray-900">{t('features.security.title')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    {t('features.security.description')}
                  </p>
                </CardContent>
              </Card>

              {/* Feature 6 */}
              <Card className="border border-gray-200 hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                    <span className="text-2xl">🚀</span>
                  </div>
                  <CardTitle className="text-gray-900">{t('features.autotrading.title')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    {t('features.autotrading.description')}
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="py-20 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                {t('pricing.title')}
              </h2>
              <p className="text-lg text-gray-600">
                {t('pricing.subtitle')}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              {/* Free Plan */}
              <Card className="border border-gray-200 bg-white">
                <CardHeader>
                  <CardTitle className="text-gray-900">{t('pricing.free.title')}</CardTitle>
                  <div className="text-4xl font-bold text-gray-900">
                    $0<span className="text-lg text-gray-500">/mo</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3 mb-8">
                    <li className="flex items-center text-gray-600">
                      <span className="text-green-500 mr-3">✓</span>
                      5 {t('pricing.channels')}
                    </li>
                    <li className="flex items-center text-gray-600">
                      <span className="text-green-500 mr-3">✓</span>
                      {t('pricing.basicAnalytics')}
                    </li>
                    <li className="flex items-center text-gray-600">
                      <span className="text-green-500 mr-3">✓</span>
                      {t('pricing.emailSupport')}
                    </li>
                  </ul>
                  <Button className="w-full bg-gray-600 hover:bg-gray-700 text-white">
                    {t('pricing.startFree')}
                  </Button>
                </CardContent>
              </Card>

              {/* Pro Plan */}
              <Card className="border-2 border-blue-500 bg-white relative">
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-blue-500 text-white px-6 py-2 rounded-full text-sm font-semibold">
                  {t('pricing.popular')}
                </div>
                <CardHeader>
                  <CardTitle className="text-gray-900">{t('pricing.pro.title')}</CardTitle>
                  <div className="text-4xl font-bold text-gray-900">
                    $29<span className="text-lg text-gray-500">/mo</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3 mb-8">
                    <li className="flex items-center text-gray-600">
                      <span className="text-green-500 mr-3">✓</span>
                      50 {t('pricing.channels')}
                    </li>
                    <li className="flex items-center text-gray-600">
                      <span className="text-green-500 mr-3">✓</span>
                      {t('pricing.advancedAnalytics')}
                    </li>
                    <li className="flex items-center text-gray-600">
                      <span className="text-green-500 mr-3">✓</span>
                      {t('pricing.mlPredictions')}
                    </li>
                    <li className="flex items-center text-gray-600">
                      <span className="text-green-500 mr-3">✓</span>
                      {t('pricing.prioritySupport')}
                    </li>
                  </ul>
                  <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                    {t('pricing.choosePro')}
                  </Button>
                </CardContent>
              </Card>

              {/* Enterprise Plan */}
              <Card className="border border-gray-200 bg-white">
                <CardHeader>
                  <CardTitle className="text-gray-900">{t('pricing.enterprise.title')}</CardTitle>
                  <div className="text-4xl font-bold text-gray-900">
                    $99<span className="text-lg text-gray-500">/mo</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3 mb-8">
                    <li className="flex items-center text-gray-600">
                      <span className="text-green-500 mr-3">✓</span>
                      {t('pricing.unlimitedChannels')}
                    </li>
                    <li className="flex items-center text-gray-600">
                      <span className="text-green-500 mr-3">✓</span>
                      {t('pricing.apiAccess')}
                    </li>
                    <li className="flex items-center text-gray-600">
                      <span className="text-green-500 mr-3">✓</span>
                      {t('pricing.personalManager')}
                    </li>
                    <li className="flex items-center text-gray-600">
                      <span className="text-green-500 mr-3">✓</span>
                      {t('pricing.sla')}
                    </li>
                  </ul>
                  <Button className="w-full bg-gray-600 hover:bg-gray-700 text-white">
                    {t('pricing.contactUs')}
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-gray-900 text-white py-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <div className="text-2xl font-bold mb-4">
                CryptoAnalytics
              </div>
              <p className="text-gray-300 mb-6">
                {t('footer.description')}
              </p>
              <div className="text-gray-400 text-sm">
                {t('footer.rights')}
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}

export default function Home() {
  return (
    <LanguageProvider>
      <HomeContent />
    </LanguageProvider>
  );
}
