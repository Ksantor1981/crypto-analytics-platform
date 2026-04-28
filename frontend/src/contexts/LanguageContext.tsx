import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from 'react';

import { Language, detectLanguage, getTranslation } from '@/lib/i18n';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(
  undefined
);

export function LanguageProvider({
  children,
}: {
  children: ReactNode;
}): React.ReactElement {
  const [language, setLanguageState] = useState<Language>('ru');

  // После гидрации читаем localStorage / navigator (на SSR всегда 'ru').
  useEffect(() => {
    const detectedLang = detectLanguage();
    setLanguageState(detectedLang);
    localStorage.setItem('language', detectedLang);
  }, []);

  const setLanguage = (lang: Language): void => {
    setLanguageState(lang);
    localStorage.setItem('language', lang);
  };

  const t = (key: string): string => getTranslation(key, language);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage(): LanguageContextType {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
