import React from 'react';
import Head from 'next/head';
import { Login } from '@/components/auth';

const LoginPage: React.FC = () => {
  return (
    <>
      <Head>
        <title>Вход - Crypto Analytics Platform</title>
        <meta name="description" content="Войдите в свой аккаунт на платформе анализа криптовалютных сигналов" />
      </Head>
      
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Crypto Analytics Platform
            </h1>
            <p className="text-gray-600">
              Платформа анализа криптовалютных сигналов
            </p>
          </div>
        </div>
        
        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            <Login />
          </div>
        </div>
      </div>
    </>
  );
};

export default LoginPage; 