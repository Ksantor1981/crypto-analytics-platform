import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  TrendingUp,
  Shield,
  Zap,
  Users,
  BarChart3,
  Star,
  CheckCircle,
  ArrowRight,
  Target,
  Brain,
  AlertCircle,
} from 'lucide-react';

export default function LandingPage() {
  const [activeFeature, setActiveFeature] = useState(0);

  const features = [
    {
      icon: <BarChart3 className="h-8 w-8 text-blue-600" />,
      title: 'Реальные рейтинги каналов',
      description:
        'Точность 87.2% на основе фактических результатов торговых сигналов',
      stats: '10,000+ проверенных сигналов',
    },
    {
      icon: <Brain className="h-8 w-8 text-purple-600" />,
      title: 'ML-прогнозирование',
      description:
        'Ensemble модель анализирует 110+ факторов для предсказания успешности сигналов',
      stats: 'Ensemble из 3 моделей',
    },
    {
      icon: <AlertCircle className="h-8 w-8 text-red-600" />,
      title: 'Антирейтинг худших каналов',
      description: 'Уникальная фича: список каналов, которых стоит избегать',
      stats: 'Сэкономьте 40% потерь',
    },
  ];

  const pricing = [
    {
      name: 'Free',
      price: '0₽',
      period: '/месяц',
      description: 'Для новичков',
      features: [
        'До 3 каналов для отслеживания',
        'Топ-10 рейтинга каналов',
        'Полный доступ к антирейтингу',
        'Базовая аналитика',
      ],
      cta: 'Начать бесплатно',
      highlight: false,
    },
    {
      name: 'Premium',
      price: '990₽',
      period: '/месяц',
      description: 'Для активных трейдеров',
      features: [
        'Безлимитное количество каналов',
        'Полный доступ ко всем рейтингам',
        'Email уведомления о сигналах',
        'Excel/CSV экспорт данных',
        'Продвинутая аналитика',
      ],
      cta: 'Попробовать Premium',
      highlight: true,
    },
    {
      name: 'Pro',
      price: '2,990₽',
      period: '/месяц',
      description: 'Для профессионалов',
      features: [
        'Все функции Premium',
        'API доступ',
        'ML прогнозы в реальном времени',
        'Кастомные алерты и webhook',
        'Приоритетная поддержка',
      ],
      cta: 'Связаться с нами',
      highlight: false,
    },
  ];

  const testimonials = [
    {
      name: 'Алексей К.',
      role: 'Частный трейдер',
      text: 'За 3 месяца использования сэкономил более 50к рублей, избегая плохих каналов',
      rating: 5,
    },
    {
      name: 'Мария С.',
      role: 'Криптоинвестор',
      text: 'Наконец-то есть инструмент для объективной оценки telegram каналов!',
      rating: 5,
    },
    {
      name: 'Дмитрий Р.',
      role: 'Трейдер',
      text: 'Антирейтинг — это гениально! Теперь знаю, каких каналов избегать',
      rating: 5,
    },
  ];

  return (
    <>
      <Head>
        <title>CryptoAnalytics - Рейтинг криптовалютных каналов</title>
        <meta
          name="description"
          content="Объективные рейтинги Telegram каналов с торговыми сигналами. Точность 87.2% на основе ML анализа."
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <div className="flex-shrink-0 flex items-center">
                  <TrendingUp className="h-8 w-8 text-blue-600" />
                  <span className="ml-2 text-xl font-bold gradient-text">
                    CryptoAnalytics
                  </span>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <Link href="/auth/login">
                  <Button variant="ghost">Войти</Button>
                </Link>
                <Link href="/auth/register">
                  <Button>Регистрация</Button>
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Перестаньте терять деньги на
              <span className="gradient-text"> плохих сигналах</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Первая платформа с объективными рейтингами Telegram каналов на
              основе реальных результатов торговли. ML анализ с точностью 87.2%
              поможет выбрать лучшие каналы и избежать худших.
            </p>
            <div className="flex justify-center space-x-4 mb-12">
              <Link href="/auth/register">
                <Button size="lg" className="text-lg px-8 py-4">
                  Начать бесплатно
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link href="/demo">
                <Button
                  variant="outline"
                  size="lg"
                  className="text-lg px-8 py-4"
                >
                  Посмотреть демо
                </Button>
              </Link>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">10,000+</div>
                <div className="text-gray-600">Проанализированных сигналов</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600">87.2%</div>
                <div className="text-gray-600">Точность прогнозов</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">500+</div>
                <div className="text-gray-600">Отслеживаемых каналов</div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Почему CryptoAnalytics?
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Мы анализируем каждый сигнал, отслеживаем реальные результаты и
                даем вам честную оценку
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <Card
                  key={index}
                  className={`cursor-pointer transition-all duration-300 card-hover ${
                    activeFeature === index
                      ? 'ring-2 ring-blue-500 shadow-lg'
                      : ''
                  }`}
                  onClick={() => setActiveFeature(index)}
                >
                  <CardHeader>
                    <div className="flex items-center space-x-3">
                      {feature.icon}
                      <CardTitle className="text-xl">{feature.title}</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-base mb-3">
                      {feature.description}
                    </CardDescription>
                    <div className="text-sm font-semibold text-blue-600">
                      {feature.stats}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Social Proof */}
        <section className="py-20 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Отзывы пользователей
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {testimonials.map((testimonial, index) => (
                <Card key={index} className="card-hover">
                  <CardContent className="pt-6">
                    <div className="flex mb-4">
                      {[...Array(testimonial.rating)].map((_, i) => (
                        <Star
                          key={i}
                          className="h-5 w-5 text-yellow-400 fill-current"
                        />
                      ))}
                    </div>
                    <p className="text-gray-600 mb-4 italic">
                      "{testimonial.text}"
                    </p>
                    <div>
                      <div className="font-semibold text-gray-900">
                        {testimonial.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {testimonial.role}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Pricing */}
        <section className="py-20 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Выберите подходящий план
              </h2>
              <p className="text-xl text-gray-600">
                Начните бесплатно и обновляйтесь по мере роста потребностей
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {pricing.map((plan, index) => (
                <Card
                  key={index}
                  className={`relative ${plan.highlight ? 'ring-2 ring-blue-500 scale-105' : ''}`}
                >
                  {plan.highlight && (
                    <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                      <span className="bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-semibold">
                        Популярный
                      </span>
                    </div>
                  )}
                  <CardHeader className="text-center">
                    <CardTitle className="text-2xl">{plan.name}</CardTitle>
                    <div className="mt-4">
                      <span className="text-4xl font-bold">{plan.price}</span>
                      <span className="text-gray-500">{plan.period}</span>
                    </div>
                    <CardDescription>{plan.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3 mb-6">
                      {plan.features.map((feature, featureIndex) => (
                        <li key={featureIndex} className="flex items-center">
                          <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                          <span className="text-gray-600">{feature}</span>
                        </li>
                      ))}
                    </ul>
                    <Button
                      className="w-full"
                      variant={plan.highlight ? 'default' : 'outline'}
                    >
                      {plan.cta}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 bg-gradient-to-r from-blue-600 to-purple-600">
          <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
            <h2 className="text-4xl font-bold text-white mb-4">
              Готовы перестать терять деньги?
            </h2>
            <p className="text-xl text-blue-100 mb-8">
              Присоединяйтесь к сотням трейдеров, которые уже экономят с
              CryptoAnalytics
            </p>
            <Link href="/auth/register">
              <Button
                size="lg"
                variant="secondary"
                className="text-lg px-8 py-4"
              >
                Начать бесплатно сейчас
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-gray-900 py-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-center">
              <TrendingUp className="h-8 w-8 text-blue-400" />
              <span className="ml-2 text-xl font-bold text-white">
                CryptoAnalytics
              </span>
            </div>
            <div className="mt-8 text-center text-gray-400">
              <p>&copy; 2025 CryptoAnalytics. Все права защищены.</p>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}


