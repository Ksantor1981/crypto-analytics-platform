import Head from 'next/head';
import Link from 'next/link';
import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Custom500() {
  return (
    <>
      <Head><title>500 - Ошибка сервера</title></Head>
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center">
          <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-6xl font-bold text-gray-900 mb-2">500</h1>
          <p className="text-xl text-gray-600 mb-6">Внутренняя ошибка сервера</p>
          <p className="text-gray-500 mb-8">Мы уже работаем над устранением. Попробуйте позже.</p>
          <div className="flex gap-4 justify-center">
            <Link href="/"><Button>На главную</Button></Link>
            <Button variant="outline" onClick={() => window.location.reload()}>Обновить</Button>
          </div>
        </div>
      </div>
    </>
  );
}
