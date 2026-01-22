/**
 * Hook for managing server lifecycle based on browser events
 *
 * Handles:
 * - Browser close detection (with 1-minute delay)
 * - Tab visibility changes
 * - Graceful shutdown scheduling
 */
import { useEffect, useRef } from 'react';
import { apiClient } from '../api/client';

interface UseServerLifecycleOptions {
  enabled?: boolean;
  shutdownDelay?: number; // milliseconds
}

export function useServerLifecycle(options: UseServerLifecycleOptions = {}) {
  const { enabled = true, shutdownDelay = 300000 } = options; // 300 seconds (5 minutes) default
  const shutdownTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isScheduledRef = useRef(false);

  useEffect(() => {
    if (!enabled) return;

    /**
     * Schedule shutdown after browser becomes hidden
     */
    const scheduleShutdown = () => {
      if (isScheduledRef.current) return; // Already scheduled

      console.log('[ServerLifecycle] Scheduling server shutdown...');

      // Set local timer to track client-side
      shutdownTimerRef.current = setTimeout(() => {
        console.log('[ServerLifecycle] Executing shutdown after delay');
        executeShutdown();
      }, shutdownDelay);

      // Call API to schedule server-side shutdown
      apiClient
        .post('/system/shutdown', null, {
          params: { delay_seconds: Math.floor(shutdownDelay / 1000) },
        })
        .catch((err) => {
          console.warn('[ServerLifecycle] Failed to schedule shutdown:', err);
        });

      isScheduledRef.current = true;
    };

    /**
     * Execute immediate shutdown
     */
    const executeShutdown = () => {
      // Final shutdown - no delay
      apiClient
        .post('/system/shutdown', null, {
          params: { delay_seconds: 0 },
        })
        .catch((err) => {
          console.warn('[ServerLifecycle] Failed to execute immediate shutdown:', err);
        });
    };

    /**
     * Handle page hide (most reliable indicator of actual browser close)
     * Triggers when:
     * - Browser window is closed
     * - Browser tab is closed
     * - Browser application is terminated
     *
     * Does NOT trigger when:
     * - User switches to another tab (visibilitychange only)
     * - User minimizes window (visibilitychange only)
     */
    const handlePageHide = () => {
      console.log('[ServerLifecycle] Page hide detected - scheduling shutdown');
      scheduleShutdown();
    };

    /**
     * Handle beforeunload as fallback for browser close detection
     */
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      console.log('[ServerLifecycle] Before unload detected - scheduling shutdown');
      scheduleShutdown();
    };

    // Register event listeners for ACTUAL browser close only
    // NOTE: Deliberately NOT using visibilitychange to avoid shutdown when user
    // just switches tabs or minimizes window
    window.addEventListener('pagehide', handlePageHide);
    window.addEventListener('beforeunload', handleBeforeUnload);

    // Cleanup
    return () => {
      window.removeEventListener('pagehide', handlePageHide);
      window.removeEventListener('beforeunload', handleBeforeUnload);

      if (shutdownTimerRef.current) {
        clearTimeout(shutdownTimerRef.current);
      }
    };
  }, [enabled, shutdownDelay]);

  return {
    // Could expose manual trigger methods if needed
  };
}
