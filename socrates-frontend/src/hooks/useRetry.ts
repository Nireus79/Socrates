/**
 * Hook to retry failed requests with exponential backoff
 */

import { useCallback, useState } from 'react';

interface RetryOptions {
  maxAttempts?: number;
  initialDelayMs?: number;
  maxDelayMs?: number;
  backoffMultiplier?: number;
}

export const useRetry = (options: RetryOptions = {}) => {
  const {
    maxAttempts = 3,
    initialDelayMs = 1000,
    maxDelayMs = 10000,
    backoffMultiplier = 2,
  } = options;

  const [isRetrying, setIsRetrying] = useState(false);
  const [attemptCount, setAttemptCount] = useState(0);

  const retry = useCallback(
    async <T,>(
      fn: () => Promise<T>,
      onRetry?: (attempt: number, error: Error) => void
    ): Promise<T> => {
      setIsRetrying(true);
      let lastError: Error | null = null;

      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
          setAttemptCount(attempt);
          const result = await fn();
          setIsRetrying(false);
          setAttemptCount(0);
          return result;
        } catch (error) {
          lastError = error instanceof Error ? error : new Error(String(error));

          if (attempt < maxAttempts) {
            const delay = Math.min(
              initialDelayMs * Math.pow(backoffMultiplier, attempt - 1),
              maxDelayMs
            );

            onRetry?.(attempt, lastError);

            await new Promise((resolve) => setTimeout(resolve, delay));
          }
        }
      }

      setIsRetrying(false);
      setAttemptCount(0);
      throw lastError;
    },
    [maxAttempts, initialDelayMs, maxDelayMs, backoffMultiplier]
  );

  return { retry, isRetrying, attemptCount };
};
