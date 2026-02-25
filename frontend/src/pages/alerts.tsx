import { NextPage } from 'next';
import { useState, useEffect } from 'react';
import Head from 'next/head';
import { apiClient } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Bell, AlertTriangle, TrendingUp, Settings, ArrowUpRight, ArrowDownRight } from 'lucide-react';

const AlertsPage: NextPage = () => {
  const [signals, setSignals] = useState<Record<string, unknown>[]>([]);
  const [channelCount, setChannelCount] = useState(0);

  useEffect(() => {
    async function load() {
      try {
        const raw = await apiClient.getSignals();
        const data = Array.isArray(raw) ? raw : (raw?.signals || []);
        setSignals(data);
        const ch = await apiClient.getChannels();
        setChannelCount(Array.isArray(ch) ? ch.length : 0);
      } catch {}
    }
    load();
  }, []);

  const pending = signals.filter(s => s.status === 'PENDING').length;
  const resolved = signals.filter(s => (s.status as string || '').includes('HIT')).length;

  return (
    <>
      <Head><title>Алерты - CryptoAnalytics</title></Head>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Bell className="h-6 w-6 text-blue-600" />
            Последние сигналы и алерты
          </h1>
          <p className="text-gray-600 mt-1">Сигналы собранные из {channelCount} каналов</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><Bell className="h-5 w-5 text-blue-600" /></div>
              <div>
                <p className="text-sm text-gray-600">Всего сигналов</p>
                <p className="text-xl font-bold">{signals.length}</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg"><AlertTriangle className="h-5 w-5 text-yellow-600" /></div>
              <div>
                <p className="text-sm text-gray-600">Ожидают</p>
                <p className="text-xl font-bold">{pending}</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><TrendingUp className="h-5 w-5 text-green-600" /></div>
              <div>
                <p className="text-sm text-gray-600">Исполнены</p>
                <p className="text-xl font-bold">{resolved}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader><CardTitle>Последние сигналы</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {signals.length === 0 && <p className="text-gray-500 text-center py-4">Нет сигналов</p>}
              {signals.map((s, i) => (
                <div key={i} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    {(s.direction as string) === 'LONG' ?
                      <ArrowUpRight className="h-5 w-5 text-green-600" /> :
                      <ArrowDownRight className="h-5 w-5 text-red-600" />
                    }
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">{s.asset as string}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          (s.direction as string) === 'LONG' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>{s.direction as string}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          (s.status as string) === 'PENDING' ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-100 text-blue-800'
                        }`}>{s.status as string}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5 max-w-md truncate">
                        {(s.original_text as string || '').slice(0, 80)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">${Number(s.entry_price || 0).toLocaleString()}</p>
                    {s.tp1_price && <p className="text-xs text-green-600">TP: ${Number(s.tp1_price).toLocaleString()}</p>}
                    {s.stop_loss && <p className="text-xs text-red-600">SL: ${Number(s.stop_loss).toLocaleString()}</p>}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

    </>
  );
};

export default AlertsPage;

