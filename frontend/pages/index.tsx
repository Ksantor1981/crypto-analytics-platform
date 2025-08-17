import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function Home() {
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
        {/* Header */}
        <header className="relative z-50 bg-black/20 backdrop-blur-xl border-b border-purple-500/20">
          <div className="container mx-auto px-6 py-4">
            <nav className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  CryptoAnalytics
                </div>
                <span className="text-xs text-purple-300 bg-purple-500/20 px-2 py-1 rounded">
                  v3.0.{timestamp}
                </span>
              </div>
              
              <div className="hidden md:flex items-center space-x-8">
                <a href="#features" className="text-purple-200 hover:text-purple-400 transition-colors">
                  Features
                </a>
                <a href="#pricing" className="text-purple-200 hover:text-purple-400 transition-colors">
                  Pricing
                </a>
                <Button 
                  onClick={() => router.push('/auth/login')}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                >
                  Get Started
                </Button>
              </div>
            </nav>
          </div>
        </header>

        {/* Hero Section */}
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
                Analyze cryptocurrency signals with machine learning. 
                87.2% prediction accuracy for maximum profit.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
                <Button 
                  onClick={() => router.push('/auth/register')}
                  size="lg"
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-lg px-8 py-4"
                >
                  Start Free Trial
                </Button>
                <Button 
                  onClick={() => router.push('/demo')}
                  variant="outline"
                  size="lg"
                  className="border-2 border-purple-400 text-purple-300 hover:bg-purple-400/10 text-lg px-8 py-4"
                >
                  View Demo
                </Button>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
                <Card className="bg-white/5 backdrop-blur-lg border-purple-500/20">
                  <CardContent className="p-6">
                    <div className="text-3xl font-bold text-purple-400 mb-2">87.2%</div>
                    <div className="text-purple-200">ML Model Accuracy</div>
                  </CardContent>
                </Card>
                <Card className="bg-white/5 backdrop-blur-lg border-purple-500/20">
                  <CardContent className="p-6">
                    <div className="text-3xl font-bold text-pink-400 mb-2">110+</div>
                    <div className="text-purple-200">Analytical Features</div>
                  </CardContent>
                </Card>
                <Card className="bg-white/5 backdrop-blur-lg border-purple-500/20">
                  <CardContent className="p-6">
                    <div className="text-3xl font-bold text-purple-400 mb-2">&lt;0.3s</div>
                    <div className="text-purple-200">API Response Time</div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-20 bg-black/20">
          <div className="container mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                Platform Features
              </h2>
              <p className="text-purple-200 text-lg max-w-2xl mx-auto">
                Harness the power of artificial intelligence for cryptocurrency signal analysis
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {/* Feature 1 */}
              <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-lg border-purple-500/20 hover:border-purple-400/40 transition-all">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-4">
                    <span className="text-2xl">🤖</span>
                  </div>
                  <CardTitle className="text-white">AI Signal Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-purple-200">
                    Ensemble machine learning models analyze signals with 87.2% accuracy
                  </p>
                </CardContent>
              </Card>

              {/* Feature 2 */}
              <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-lg border-purple-500/20 hover:border-purple-400/40 transition-all">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-4">
                    <span className="text-2xl">📊</span>
                  </div>
                  <CardTitle className="text-white">Real-time Data</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-purple-200">
                    Live data from Binance and Bybit exchanges in real-time
                  </p>
                </CardContent>
              </Card>

              {/* Feature 3 */}
              <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-lg border-purple-500/20 hover:border-purple-400/40 transition-all">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-4">
                    <span className="text-2xl">🎯</span>
                  </div>
                  <CardTitle className="text-white">Channel Rating</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-purple-200">
                    Innovative system for evaluating cryptocurrency channel quality
                  </p>
                </CardContent>
              </Card>

              {/* Feature 4 */}
              <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-lg border-purple-500/20 hover:border-purple-400/40 transition-all">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-4">
                    <span className="text-2xl">⚡</span>
                  </div>
                  <CardTitle className="text-white">High Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-purple-200">
                    API responds in less than 0.3 seconds, 99.9% uptime
                  </p>
                </CardContent>
              </Card>

              {/* Feature 5 */}
              <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-lg border-purple-500/20 hover:border-purple-400/40 transition-all">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-4">
                    <span className="text-2xl">🔒</span>
                  </div>
                  <CardTitle className="text-white">Security</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-purple-200">
                    JWT authentication, RBAC system, DDoS protection
                  </p>
                </CardContent>
              </Card>

              {/* Feature 6 */}
              <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-lg border-purple-500/20 hover:border-purple-400/40 transition-all">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mb-4">
                    <span className="text-2xl">🚀</span>
                  </div>
                  <CardTitle className="text-white">Auto-trading (Coming Soon)</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-purple-200">
                    Automated trading based on AI signal analysis
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="py-20">
          <div className="container mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                Pricing Plans
              </h2>
              <p className="text-purple-200 text-lg">
                Choose the plan that fits your needs
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              {/* Free Plan */}
              <Card className="bg-white/5 backdrop-blur-lg border-purple-500/20">
                <CardHeader>
                  <CardTitle className="text-white">Free</CardTitle>
                  <div className="text-4xl font-bold text-purple-400">
                    $0<span className="text-lg text-purple-200">/mo</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3 mb-8">
                    <li className="flex items-center text-purple-200">
                      <span className="text-green-400 mr-3">✓</span>
                      5 channels
                    </li>
                    <li className="flex items-center text-purple-200">
                      <span className="text-green-400 mr-3">✓</span>
                      Basic analytics
                    </li>
                    <li className="flex items-center text-purple-200">
                      <span className="text-green-400 mr-3">✓</span>
                      Email support
                    </li>
                  </ul>
                  <Button className="w-full bg-purple-600 hover:bg-purple-700">
                    Start Free
                  </Button>
                </CardContent>
              </Card>

              {/* Pro Plan */}
              <Card className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-lg border-2 border-purple-400 relative">
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-2 rounded-full text-sm font-semibold">
                  Popular
                </div>
                <CardHeader>
                  <CardTitle className="text-white">Pro</CardTitle>
                  <div className="text-4xl font-bold text-purple-400">
                    $29<span className="text-lg text-purple-200">/mo</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3 mb-8">
                    <li className="flex items-center text-purple-200">
                      <span className="text-green-400 mr-3">✓</span>
                      50 channels
                    </li>
                    <li className="flex items-center text-purple-200">
                      <span className="text-green-400 mr-3">✓</span>
                      Advanced analytics
                    </li>
                    <li className="flex items-center text-purple-200">
                      <span className="text-green-400 mr-3">✓</span>
                      ML predictions
                    </li>
                    <li className="flex items-center text-purple-200">
                      <span className="text-green-400 mr-3">✓</span>
                      Priority support
                    </li>
                  </ul>
                  <Button className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600">
                    Choose Pro
                  </Button>
                </CardContent>
              </Card>

              {/* Enterprise Plan */}
              <Card className="bg-white/5 backdrop-blur-lg border-purple-500/20">
                <CardHeader>
                  <CardTitle className="text-white">Enterprise</CardTitle>
                  <div className="text-4xl font-bold text-purple-400">
                    $99<span className="text-lg text-purple-200">/mo</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3 mb-8">
                    <li className="flex items-center text-purple-200">
                      <span className="text-green-400 mr-3">✓</span>
                      Unlimited channels
                    </li>
                    <li className="flex items-center text-purple-200">
                      <span className="text-green-400 mr-3">✓</span>
                      API access
                    </li>
                    <li className="flex items-center text-purple-200">
                      <span className="text-green-400 mr-3">✓</span>
                      Personal manager
                    </li>
                    <li className="flex items-center text-purple-200">
                      <span className="text-green-400 mr-3">✓</span>
                      99.9% SLA
                    </li>
                  </ul>
                  <Button className="w-full bg-purple-600 hover:bg-purple-700">
                    Contact Us
                  </Button>
                </CardContent>
              </Card>
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
                Cryptocurrency signal analysis with artificial intelligence
              </p>
              <div className="text-purple-400 text-sm">
                © 2025 CryptoAnalytics. All rights reserved. v3.0.{timestamp}
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
