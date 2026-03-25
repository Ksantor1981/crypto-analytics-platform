import Head from 'next/head';
import Link from 'next/link';
import { AlertTriangle } from 'lucide-react';

import { Button } from '@/components/ui/button';

export default function Custom404() {
  return (
    <>
      <Head>
        <title>404 - Страница не найдена</title>
      </Head>
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center">
          <AlertTriangle className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
          <h1 className="text-6xl font-bold text-gray-900 mb-2">404</h1>
          <p className="text-xl text-gray-600 mb-6">Страница не найдена</p>
          <p className="text-gray-500 mb-8">
            Возможно, она была перемещена или удалена.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/">
              <Button>На главную</Button>
            </Link>
            <Link href="/dashboard">
              <Button variant="outline">В панель</Button>
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}
