import { useState, useCallback, useEffect } from 'react';

/**
 * Debounced value hook — возвращает значение с задержкой после последнего изменения.
 */
export function useDebounced<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Debounced callback — вызывает callback с задержкой.
 */
export function useDebouncedCallback<T extends (...args: unknown[]) => unknown>(
  callback: T,
  delay: number
): (...args: Parameters<T>) => void {
  const [timeoutId, setTimeoutId] = useState<ReturnType<
    typeof setTimeout
  > | null>(null);

  const debounced = useCallback(
    (...args: Parameters<T>) => {
      if (timeoutId) clearTimeout(timeoutId);
      const id = setTimeout(() => {
        callback(...args);
        setTimeoutId(null);
      }, delay);
      setTimeoutId(id);
    },
    [callback, delay, timeoutId]
  );

  useEffect(() => {
    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [timeoutId]);

  return debounced;
}
