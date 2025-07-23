import React, { useMemo } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  TrendingUp,
  Search,
  Users,
  BarChart3,
  Plus,
  CheckCircle,
} from 'lucide-react';
import { useChannels } from '@/hooks/useChannels';
import { Loading } from '@/components/ui/Loading';
import { AddChannelModal, ChannelFormData } from '@/components/channels/AddChannelModal';
import { ChannelActions } from '@/components/channels/ChannelActions';
import { StatusBadge } from '@/components/channels/StatusBadge';
import { ChannelView } from '@/types/view';
import { Channel } from '@/types';

// Fallback mock data for demonstration when API is not available
const fallbackChannels: ChannelView[] = [
  {
    id: '1',
    name: 'CryptoSignals Pro',
    url: 'https://t.me/cryptosignals_pro',
    description: 'Профессиональные сигналы с высокой точностью',
    type: 'telegram',
    status: 'active',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    accuracy: 87.5,
    signals: 156,
    roi: 24.3,
    subscribers: 12500,
    category: 'premium',
    rating: 4.8,
    avatar: '🚀',
  },
  {
    id: '2',
    name: 'TradingMaster',
    url: 'https://t.me/tradingmaster',
    description: 'Ежедневные торговые возможности',
    type: 'telegram',
    status: 'active',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    accuracy: 82.1,
    signals: 89,
    roi: 18.7,
    subscribers: 8900,
    category: 'medium',
    rating: 4.5,
    avatar: '📈',
  },
  {
    id: '3',
    name: 'CoinHunter',
    url: 'https://t.me/coinhunter',
    description: 'Поиск перспективных альткоинов',
    type: 'telegram',
    status: 'pending',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    accuracy: 91.2,
    signals: 203,
    roi: 31.5,
    subscribers: 15600,
    category: 'premium',
    rating: 4.9,
    avatar: '🎯',
  },
];

const categories = [
  { value: 'all', label: 'Все каналы' },
  { value: 'premium', label: 'Премиум' },
  { value: 'medium', label: 'Стандарт' },
  { value: 'basic', label: 'Базовые' },
];

const sortOptions = [
  { value: 'rating', label: 'По рейтингу' },
  { value: 'accuracy', label: 'По точности' },
  { value: 'roi', label: 'По ROI' },
  { value: 'subscribers', label: 'По подписчикам' },
];

