import { useState, useEffect } from 'react';
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

export default function ResetPasswordPage() {
  const router = useRouter();
  const { token } = router.query;
  
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);

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

  useEffect(() => {
    if (!token) {
      setError('Недействительная ссылка для сброса пароля');
    }
  }, [token]);

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

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/users/reset-password`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            token,
            new_password: formData.password,
          }),
        }
      );

      if (response.ok) {
        setIsSuccess(true);
        setTimeout(() => {
          router.push('/auth/login');
        }, 3000);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Ошибка при сбросе пароля');
      }
    } catch (err) {
      setError('Ошибка сети. Попробуйте позже.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <>
        <Head>
          <title>Сброс пароля - CryptoAnalytics</title>
        </Head>
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardContent className="pt-6 text-center">
              <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Недействительная ссылка
              </h3>
              <p className="text-gray-600 mb-4">
                Ссылка для сброса пароля недействительна или истекла.
              </p>
              <Link href="/auth/forgot-password">
                <Button>Запросить новую ссылку</Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </>
    );
  }

  return (
    <>
      <Head>
        <title>Сброс пароля - CryptoAnalytics</title>
        <meta
          name="description"
          content="Установите новый пароль для вашего аккаунта CryptoAnalytics"
        />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          {/* Header */}
          <div className="text-center mb-8">
            <Link href="/" className="inline-flex items-center space-x-2 mb-6">
              <TrendingUp className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">
                CryptoAnalytics
              </span>
            </Link>
          </div>

          <Card className="shadow-xl border-0">
            <CardHeader className="space-y-1 text-center">
              <CardTitle className="text-2xl font-bold">
                Установить новый пароль
              </CardTitle>
              <CardDescription>
                Введите новый пароль для вашего аккаунта
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isSuccess ? (
                <div className="text-center space-y-4">
                  <div className="flex justify-center">
                    <CheckCircle className="h-16 w-16 text-green-500" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      Пароль успешно изменен!
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Ваш пароль был успешно обновлен. Вы будете перенаправлены
                      на страницу входа через несколько секунд.
                    </p>
                  </div>
                  <Link href="/auth/login">
                    <Button className="w-full">Войти в аккаунт</Button>
                  </Link>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  {error && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-3">
                      <p className="text-sm text-red-600">{error}</p>
                    </div>
                  )}

                  {/* Password */}
                  <div className="space-y-2">
                    <label
                      htmlFor="password"
                      className="text-sm font-medium text-gray-700"
                    >
                      Новый пароль
                    </label>
                    <div className="relative">
                      <input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        value={formData.password}
                        onChange={(e) =>
                          setFormData({ ...formData, password: e.target.value })
                        }
                        className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Введите новый пароль"
                        required
                      />
                      <button
                        type="button"
                        className="absolute inset-y-0 right-0 pr-3 flex items-center"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4 text-gray-400" />
                        ) : (
                          <Eye className="h-4 w-4 text-gray-400" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Password Requirements */}
                  {formData.password && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-gray-700">
                        Требования к паролю:
                      </p>
                      <div className="space-y-1">
                        {passwordRequirements.map((req, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            {req.met ? (
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            ) : (
                              <XCircle className="h-4 w-4 text-red-500" />
                            )}
                            <span
                              className={`text-sm ${
                                req.met ? 'text-green-700' : 'text-red-700'
                              }`}
                            >
                              {req.text}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Confirm Password */}
                  <div className="space-y-2">
                    <label
                      htmlFor="confirmPassword"
                      className="text-sm font-medium text-gray-700"
                    >
                      Подтвердите пароль
                    </label>
                    <div className="relative">
                      <input
                        id="confirmPassword"
                        type={showConfirmPassword ? 'text' : 'password'}
                        value={formData.confirmPassword}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            confirmPassword: e.target.value,
                          })
                        }
                        className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Повторите пароль"
                        required
                      />
                      <button
                        type="button"
                        className="absolute inset-y-0 right-0 pr-3 flex items-center"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      >
                        {showConfirmPassword ? (
                          <EyeOff className="h-4 w-4 text-gray-400" />
                        ) : (
                          <Eye className="h-4 w-4 text-gray-400" />
                        )}
                      </button>
                    </div>
                    {formData.confirmPassword && (
                      <div className="flex items-center space-x-2">
                        {passwordsMatch ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500" />
                        )}
                        <span
                          className={`text-sm ${
                            passwordsMatch ? 'text-green-700' : 'text-red-700'
                          }`}
                        >
                          {passwordsMatch ? 'Пароли совпадают' : 'Пароли не совпадают'}
                        </span>
                      </div>
                    )}
                  </div>

                  <Button
                    type="submit"
                    className="w-full"
                    disabled={isLoading || !isPasswordValid || !passwordsMatch}
                  >
                    {isLoading ? 'Обновляем пароль...' : 'Обновить пароль'}
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>

          {/* Footer */}
          <div className="text-center mt-8">
            <Link
              href="/auth/login"
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              ← Вернуться к входу
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}


