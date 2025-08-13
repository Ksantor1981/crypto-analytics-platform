import { useCallback } from 'react';
// import { useToast } from '@/contexts/ToastContext';
import { ApiError } from '@/lib/api/client';

export const useErrorHandler = () => {
  // useToast заменен на console

  const handleError = useCallback(
    (error: unknown, defaultMessage: string) => {
      if (error instanceof ApiError) {
        if (error.status === 401) {
          console.error('Ошибка аутентификации', 'Пожалуйста, войдите в систему');
        } else if (error.status === 403) {
          console.error(
            'Доступ запрещен',
            'У вас нет прав для выполнения этого действия'
          );
        } else if (error.status === 404) {
          console.error('Не найдено', 'Запрашиваемый ресурс не найден');
        } else if (error.status >= 500) {
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
