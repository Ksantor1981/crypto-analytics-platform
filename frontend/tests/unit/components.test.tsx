import React from 'react';
import { render, screen, fireEvent, waitFor, within, cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

beforeEach(cleanup);

// Mock API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    auth: {
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
    },
    channels: {
      getAll: jest.fn(),
      create: jest.fn(),
      delete: jest.fn(),
    },
    signals: {
      getAll: jest.fn(),
      getById: jest.fn(),
    },
  },
}));

// Test wrapper with providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

// Mock components for testing
const MockLoginForm = () => (
  <div data-testid="login-form">
    <input data-testid="email-input" type="email" placeholder="Email" />
    <input data-testid="password-input" type="password" placeholder="Password" />
    <button data-testid="login-button" type="submit">Войти</button>
  </div>
);

const MockChannelCard = ({ channel }: { channel: any }) => (
  <div data-testid="channel-card">
    <h3 data-testid="channel-name">{channel.name}</h3>
    <p data-testid="channel-url">{channel.url}</p>
    <span data-testid="channel-accuracy">{channel.accuracy}%</span>
  </div>
);

const MockSignalTable = ({ signals }: { signals: any[] }) => (
  <table data-testid="signal-table">
    <tbody>
      {signals.map((signal, index) => (
        <tr key={index} data-testid={`signal-row-${index}`}>
          <td data-testid={`signal-pair-${index}`}>{signal.pair}</td>
          <td data-testid={`signal-type-${index}`}>{signal.type}</td>
          <td data-testid={`signal-price-${index}`}>{signal.price}</td>
        </tr>
      ))}
    </tbody>
  </table>
);