const ChannelsPage: React.FC = () => {
  const {
    channels: apiChannels,
    isLoading,
    createChannel,
    updateChannel,
    deleteChannel,
  } = useChannels();

  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [activeCategory, setActiveCategory] = React.useState('all');
  const [searchTerm, setSearchTerm] = React.useState('');
  const [sortOption, setSortOption] = React.useState('rating');

  const channels: ChannelView[] = (apiChannels?.length ? apiChannels : fallbackChannels) as ChannelView[];

  const filteredAndSortedChannels = useMemo(() => {
    if (!channels) return [];
    let filtered = channels.filter((channel) => {
      const matchesCategory = activeCategory === 'all' || !channel.category || channel.category === activeCategory;
      const matchesSearch = channel.name.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesCategory && matchesSearch;
    });

    return [...filtered].sort((a, b) => {
      switch (sortOption) {
        case 'accuracy':
          return (b.accuracy || 0) - (a.accuracy || 0);
        case 'roi':
          return (b.roi || 0) - (a.roi || 0);
        case 'subscribers':
          return (b.subscribers || 0) - (a.subscribers || 0);
        case 'rating':
        default:
          return (b.rating || 0) - (a.rating || 0);
      }
    });
  }, [channels, activeCategory, searchTerm, sortOption]);

  const handleAddChannel = async (data: ChannelFormData) => {
    const newChannelData = { ...data, type: 'telegram' as const };
    await createChannel(newChannelData as Omit<Channel, 'id' | 'status' | 'createdAt' | 'updatedAt'>);
    setIsModalOpen(false);
  };

  if (isLoading && !apiChannels?.length) {
    return <Loading />;
  }

  return (
    <>
      <Head>
        <title>Каналы - Crypto Analytics</title>
        <meta name="description" content="Просмотр и управление каналами для анализа крипто-сигналов." />
      </Head>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Каналы</h1>
          <Button onClick={() => setIsModalOpen(true)} className="mt-4 sm:mt-0">
            <Plus className="mr-2 h-4 w-4" />
            Добавить канал
          </Button>
        </div>

        <AddChannelModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onAdd={handleAddChannel}
        />

        <Card className="mb-8">
          <CardContent className="p-4 flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
            <div className="w-full md:w-1/2 lg:w-1/3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-5 w-5" />
                <Input
                  placeholder="Поиск по названию..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10"
                />
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <select
                value={activeCategory}
                onChange={(e) => setActiveCategory(e.target.value)}
                className="form-select rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
              >
                {categories.map((c) => (<option key={c.value} value={c.value}>{c.label}</option>))}
              </select>
              <select
                value={sortOption}
                onChange={(e) => setSortOption(e.target.value)}
                className="form-select rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
              >
                {sortOptions.map((s) => (<option key={s.value} value={s.value}>{s.label}</option>))}
              </select>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredAndSortedChannels.length > 0 ? (
            filteredAndSortedChannels.map((channel) => (
              <Card key={channel.id} className="flex flex-col justify-between transition-shadow duration-300 hover:shadow-lg rounded-lg overflow-hidden">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3 min-w-0">
                      <div className="text-3xl flex-shrink-0">{channel.avatar || '📢'}</div>
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-lg leading-tight truncate">
                          <Link href={`/channels/${channel.id}`} className="hover:underline" title={channel.name}>
                            {channel.name}
                          </Link>
                        </CardTitle>
                        <StatusBadge status={channel.status} />
                      </div>
                    </div>
                    <ChannelActions
                      channel={channel as Channel & { url: string }}
                      onDelete={() => deleteChannel(channel.id)}
                      onActivate={() => updateChannel({ id: channel.id, data: { status: 'active' } })}
                      onDeactivate={() => updateChannel({ id: channel.id, data: { status: 'inactive' } })}
                    />
                  </div>
                </CardHeader>
                <CardContent className="flex-grow">
                  <p className="text-sm text-gray-600 mb-4 h-10 overflow-hidden">{channel.description}</p>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="flex items-center truncate"><CheckCircle className="h-4 w-4 mr-2 text-green-500 flex-shrink-0" /> <span>Точность: {channel.accuracy?.toFixed(1) ?? 'N/A'}%</span></div>
                    <div className="flex items-center truncate"><TrendingUp className="h-4 w-4 mr-2 text-blue-500 flex-shrink-0" /> <span>ROI: {channel.roi?.toFixed(1) ?? 'N/A'}%</span></div>
                    <div className="flex items-center truncate"><Users className="h-4 w-4 mr-2 text-purple-500 flex-shrink-0" /> <span>Подписчики: {channel.subscribers ?? 'N/A'}</span></div>
                    <div className="flex items-center truncate"><BarChart3 className="h-4 w-4 mr-2 text-yellow-500 flex-shrink-0" /> <span>Сигналы: {channel.signals ?? 'N/A'}</span></div>
                  </div>
                </CardContent>
                <div className="p-4 border-t mt-auto bg-gray-50">
                  <Link href={`/channels/${channel.id}`} passHref>
                    <Button variant="outline" className="w-full">Подробнее</Button>
                  </Link>
                </div>
              </Card>
            ))
          ) : (
            <div className="col-span-full text-center py-16">
              <Search className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">Каналы не найдены</h3>
              <p className="mt-1 text-sm text-gray-500">Попробуйте изменить фильтры или добавить новый канал.</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default ChannelsPage;



