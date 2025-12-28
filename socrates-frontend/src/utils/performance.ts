/**
 * Performance optimization utilities
 *
 * Features:
 * - Debouncing for search and filter operations
 * - Throttling for scroll and resize events
 * - Memoization for expensive computations
 * - Request idle callback for non-critical tasks
 */

/**
 * Debounce a function call
 * Useful for search inputs, filter changes, etc.
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout | null = null;

  return function (...args: Parameters<T>) {
    if (timeoutId) clearTimeout(timeoutId);

    timeoutId = setTimeout(() => {
      func(...args);
    }, delay);
  };
}

/**
 * Throttle a function call
 * Useful for scroll, resize, and mouse move events
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;

  return function (...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
}

/**
 * Memoize a function result
 * Cache results based on arguments
 */
export function memoize<T extends (...args: any[]) => any>(
  fn: T,
  resolver?: (...args: Parameters<T>) => string
): T {
  const cache = new Map<string, any>();

  return ((...args: Parameters<T>) => {
    const key = resolver ? resolver(...args) : JSON.stringify(args);

    if (cache.has(key)) {
      return cache.get(key);
    }

    const result = fn(...args);
    cache.set(key, result);
    return result;
  }) as T;
}

/**
 * Schedule a task to run when browser is idle
 * Falls back to setTimeout if requestIdleCallback not available
 */
export function scheduleIdleTask(callback: IdleRequestCallback): number {
  if (typeof requestIdleCallback !== 'undefined') {
    return requestIdleCallback(callback);
  }

  // Fallback: use setTimeout with 0 delay
  return setTimeout(() => {
    callback({ didTimeout: false, timeRemaining: () => 0 } as IdleDeadline);
  }, 0);
}

/**
 * Cancel an idle task
 */
export function cancelIdleTask(id: number): void {
  if (typeof cancelIdleCallback !== 'undefined') {
    cancelIdleCallback(id);
  } else {
    clearTimeout(id);
  }
}

/**
 * Compare two objects for shallow equality
 * Used in React.memo custom comparators
 */
export function shallowEqual(a: any, b: any): boolean {
  if (a === b) return true;
  if (a == null || b == null) return false;

  const keysA = Object.keys(a);
  const keysB = Object.keys(b);

  if (keysA.length !== keysB.length) return false;

  for (const key of keysA) {
    if (!(key in b) || a[key] !== b[key]) {
      return false;
    }
  }

  return true;
}

/**
 * Performance monitoring
 * Measure component render time
 */
export class PerformanceMonitor {
  private static marks = new Map<string, number>();

  static mark(label: string): void {
    this.marks.set(label, performance.now());
  }

  static measure(label: string, startMark: string): number {
    const endTime = performance.now();
    const startTime = this.marks.get(startMark);

    if (!startTime) {
      console.warn(`Start mark "${startMark}" not found`);
      return 0;
    }

    const duration = endTime - startTime;

    if (process.env.NODE_ENV === 'development') {
      console.log(`[Performance] ${label}: ${duration.toFixed(2)}ms`);
    }

    return duration;
  }

  static clearMarks(): void {
    this.marks.clear();
  }
}

/**
 * Batch updates to reduce re-renders
 * Useful for multiple state updates
 */
export function batchUpdates(callback: () => void): void {
  // React 18+ handles batching automatically
  // This is a helper for explicit control
  callback();
}
