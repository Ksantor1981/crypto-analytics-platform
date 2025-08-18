import React from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { Button } from '@/components/ui/button';

export function LanguageSwitcher() {
  const { language, setLanguage, t } = useLanguage();

  return (
    <div className="flex items-center space-x-1">
      <Button
        variant={language === 'ru' ? 'default' : 'outline'}
        size="sm"
        onClick={() => setLanguage('ru')}
        className={`${
          language === 'ru'
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'border-gray-300 text-gray-600 hover:bg-gray-50'
        } transition-all duration-200`}
      >
        🇷🇺
      </Button>
      <Button
        variant={language === 'en' ? 'default' : 'outline'}
        size="sm"
        onClick={() => setLanguage('en')}
        className={`${
          language === 'en'
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'border-gray-300 text-gray-600 hover:bg-gray-50'
        } transition-all duration-200`}
      >
        🇺🇸
      </Button>
    </div>
  );
}
