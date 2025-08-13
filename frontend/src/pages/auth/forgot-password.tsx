import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
// import { useRouter } from 'next/router';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { TrendingUp, ArrowLeft, CheckCircle } from 'lucide-react';

export default function ForgotPasswordPage() {
  // const router = useRouter(); // не используется
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/users/forgot-password`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email }),
        }
      );

      if (response.ok) {
        setIsSuccess(true);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Ошибка при отправке запроса');
      }
    } catch (err) {
      setError('Ошибка сети. Попробуйте позже.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Восстановление пароля - CryptoAnalytics</title>
        <meta
          name="description"
          content="Восстановите доступ к вашему аккаунту CryptoAnalytics"
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
                Восстановление пароля
              </CardTitle>
              <CardDescription>
                Введите ваш email для получения ссылки на восстановление пароля
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
                      Письмо отправлено!
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Мы отправили инструкции по восстановлению пароля на адрес{' '}
                      <strong>{email}</strong>
                    </p>
                    <p className="text-sm text-gray-500 mb-6">
                      Если письмо не пришло в течение 5 минут, проверьте папку
                      "Спам" или попробуйте еще раз.
                    </p>
                  </div>
                  <div className="space-y-3">
                    <Button
                      onClick={() => {
                        setIsSuccess(false);
                        setEmail('');
                      }}
                      variant="outline"
                      className="w-full"
                    >
                      Отправить еще раз
                    </Button>
                    <Link href="/auth/login">
                      <Button variant="ghost" className="w-full">
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Вернуться к входу
                      </Button>
                    </Link>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  {error && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-3">
                      <p className="text-sm text-red-600">{error}</p>
                    </div>
                  )}

                  <div className="space-y-2">
                    <label
                      htmlFor="email"
                      className="text-sm font-medium text-gray-700"
                    >
                      Email адрес
                    </label>
                    <input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="your@email.com"
                      required
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full"
                    disabled={isLoading || !email}
                  >
                    {isLoading ? 'Отправляем...' : 'Отправить инструкции'}
                  </Button>

                  <div className="text-center space-y-2">
                    <Link href="/auth/login">
                      <Button variant="ghost" className="text-sm">
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Вернуться к входу
                      </Button>
                    </Link>
                  </div>
                </form>
              )}
            </CardContent>
          </Card>

          {/* Footer */}
          <div className="text-center mt-8">
            <p className="text-sm text-gray-500">
              Нет аккаунта?{' '}
              <Link
                href="/auth/register"
                className="font-medium text-blue-600 hover:text-blue-500"
              >
                Зарегистрироваться
              </Link>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}


