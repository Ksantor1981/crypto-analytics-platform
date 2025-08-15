import { useCallback } from 'react';
// import { useToast } from '@/contexts/ToastContext';
import { ApiError } from '@/types';

export const useErrorHandler = () => {
  // useToast заменен на console

  const handleError = useCallback(
    (error: unknown, defaultMessage: string) => {
      if (error instanceof Error) {
        if (error.message.includes('401')) {
          console.error('Ошибка аутентификации', 'Пожалуйста, войдите в систему');
        } else if (error.message.includes('403')) {
          console.error(
            'Доступ запрещен',
            'У вас нет прав для выполнения этого действия'
          );
        } else if (error.message.includes('404')) {
          console.error('Не найдено', 'Запрашиваемый ресурс не найден');
        } else if (error.message.includes('500')) {
          console.error('Ошибка сервера', 'Произошла внутренняя ошибка сервера');
        } else {
          console.error('Ошибка', error.message || defaultMessage);
        }
      } else {
        console.error('Ошибка', defaultMessage);
      }
    },
    []
  );

  return { handleError };
};
