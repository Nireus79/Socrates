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
     * Cancel shutdown when browser becomes visible again
     */
    const cancelShutdown = () => {
      if (!isScheduledRef.current) return;

      console.log('[ServerLifecycle] Cancelling scheduled shutdown');

      // Clear local timer
      if (shutdownTimerRef.current) {
        clearTimeout(shutdownTimerRef.current);
        shutdownTimerRef.current = null;
      }

      // Call API to cancel server-side shutdown
      apiClient.post('/system/shutdown/cancel').catch((err) => {
        console.warn('[ServerLifecycle] Failed to cancel shutdown:', err);
      });

      isScheduledRef.current = false;
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
     * Handle visibility change (tab switch, minimize, etc.)
     */
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page hidden
        scheduleShutdown();
      } else {
        // Page visible again
        cancelShutdown();
      }
    };

    /**
     * Handle beforeunload (browser close/refresh)
     */
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      scheduleShutdown();
      // Note: Can't reliably make async API calls in beforeunload
      // Relying on visibilitychange as primary trigger
    };

    /**
     * Handle page hide (most reliable)
     */
    const handlePageHide = () => {
      scheduleShutdown();
    };

    // Register event listeners
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('pagehide', handlePageHide);

    // Cleanup
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('pagehide', handlePageHide);

      if (shutdownTimerRef.current) {
        clearTimeout(shutdownTimerRef.current);
      }
    };
  }, [enabled, shutdownDelay]);

  return {
    // Could expose manual trigger methods if needed
  };
}
