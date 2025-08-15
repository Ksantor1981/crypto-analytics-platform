import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { TrendingUp, Eye, EyeOff, CheckCircle, XCircle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    agreeToTerms: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const passwordRequirements = [
    { text: 'Минимум 8 символов', met: formData.password.length >= 8 },
    { text: 'Содержит цифру', met: /\d/.test(formData.password) },
    { text: 'Содержит заглавную букву', met: /[A-Z]/.test(formData.password) },
    { text: 'Содержит строчную букву', met: /[a-z]/.test(formData.password) },
  ];

  const isPasswordValid = passwordRequirements.every(req => req.met);
  const passwordsMatch =
    formData.password === formData.confirmPassword &&
    formData.confirmPassword !== '';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    if (!isPasswordValid) {
      setError('Пароль не соответствует требованиям');
      setIsLoading(false);
      return;
    }

    if (!passwordsMatch) {
      setError('Пароли не совпадают');
      setIsLoading(false);
      return;
    }

    if (!formData.agreeToTerms) {
      setError('Необходимо согласиться с условиями использования');
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/users/register`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: formData.email,
            password: formData.password,
            first_name: formData.firstName,
            last_name: formData.lastName,
          }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        // Автоматически входим после регистрации
        await login(formData.email, formData.password);
        router.push('/dashboard');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Ошибка регистрации. Возможно, пользователь с таким email уже существует.');
      }
    } catch (err) {
      setError('Ошибка подключения к серверу. Попробуйте позже.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  return (
    <>
      <Head>
        <title>Регистрация - CryptoAnalytics</title>
        <meta
          name="description"
          content="Создайте аккаунт в CryptoAnalytics для доступа к рейтингам каналов"
        />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="text-center mb-8">
            <Link href="/" className="inline-flex items-center">
              <TrendingUp className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-2xl font-bold gradient-text">
                CryptoAnalytics
              </span>
            </Link>
          </div>

          <Card className="card-hover">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Создать аккаунт</CardTitle>
              <CardDescription>
                Присоединяйтесь к сотням трейдеров, которые экономят на торговле
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                    {error}
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label
                      htmlFor="firstName"
                      className="block text-sm font-medium text-gray-700 mb-2"
                    >
                      Имя
                    </label>
                    <input
                      id="firstName"
                      name="firstName"
                      type="text"
                      required
                      value={formData.firstName}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Иван"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="lastName"
                      className="block text-sm font-medium text-gray-700 mb-2"
                    >
                      Фамилия
                    </label>
                    <input
                      id="lastName"
                      name="lastName"
                      type="text"
                      required
                      value={formData.lastName}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Иванов"
                    />
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="email"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Email
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="your@email.com"
                  />
                </div>

                <div>
                  <label
                    htmlFor="password"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Пароль
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      required
                      value={formData.password}
                      onChange={handleChange}
                      className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Создайте надежный пароль"
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 px-3 flex items-center"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? (
                        <EyeOff className="h-5 w-5 text-gray-400" />
                      ) : (
                        <Eye className="h-5 w-5 text-gray-400" />
                      )}
                    </button>
                  </div>

                  {/* Password requirements */}
                  {formData.password && (
                    <div className="mt-2 space-y-1">
                      {passwordRequirements.map((req, index) => (
                        <div key={index} className="flex items-center text-xs">
                          {req.met ? (
                            <CheckCircle className="h-3 w-3 text-green-500 mr-2" />
                          ) : (
                            <XCircle className="h-3 w-3 text-red-500 mr-2" />
                          )}
                          <span
                            className={
                              req.met ? 'text-green-700' : 'text-red-700'
                            }
                          >
                            {req.text}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="confirmPassword"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Подтвердите пароль
                  </label>
                  <div className="relative">
                    <input
                      id="confirmPassword"
                      name="confirmPassword"
                      type={showConfirmPassword ? 'text' : 'password'}
                      required
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      className={`w-full px-3 py-2 pr-10 border rounded-md shadow-sm focus:outline-none focus:ring-2 ${
                        formData.confirmPassword && passwordsMatch
                          ? 'border-green-300 focus:ring-green-500 focus:border-green-500'
                          : formData.confirmPassword && !passwordsMatch
                            ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                            : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
                      }`}
                      placeholder="Повторите пароль"
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 px-3 flex items-center"
                      onClick={() =>
                        setShowConfirmPassword(!showConfirmPassword)
                      }
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="h-5 w-5 text-gray-400" />
                      ) : (
                        <Eye className="h-5 w-5 text-gray-400" />
                      )}
                    </button>
                  </div>

                  {formData.confirmPassword && !passwordsMatch && (
                    <p className="mt-1 text-xs text-red-600">
                      Пароли не совпадают
                    </p>
                  )}
                </div>

                <div className="flex items-start">
                  <input
                    id="agreeToTerms"
                    name="agreeToTerms"
                    type="checkbox"
                    required
                    checked={formData.agreeToTerms}
                    onChange={handleChange}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mt-0.5"
                  />
                  <label
                    htmlFor="agreeToTerms"
                    className="ml-2 block text-sm text-gray-700"
                  >
                    Я согласен с{' '}
                    <Link
                      href="/terms"
                      className="text-blue-600 hover:text-blue-500"
                    >
                      условиями использования
                    </Link>{' '}
                    и{' '}
                    <Link
                      href="/privacy"
                      className="text-blue-600 hover:text-blue-500"
                    >
                      политикой конфиденциальности
                    </Link>
                  </label>
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={
                    isLoading ||
                    !isPasswordValid ||
                    !passwordsMatch ||
                    !formData.agreeToTerms
                  }
                >
                  {isLoading ? 'Создание аккаунта...' : 'Создать аккаунт'}
                </Button>
              </form>

              <div className="mt-6 text-center">
                <p className="text-sm text-gray-600">
                  Уже есть аккаунт?{' '}
                  <Link
                    href="/auth/login"
                    className="text-blue-600 hover:text-blue-500 font-medium"
                  >
                    Войти
                  </Link>
                </p>
              </div>

              {/* Free plan highlight */}
              <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md">
                <h4 className="text-sm font-medium text-green-800 mb-2">
                  🎉 Бесплатный старт:
                </h4>
                <ul className="text-xs text-green-700 space-y-1">
                  <li>• До 3 каналов для отслеживания</li>
                  <li>• Топ-10 рейтинга каналов</li>
                  <li>• Полный доступ к антирейтингу</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          <div className="mt-8 text-center text-sm text-gray-500">
            <Link href="/" className="hover:text-gray-700">
              ← Вернуться на главную
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}


