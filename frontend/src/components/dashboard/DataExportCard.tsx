'use client';

import { useState } from 'react';
import { Download, FileSpreadsheet, FileJson, Crown } from 'lucide-react';
import Link from 'next/link';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api';

function planAllowsPremiumExport(plan?: string): boolean {
  const p = (plan || 'free').toLowerCase();
  return p === 'premium' || p === 'pro';
}

interface DataExportCardProps {
  /** План из AuthContext: Free | Premium | Pro */
  subscriptionPlan?: string;
  isAuthenticated: boolean;
}

export function DataExportCard({
  subscriptionPlan,
  isAuthenticated,
}: DataExportCardProps) {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const premium = planAllowsPremiumExport(subscriptionPlan);

  const run = async (key: string, fn: () => Promise<void>) => {
    setError(null);
    setLoading(key);
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка экспорта');
    } finally {
      setLoading(null);
    }
  };

  if (!isAuthenticated) {
    return (
      <Card className="mb-8 border-dashed">
        <CardHeader>
          <CardTitle className="text-lg">Экспорт данных</CardTitle>
          <CardDescription>
            Войдите, чтобы скачать CSV сигналов или оформить Premium для полного
            экспорта.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" asChild>
            <Link href="/auth/login">Войти</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mb-8 border-gray-200">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Download className="h-5 w-5 text-blue-600" />
          <CardTitle className="text-lg">Экспорт данных</CardTitle>
        </div>
        <CardDescription>
          <strong>CSV (снимок)</strong> — до 1000 последних сигналов для всех
          авторизованных. <strong>Premium+</strong> — свои каналы / сигналы /
          аналитика в CSV, Excel и JSON.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-md p-2">
            {error}
          </p>
        )}

        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">
            Быстрый CSV (все сигналы платформы, снимок)
          </p>
          <Button
            variant="outline"
            size="sm"
            disabled={!!loading}
            onClick={() =>
              run('snap', () => apiClient.downloadSignalsCsvSnapshot())
            }
          >
            {loading === 'snap' ? 'Загрузка…' : 'Скачать signals_export.csv'}
          </Button>
        </div>

        {premium ? (
          <div className="border-t pt-4 space-y-3">
            <p className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <Crown className="h-4 w-4 text-amber-500" />
              Экспорт по подписке (ваши данные)
            </p>
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="secondary"
                disabled={!!loading}
                onClick={() =>
                  run('s-csv', () =>
                    apiClient.downloadPremiumExport('signals', 'csv')
                  )
                }
              >
                {loading === 's-csv' ? '…' : 'Сигналы CSV'}
              </Button>
              <Button
                size="sm"
                variant="secondary"
                disabled={!!loading}
                onClick={() =>
                  run('s-xlsx', () =>
                    apiClient.downloadPremiumExport('signals', 'excel')
                  )
                }
              >
                <FileSpreadsheet className="h-4 w-4 mr-1" />
                {loading === 's-xlsx' ? '…' : 'Сигналы Excel'}
              </Button>
              <Button
                size="sm"
                variant="secondary"
                disabled={!!loading}
                onClick={() =>
                  run('ch-csv', () =>
                    apiClient.downloadPremiumExport('channels', 'csv')
                  )
                }
              >
                {loading === 'ch-csv' ? '…' : 'Каналы CSV'}
              </Button>
              <Button
                size="sm"
                variant="secondary"
                disabled={!!loading}
                onClick={() =>
                  run('an-json', () =>
                    apiClient.downloadPremiumExport('analytics', 'json')
                  )
                }
              >
                <FileJson className="h-4 w-4 mr-1" />
                {loading === 'an-json' ? '…' : 'Аналитика JSON'}
              </Button>
            </div>
          </div>
        ) : (
          <div className="border-t pt-4 rounded-md bg-amber-50 border border-amber-100 p-3 text-sm text-amber-900">
            Полный экспорт (Excel, свои каналы и аналитика) доступен на тарифах{' '}
            <strong>Premium</strong> и <strong>Pro</strong>.
            <Button
              variant="link"
              className="p-0 h-auto ml-1 text-amber-800"
              asChild
            >
              <Link href="/subscription">Оформить подписку</Link>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
