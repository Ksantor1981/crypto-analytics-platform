import { useCallback } from 'react';
import { useToast } from '@/contexts/ToastContext';
import { ApiError } from '@/lib/api/client';

export const useErrorHandler = () => {
  const { showError, showWarning } = useToast();

  const handleError = useCallback(
    (error: unknown, defaultMessage: string) => {
      if (error instanceof ApiError) {
        if (error.status === 401) {
          showError('Ошибка аутентификации', 'Пожалуйста, войдите в систему');
        } else if (error.status === 403) {
          showError(
            'Доступ запрещен',
            'У вас нет прав для выполнения этого действия'
          );
        } else if (error.status === 404) {
          showError('Не найдено', 'Запрашиваемый ресурс не найден');
        } else if (error.status >= 500) {
          showError('Ошибка сервера', 'Произошла внутренняя ошибка сервера');
        } else {
          showError('Ошибка', error.message || defaultMessage);
        }
      } else {
        showError('Ошибка', defaultMessage);
      }
    },
    [showError]
  );

  return { handleError };
};
