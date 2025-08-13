module.exports = {
  // Общие настройки
  semi: true,                     // Использовать точки с запятой
  trailingComma: 'es5',           // Добавлять запятые в многострочных литералах
  singleQuote: true,              // Использовать одинарные кавычки
  printWidth: 80,                 // Максимальная длина строки
  tabWidth: 2,                    // Размер отступа
  useTabs: false,                 // Использовать пробелы вместо табуляции

  // Настройки для React и TypeScript
  bracketSpacing: true,           // Добавлять пробелы внутри фигурных скобок
  jsxBracketSameLine: false,      // Закрывающий тег JSX на новой строке
  arrowParens: 'avoid',           // Стрелочные функции без скобок, где возможно

  // Настройки для разных типов файлов
  overrides: [
    {
      files: '*.json',
      options: {
        printWidth: 120
      }
    },
    {
      files: ['*.yml', '*.yaml'],
      options: {
        tabWidth: 2
      }
    }
  ],

  // Плагины
  plugins: [
    '@trivago/prettier-plugin-sort-imports'
  ],

  // Настройки для сортировки импортов
  importOrder: [
    '^react(/.*)?$',
    '^next(/.*)?$',
    '^@/(.*)$',
    '^[./]'
  ],
  importOrderSeparation: true,
  importOrderSortSpecifiers: true
};
