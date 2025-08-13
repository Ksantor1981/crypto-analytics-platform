import { renderHook, act } from '@testing-library/react-hooks';
import { useChannels } from './useChannels';
import { channelsApi } from '@/lib/api/channels';
import { Channel } from '@/types';

// Мок для API
jest.mock('@/lib/api/channels');

describe('useChannels Hook', () => {
  const mockChannels: Channel[] = [
    {
      id: '1',
      name: 'Test Channel 1',
      status: 'active',
      created_at: '2023-01-01T00:00:00Z',
      accuracy: 75,
      type: 'telegram'
    },
    {
      id: '2',
      name: 'Test Channel 2',
      status: 'inactive',
      created_at: '2023-02-01T00:00:00Z',
      accuracy: 60,
      type: 'twitter'
    }
  ];

  beforeEach(() => {
    (channelsApi.getChannels as jest.Mock).mockResolvedValue(mockChannels);
  });

  it('fetches and filters channels correctly', async () => {
    const { result, waitForNextUpdate } = renderHook(() => 
      useChannels({ type: 'telegram' })
    );

    await waitForNextUpdate();

    expect(result.current.channels).toEqual(mockChannels);
    expect(result.current.filteredChannels).toHaveLength(1);
    expect(result.current.filteredChannels[0].type).toBe('telegram');
  });

  it('applies filters dynamically', async () => {
    const { result, waitForNextUpdate } = renderHook(() => 
      useChannels()
    );

    await waitForNextUpdate();

    act(() => {
      result.current.applyFilters({ status: 'active' });
    });

    expect(result.current.filteredChannels).toHaveLength(1);
    expect(result.current.filteredChannels[0].status).toBe('active');
  });

  it('handles accuracy range filter', async () => {
    const { result, waitForNextUpdate } = renderHook(() => 
      useChannels()
    );

    await waitForNextUpdate();

    act(() => {
      result.current.applyFilters({ accuracy_range: '70-80' });
    });

    expect(result.current.filteredChannels).toHaveLength(1);
    expect(result.current.filteredChannels[0].accuracy).toBeGreaterThanOrEqual(70);
    expect(result.current.filteredChannels[0].accuracy).toBeLessThanOrEqual(80);
  });

  it('handles date filters', async () => {
    const { result, waitForNextUpdate } = renderHook(() => 
      useChannels()
    );

    await waitForNextUpdate();

    act(() => {
      result.current.applyFilters({ 
        created_from: '2023-01-15T00:00:00Z',
        created_to: '2023-02-15T00:00:00Z'
      });
    });

    expect(result.current.filteredChannels).toHaveLength(1);
    expect(result.current.filteredChannels[0].id).toBe('2');
  });
});
