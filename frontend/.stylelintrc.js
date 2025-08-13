module.exports = {
  extends: ['stylelint-config-standard'],
  rules: {
    // Кастомные правила
    'indentation': 2,
    'color-hex-case': 'lower',
    'selector-list-comma-newline-after': 'always',
    'declaration-block-trailing-semicolon': 'always',
    'no-descending-specificity': null,
    
    // Правила для tailwind
    'at-rule-no-unknown': [
      true,
      {
        ignoreAtRules: [
          'tailwind',
          'apply',
          'variants',
          'responsive',
          'screen'
        ]
      }
    ],
    
    // Игнорирование специфических паттернов
    'selector-pseudo-class-no-unknown': [
      true,
      {
        ignorePseudoClasses: ['global']
      }
    ]
  }
};
