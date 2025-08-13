const nextJest = require('next/jest');

const createJestConfig = nextJest({
  // Путь к Next.js приложению
  dir: './',
});

/** @type {import('jest').Config} */
const customJestConfig = {
  // Базовые настройки
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  
  // Модули и расширения
  moduleNameMapper: {
    // Поддержка алиасов из tsconfig
    '^@/(.*)$': '<rootDir>/src/$1',
  },

  // Покрытие кода
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{ts,tsx}',
    '!src/pages/_*.{ts,tsx}',
    '!src/types/**/*.{ts,tsx}',
  ],
  coverageThreshold: {
    global: {
      branches: 50,
      functions: 50,
      lines: 50,
      statements: 50
    }
  },

  // Настройки тестирования
  testPathIgnorePatterns: [
    '<rootDir>/.next/', 
    '<rootDir>/node_modules/',
    '<rootDir>/cypress/'
  ],

  // Трансформации
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', { presets: ['next/babel'] }],
  },

  // Расширения файлов
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],

  // Глобальные настройки
  globals: {
    'ts-jest': {
      tsconfig: 'tsconfig.jest.json'
    }
  }
};

module.exports = createJestConfig(customJestConfig);