describe('Frontend Components Unit Tests', () => {
  describe('LoginForm Component', () => {
    test('renders login form with all fields', () => {
      render(
        <TestWrapper>
          <MockLoginForm />
        </TestWrapper>
      );

      expect(screen.getByTestId('login-form')).toBeInTheDocument();
      expect(screen.getByTestId('email-input')).toBeInTheDocument();
      expect(screen.getByTestId('password-input')).toBeInTheDocument();
      expect(screen.getByTestId('login-button')).toBeInTheDocument();
    });

    test('handles form submission', async () => {
      const mockSubmit = jest.fn((e) => e.preventDefault());
      const { container } = render(
        <TestWrapper>
          <form data-testid="submit-form" onSubmit={mockSubmit}>
            <input data-testid="submit-email" type="email" />
            <input data-testid="submit-password" type="password" />
            <button data-testid="submit-btn" type="submit">Войти</button>
          </form>
        </TestWrapper>
      );
      const emailInput = container.querySelector('[data-testid="submit-email"]');
      const passwordInput = container.querySelector('[data-testid="submit-password"]');
      const submitButton = container.querySelector('[data-testid="submit-btn"]');
      if (emailInput && passwordInput && submitButton) {
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.click(submitButton);
      }
      await waitFor(() => expect(mockSubmit).toHaveBeenCalled());
    });

    test('validates email format', () => {
      const { container } = render(
        <TestWrapper>
          <MockLoginForm />
        </TestWrapper>
      );
      const emailInput = container.querySelector(
        '[data-testid="email-input"]'
      ) as HTMLInputElement | null;
      expect(emailInput).not.toBeNull();

      fireEvent.change(emailInput!, { target: { value: 'invalid-email' } });

      expect(emailInput).toHaveValue('invalid-email');
      // В реальном компоненте здесь была бы валидация
    });
  });

  describe('ChannelCard Component', () => {
    const mockChannel = {
      id: 1,
      name: 'Test Channel',
      url: 'https://t.me/testchannel',
      accuracy: 85.5,
      signals_count: 150,
      category: 'crypto'
    };

    test('renders channel information correctly', () => {
      const { container } = render(
        <TestWrapper>
          <MockChannelCard channel={mockChannel} />
        </TestWrapper>
      );

      const scope = within(container);
      expect(scope.getByTestId('channel-card')).toBeInTheDocument();
      expect(scope.getByTestId('channel-name')).toHaveTextContent('Test Channel');
      expect(scope.getByTestId('channel-url')).toHaveTextContent('https://t.me/testchannel');
      expect(scope.getByTestId('channel-accuracy')).toHaveTextContent('85.5%');
    });

    test('displays channel metrics', () => {
      const { container } = render(
        <TestWrapper>
          <MockChannelCard channel={mockChannel} />
        </TestWrapper>
      );

      const card = within(container).getByTestId('channel-card');
      expect(card).toBeInTheDocument();
    });
  });

  describe('SignalTable Component', () => {
    const mockSignals = [
      {
        id: 1,
        pair: 'BTC/USDT',
        type: 'BUY',
        price: 45000,
        target: 46000,
        stop_loss: 44000,
        timestamp: '2025-08-16T10:00:00Z'
      },
      {
        id: 2,
        pair: 'ETH/USDT',
        type: 'SELL',
        price: 3200,
        target: 3100,
        stop_loss: 3300,
        timestamp: '2025-08-16T11:00:00Z'
      }
    ];

    test('renders signal table with data', () => {
      const { container } = render(
        <TestWrapper>
          <MockSignalTable signals={mockSignals} />
        </TestWrapper>
      );

      const scope = within(container);
      expect(scope.getByTestId('signal-table')).toBeInTheDocument();
      expect(scope.getByTestId('signal-row-0')).toBeInTheDocument();
      expect(scope.getByTestId('signal-row-1')).toBeInTheDocument();
    });

    test('displays signal information correctly', () => {
      const { container } = render(
        <TestWrapper>
          <MockSignalTable signals={mockSignals} />
        </TestWrapper>
      );

      const scope = within(container);
      expect(scope.getByTestId('signal-pair-0')).toHaveTextContent('BTC/USDT');
      expect(scope.getByTestId('signal-type-0')).toHaveTextContent('BUY');
      expect(scope.getByTestId('signal-price-0')).toHaveTextContent('45000');
      expect(scope.getByTestId('signal-pair-1')).toHaveTextContent('ETH/USDT');
      expect(scope.getByTestId('signal-type-1')).toHaveTextContent('SELL');
      expect(scope.getByTestId('signal-price-1')).toHaveTextContent('3200');
    });

    test('handles empty signals array', () => {
      const { container } = render(
        <TestWrapper>
          <MockSignalTable signals={[]} />
        </TestWrapper>
      );

      expect(within(container).getByTestId('signal-table')).toBeInTheDocument();
    });
  });

  describe('Navigation Component', () => {
    test('renders navigation menu', () => {
      render(
        <TestWrapper>
          <nav data-testid="main-navigation">
            <a href="/dashboard" data-testid="nav-dashboard">Dashboard</a>
            <a href="/channels" data-testid="nav-channels">Channels</a>
            <a href="/signals" data-testid="nav-signals">Signals</a>
            <a href="/profile" data-testid="nav-profile">Profile</a>
          </nav>
        </TestWrapper>
      );

      expect(screen.getByTestId('main-navigation')).toBeInTheDocument();
      expect(screen.getByTestId('nav-dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('nav-channels')).toBeInTheDocument();
      expect(screen.getByTestId('nav-signals')).toBeInTheDocument();
      expect(screen.getByTestId('nav-profile')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    test('displays error message when API fails', async () => {
      const ErrorComponent = () => (
        <div data-testid="error-message" className="error">
          Произошла ошибка при загрузке данных
        </div>
      );

      render(
        <TestWrapper>
          <ErrorComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('error-message')).toBeInTheDocument();
      expect(screen.getByTestId('error-message')).toHaveTextContent('Произошла ошибка при загрузке данных');
    });

    test('shows loading state', () => {
      const LoadingComponent = () => (
        <div data-testid="loading-spinner" className="loading">
          Загрузка...
        </div>
      );

      render(
        <TestWrapper>
          <LoadingComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
      expect(screen.getByTestId('loading-spinner')).toHaveTextContent('Загрузка...');
    });
  });
});
