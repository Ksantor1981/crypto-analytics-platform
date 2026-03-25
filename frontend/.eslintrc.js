module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  plugins: [
    '@typescript-eslint', 
    'react', 
    'react-hooks', 
    'import', 
    'jsx-a11y', 
    'prettier'
  ],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    // type-aware strict rules (no-unsafe-*, strict-boolean) — отдельно в overrides для узких путей
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
    'plugin:import/recommended',
    'plugin:import/typescript',
    'prettier'
  ],
  parserOptions: {
    ecmaVersion: 2021,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true
    },
    project: './tsconfig.json'
  },
  settings: {
    react: {
      version: 'detect'
    },
    'import/resolver': {
      typescript: {
        project: './tsconfig.json'
      }
    }
  },
  rules: {
    // TypeScript (UI/Next: без обязательных return types и strict-boolean на каждой строке)
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', { 
      argsIgnorePattern: '^_',
      varsIgnorePattern: '^_'
    }],
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

    // React-specific rules
    'react/prop-types': 'off', // TypeScript handles prop types
    'react/react-in-jsx-scope': 'off', // Not needed in modern React
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    // React 19 / расширенные правила — слишком шумно для существующего UI без рефакторинга
    'react-hooks/set-state-in-effect': 'off',
    'react-hooks/refs': 'off',
    'react-hooks/purity': 'off',
    'react-hooks/immutability': 'off',
    'react/no-unknown-property': ['error', { ignore: ['jsx'] }],

    // Import rules
    'import/order': ['error', {
      groups: [
        'builtin', 
        'external', 
        'internal', 
        'parent', 
        'sibling', 
        'index'
      ],
      'newlines-between': 'always'
    }],
    'import/no-unresolved': 'error',
    'import/named': 'error',

    // Accessibility (строгие подтипы — предупреждения; критичное остаётся)
    'jsx-a11y/alt-text': 'error',
    'jsx-a11y/aria-role': 'error',
    // label-has-for дублирует label-has-associated-control (deprecated в jsx-a11y)
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

    // General best practices
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'no-debugger': 'error',
    'complexity': ['warn', 10],
    'max-lines-per-function': ['warn', 50],
    'max-depth': ['warn', 4],

    // CVA / re-export «default» (shadcn) — ложные срабатывания import plugin
    'import/no-named-as-default': 'off',
    'import/no-named-as-default-member': 'off',

    // Prettier integration
    'prettier/prettier': 'error'
  },
  overrides: [
    // Остальной UI src — мягче базовых 50/10
    {
      files: ['src/**/*.ts', 'src/**/*.tsx'],
      rules: {
        'max-lines-per-function': ['warn', 95],
        complexity: ['warn', 14],
      },
    },
    // Страницы Next — крупные layout-функции без разбиения на этапе MVP
    {
      files: ['src/pages/**/*.ts', 'src/pages/**/*.tsx'],
      rules: {
        'max-lines-per-function': ['warn', 650],
        complexity: ['warn', 28],
      },
    },
    // Компоненты, хуки, контексты — длинные формы и списки
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
        'max-lines-per-function': 'off'
      }
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
        '@typescript-eslint/no-unnecessary-condition': 'off'
      }
    },
    {
      files: ['**/*.test.ts', '**/*.test.tsx'],
      env: {
        jest: true
      },
      rules: {
        '@typescript-eslint/no-explicit-any': 'off',
        'max-lines-per-function': 'off',
        complexity: 'off',
      }
    }
  ]
};
