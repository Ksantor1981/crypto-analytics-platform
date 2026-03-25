import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { Channel } from '@/types';

import { useChannels } from './useChannels';

const mockChannels: Channel[] = [
  {
    id: '1',
    name: 'Test Channel 1',
    status: 'active',
    created_at: '2023-01-01',
    accuracy: 75,
    type: 'telegram',
  },
  {
    id: '2',
    name: 'Test Channel 2',
    status: 'inactive',
    created_at: '2023-02-01',
    accuracy: 60,
    type: 'twitter',
  },
];

const mockGetChannels = jest.fn().mockResolvedValue(mockChannels);
jest.mock('@/lib/api', () => ({
  apiClient: {
    getChannels: (...args: unknown[]) => mockGetChannels(...args),
    getChannel: jest.fn(),
    createChannel: jest.fn(),
    updateChannel: jest.fn(),
    deleteChannel: jest.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const Wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
  Wrapper.displayName = 'TestQueryClientProvider';
  return Wrapper;
};

describe('useChannels Hook', () => {
  beforeEach(() => {
    mockGetChannels.mockResolvedValue(mockChannels);
  });

  it('fetches channels correctly', async () => {
    const { result } = renderHook(() => useChannels(), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.channels).toHaveLength(2));
    expect(result.current.channels[0].name).toBe('Test Channel 1');
  });

  it('returns loading state initially', () => {
    const { result } = renderHook(() => useChannels(), {
      wrapper: createWrapper(),
    });
    expect(result.current.isLoading).toBe(true);
  });

  it('exposes refetch and mutations', async () => {
    const { result } = renderHook(() => useChannels(), {
      wrapper: createWrapper(),
    });
    await waitFor(() =>
      expect(result.current.channels.length).toBeGreaterThanOrEqual(0)
    );
    expect(typeof result.current.refetch).toBe('function');
    expect(typeof result.current.createChannel).toBe('function');
    expect(typeof result.current.deleteChannel).toBe('function');
  });
});
