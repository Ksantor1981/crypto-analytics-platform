// Импорт библиотек тестирования
import '@testing-library/jest-dom';
import '@testing-library/react/dont-cleanup-after-each';

// Настройка mock для fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({}),
    ok: true,
    status: 200
  })
);

// Настройка mock для window
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn()
  }))
});

// Настройка console
const originalConsoleError = console.error;
console.error = (...args) => {
  const suppressedErrors = [
    /Warning: An update inside a test was not wrapped in act\(\)/,
    /Warning: Can't perform a React state update on an unmounted component/
  ];

  const errorMessage = args[0];
  if (!suppressedErrors.some(pattern => pattern.test(errorMessage))) {
    originalConsoleError(...args);
  }
};

// Очистка моков после каждого теста
afterEach(() => {
  jest.clearAllMocks();
});
