import { useCallback } from 'react';
import { useToast } from '@/contexts/ToastContext';
import { ApiError } from '@/lib/api/client';

export const useErrorHandler = () => {
  const { showError, showWarning } = useToast();

  const handleError = useCallback((error: unknown, customMessage?: string) => {
    console.error('Error occurred:', error);

    if (error instanceof ApiError) {
      // Обработка API ошибок
      switch (error.status) {
        case 400:
          showError(
            'Некорректный запрос',
            customMessage || error.message || 'Проверьте введенные данные'
          );
          break;
        case 401:
          showError(
            'Ошибка авторизации',
            'Пожалуйста, войдите в систему заново'
          );
          // Здесь можно добавить редирект на страницу входа
          break;
        case 403:
          showError(
            'Доступ запрещен',
            'У вас нет прав для выполнения этого действия'
          );
          break;
        case 404:
          showError(
            'Ресурс не найден',
            customMessage || 'Запрашиваемый ресурс не существует'
          );
          break;
        case 409:
          showWarning(
            'Конфликт данных',
            customMessage || error.message || 'Данные уже существуют'
          );
          break;
        case 422:
          showError(
            'Ошибка валидации',
            customMessage || error.message || 'Проверьте корректность данных'
          );
          break;
        case 429:
          showWarning(
            'Слишком много запросов',
            'Пожалуйста, подождите перед следующим запросом'
          );
          break;
        case 500:
          showError(
            'Ошибка сервера',
            'Произошла внутренняя ошибка сервера. Попробуйте позже'
          );
          break;
        case 502:
        case 503:
        case 504:
          showError(
            'Сервис недоступен',
            'Сервер временно недоступен. Попробуйте позже'
          );
          break;
        default:
          showError(
            'Произошла ошибка',
            customMessage || error.message || 'Неизвестная ошибка'
          );
      }
    } else if (error instanceof Error) {
      // Обработка обычных JavaScript ошибок
      if (error.name === 'NetworkError' || error.message.includes('fetch')) {
        showError(
          'Ошибка сети',
          'Проверьте подключение к интернету'
        );
      } else {
        showError(
          'Произошла ошибка',
          customMessage || error.message || 'Неизвестная ошибка'
        );
      }
    } else {
      // Обработка неизвестных ошибок
      showError(
        'Произошла ошибка',
        customMessage || 'Неизвестная ошибка'
      );
    }
  }, [showError, showWarning]);

  const handleAsyncError = useCallback(async <T>(
    asyncOperation: () => Promise<T>,
    customMessage?: string
  ): Promise<T | null> => {
    try {
      return await asyncOperation();
    } catch (error) {
      handleError(error, customMessage);
      return null;
    }
  }, [handleError]);

  const handleAsyncErrorWithRetry = useCallback(async <T>(
    asyncOperation: () => Promise<T>,
    maxRetries: number = 3,
    customMessage?: string
  ): Promise<T | null> => {
    let lastError: unknown;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await asyncOperation();
      } catch (error) {
        lastError = error;
        
        if (attempt === maxRetries) {
          handleError(error, customMessage);
          return null;
        }
        
        // Экспоненциальная задержка между попытками
        const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    return null;
  }, [handleError]);

  return {
    handleError,
    handleAsyncError,
    handleAsyncErrorWithRetry
  };
}; 