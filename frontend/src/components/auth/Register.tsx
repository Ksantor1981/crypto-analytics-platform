'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { RegisterRequest } from '@/types';

interface RegisterProps {
  onSuccess?: () => void;
}

export const Register: React.FC<RegisterProps> = ({ onSuccess }) => {
  const [formData, setFormData] = useState<RegisterRequest>({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
  });
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { register } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    // Validate passwords match
    if (formData.password !== confirmPassword) {
      setError('Пароли не совпадают');
      setIsLoading(false);
      return;
    }

    // Validate password strength
    if (formData.password.length < 8) {
      setError('Пароль должен содержать минимум 8 символов');
      setIsLoading(false);
      return;
    }

    try {
      // Проверяем, что все обязательные поля заполнены
      if (!formData.first_name || !formData.last_name) {
        setError('Пожалуйста, заполните все поля');
        setIsLoading(false);
        return;
      }
      
      await register({
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name
      });
      
      if (onSuccess) {
        onSuccess();
      } else {
        router.push('/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Ошибка регистрации');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <h2 className="text-2xl font-bold text-center text-gray-900">
          Регистрация
        </h2>
        <p className="text-center text-gray-600 mt-2">
          Создайте аккаунт для доступа к платформе
        </p>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Имя"
              type="text"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              placeholder="Ваше имя"
              required
              disabled={isLoading}
            />

            <Input
              label="Фамилия"
              type="text"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              placeholder="Ваша фамилия"
              required
              disabled={isLoading}
            />
          </div>

          <Input
            label="Email"
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="Введите ваш email"
            required
            disabled={isLoading}
          />

          <Input
            label="Пароль"
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Создайте пароль"
            required
            disabled={isLoading}
            helperText="Минимум 8 символов"
          />

          <Input
            label="Подтвердите пароль"
            type="password"
            name="confirmPassword"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            placeholder="Повторите пароль"
            required
            disabled={isLoading}
          />

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <Button
            type="submit"
            variant="default"
            size="lg"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? 'Регистрация...' : 'Зарегистрироваться'}
          </Button>
        </form>
      </CardContent>

      <CardFooter className="text-center">
        <p className="text-sm text-gray-600">
          Уже есть аккаунт?{' '}
          <Link
            href="/auth/login"
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            Войти
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
};
