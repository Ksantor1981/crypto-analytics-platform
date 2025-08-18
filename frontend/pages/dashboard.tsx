import React from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function Dashboard() {
  const router = useRouter();

  return (
    <>
      <Head>
        <title>Дашборд - CryptoAnalytics</title>
        <meta name="description" content="Панель управления CryptoAnalytics" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <div className="text-2xl font-bold text-gray-900">
                  CryptoAnalytics
                </div>
              </div>
              
              <nav className="flex items-center space-x-4">
                <Button 
                  onClick={() => router.push('/')}
                  variant="outline"
                  className="border-gray-300 text-gray-700 hover:bg-gray-50"
                >
                  На главную
                </Button>
              </nav>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                Добро пожаловать в CryptoAnalytics!
              </h1>
              <p className="text-lg text-gray-600">
                Ваш аккаунт успешно создан. Здесь вы можете управлять своими настройками и аналитикой.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Quick Stats */}
              <Card className="border border-gray-200">
                <CardHeader>
                  <CardTitle className="text-gray-900">Активные каналы</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-blue-600">5</div>
                  <p className="text-gray-600">из 5 доступных</p>
                </CardContent>
              </Card>

              <Card className="border border-gray-200">
                <CardHeader>
                  <CardTitle className="text-gray-900">Точность прогнозов</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-green-600">87.2%</div>
                  <p className="text-gray-600">за последние 30 дней</p>
                </CardContent>
              </Card>

              <Card className="border border-gray-200">
                <CardHeader>
                  <CardTitle className="text-gray-900">API запросы</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-purple-600">1,247</div>
                  <p className="text-gray-600">в этом месяце</p>
                </CardContent>
              </Card>
            </div>

            <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recent Activity */}
              <Card className="border border-gray-200">
                <CardHeader>
                  <CardTitle className="text-gray-900">Последняя активность</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">Новый сигнал BTC</p>
                        <p className="text-xs text-gray-500">2 минуты назад</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">Обновление рейтинга ETH</p>
                        <p className="text-xs text-gray-500">15 минут назад</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">Новый канал добавлен</p>
                        <p className="text-xs text-gray-500">1 час назад</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Actions */}
              <Card className="border border-gray-200">
                <CardHeader>
                  <CardTitle className="text-gray-900">Быстрые действия</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <Button 
                      onClick={() => router.push('/channels')}
                      className="w-full justify-start bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      📊 Просмотреть каналы
                    </Button>
                    <Button 
                      onClick={() => router.push('/analytics')}
                      variant="outline"
                      className="w-full justify-start border-gray-300 text-gray-700 hover:bg-gray-50"
                    >
                      📈 Аналитика
                    </Button>
                    <Button 
                      onClick={() => router.push('/settings')}
                      variant="outline"
                      className="w-full justify-start border-gray-300 text-gray-700 hover:bg-gray-50"
                    >
                      ⚙️ Настройки
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="mt-8 text-center">
              <p className="text-gray-600 mb-4">
                Это демо-версия. В полной версии здесь будет полноценный дашборд с аналитикой.
              </p>
              <Button 
                onClick={() => router.push('/')}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                Вернуться на главную
              </Button>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
