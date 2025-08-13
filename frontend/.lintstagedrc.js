module.exports = {
  // TypeScript и React файлы
  '**/*.{ts,tsx}': [
    'eslint --fix',
    'prettier --write',
    'git add'
  ],

  // Стили
  '**/*.{css,scss,less}': [
    'stylelint --fix',
    'prettier --write',
    'git add'
  ],

  // JSON и конфигурационные файлы
  '**/*.{json,yml,yaml,md}': [
    'prettier --write',
    'git add'
  ]
};
