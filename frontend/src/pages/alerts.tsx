import { NextPage } from 'next';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import AlertSystem from '@/components/notifications/AlertSystem';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Bell, AlertTriangle, TrendingUp, Settings } from 'lucide-react';

const AlertsPage: NextPage = () => {
  return (
    <DashboardLayout title="Алерты и уведомления">
      <div className="space-y-6">
        {/* Заголовок страницы */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <Bell className="h-8 w-8 text-blue-600 mr-3" />
                Система алертов
              </h1>
              <p className="text-gray-600 mt-2">
                Настройте уведомления для получения важной информации о рынке и
                ваших сигналах
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <div className="text-right">
                <div className="text-sm text-gray-500">Статус системы</div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium text-green-600">
                    Активна
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Быстрая статистика */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Bell className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">
                    Активных алертов
                  </p>
                  <p className="text-2xl font-bold text-gray-900">12</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <AlertTriangle className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">
                    Сработало сегодня
                  </p>
                  <p className="text-2xl font-bold text-gray-900">5</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <TrendingUp className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">
                    Успешных алертов
                  </p>
                  <p className="text-2xl font-bold text-gray-900">89%</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Settings className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">
                    Настроенных
                  </p>
                  <p className="text-2xl font-bold text-gray-900">18</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Компонент системы алертов */}
        <AlertSystem />

        {/* Информация и помощь */}
        <Card>
          <CardHeader>
            <CardTitle>💡 Советы по использованию алертов</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">
                  Ценовые алерты
                </h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>
                    • Устанавливайте алерты на ключевых уровнях
                    поддержки/сопротивления
                  </li>
                  <li>
                    • Используйте алерты для фиксации прибыли на целевых уровнях
                  </li>
                  <li>
                    • Настраивайте уведомления о приближении к стоп-лоссам
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">
                  Сигнальные алерты
                </h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>
                    • Фильтруйте сигналы по уровню уверенности (confidence)
                  </li>
                  <li>• Получайте уведомления только от проверенных каналов</li>
                  <li>• Настройте алерты на определенные криптопары</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default AlertsPage;

