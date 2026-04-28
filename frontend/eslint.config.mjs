import { FlatCompat } from '@eslint/eslintrc';
import js from '@eslint/js';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTs from 'eslint-config-next/typescript';
import prettierPlugin from 'eslint-plugin-prettier';
import tsParser from '@typescript-eslint/parser';
import globals from 'globals';
import { dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
});

const baseRules = {
  '@typescript-eslint/explicit-function-return-type': 'off',
  '@typescript-eslint/no-explicit-any': 'warn',
  '@typescript-eslint/no-unused-vars': [
    'error',
    {
      argsIgnorePattern: '^_',
      varsIgnorePattern: '^_',
    },
  ],
  '@typescript-eslint/strict-boolean-expressions': 'off',
  '@typescript-eslint/no-unnecessary-condition': 'warn',
  '@typescript-eslint/no-floating-promises': 'warn',
  '@typescript-eslint/no-misused-promises': [
    'error',
    {
      checksVoidReturn: {
        attributes: false,
        properties: false,
      },
    },
  ],

  'react/prop-types': 'off',
  'react/react-in-jsx-scope': 'off',
  'react-hooks/rules-of-hooks': 'error',
  'react-hooks/exhaustive-deps': 'warn',
  'react-hooks/set-state-in-effect': 'off',
  'react-hooks/refs': 'off',
  'react-hooks/purity': 'off',
  'react-hooks/immutability': 'off',
  'react/no-unknown-property': ['error', { ignore: ['jsx'] }],

  'import/order': [
    'error',
    {
      groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
      'newlines-between': 'always',
    },
  ],
  'import/no-unresolved': 'error',
  // TypeScript packages with generated declarations often trigger false positives here.
  'import/named': 'off',

  'jsx-a11y/alt-text': 'error',
  'jsx-a11y/aria-role': 'error',
  'jsx-a11y/label-has-for': 'off',
  'jsx-a11y/label-has-associated-control': [
    'warn',
    {
      depth: 25,
      labelComponents: ['label', 'Label'],
      controlComponents: ['Input', 'input', 'select', 'textarea'],
    },
  ],
  'jsx-a11y/click-events-have-key-events': 'warn',
  'jsx-a11y/no-static-element-interactions': 'warn',
  'jsx-a11y/heading-has-content': 'warn',

  'no-console': ['warn', { allow: ['warn', 'error'] }],
  'no-debugger': 'error',
  complexity: ['warn', 10],
  'max-lines-per-function': ['warn', 50],
  'max-depth': ['warn', 4],

  'import/no-named-as-default': 'off',
  'import/no-named-as-default-member': 'off',
  'prettier/prettier': ['error', { endOfLine: 'auto' }],
};

const eslintConfig = [
  {
    ignores: [
      'node_modules/**',
      '.next/**',
      'out/**',
      'build/**',
      'coverage/**',
      'next-env.d.ts',
      'package.json.new',
    ],
  },
  ...compat.extends(
    'eslint:recommended',
    'plugin:import/recommended',
    'plugin:import/typescript',
    'prettier'
  ),
  ...nextVitals,
  ...nextTs,
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 2021,
        sourceType: 'module',
        ecmaFeatures: {
          jsx: true,
        },
        project: './tsconfig.json',
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    settings: {
      react: {
        version: 'detect',
      },
      'import/resolver': {
        typescript: {
          project: './tsconfig.json',
        },
      },
    },
    plugins: {
      prettier: prettierPlugin,
    },
    rules: baseRules,
  },
  {
    files: ['src/**/*.ts', 'src/**/*.tsx'],
    rules: {
      'max-lines-per-function': ['warn', 95],
      complexity: ['warn', 14],
    },
  },
  {
    files: ['src/pages/**/*.ts', 'src/pages/**/*.tsx'],
    rules: {
      'max-lines-per-function': ['warn', 650],
      complexity: ['warn', 28],
      '@typescript-eslint/no-unnecessary-condition': 'off',
    },
  },
  {
    files: [
      'src/components/**/*.ts',
      'src/components/**/*.tsx',
      'src/hooks/**/*.ts',
      'src/hooks/**/*.tsx',
      'src/contexts/**/*.ts',
      'src/contexts/**/*.tsx',
    ],
    rules: {
      'max-lines-per-function': ['warn', 420],
      complexity: ['warn', 22],
    },
  },
  {
    files: ['src/components/FeedbackForm.tsx'],
    rules: {
      'max-lines-per-function': 'off',
    },
  },
  {
    files: ['src/lib/**/*.ts', 'src/lib/**/*.tsx'],
    rules: {
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unsafe-assignment': 'off',
      '@typescript-eslint/no-unsafe-argument': 'off',
      '@typescript-eslint/no-unsafe-call': 'off',
      '@typescript-eslint/no-unsafe-member-access': 'off',
      '@typescript-eslint/no-unsafe-return': 'off',
      '@typescript-eslint/strict-boolean-expressions': 'off',
      '@typescript-eslint/no-unnecessary-condition': 'off',
    },
  },
  {
    files: ['**/*.test.ts', '**/*.test.tsx'],
    languageOptions: {
      globals: globals.jest,
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      'max-lines-per-function': 'off',
      complexity: 'off',
    },
  },
];

export default eslintConfig;
