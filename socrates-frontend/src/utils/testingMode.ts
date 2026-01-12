/**
 * Testing Mode Utility
 *
 * Manages testing mode state for subscription testing and feature validation.
 * This allows testing of subscription features without actual payment.
 */

export const TestingMode = {
  /**
   * Check if testing mode is currently enabled
   */
  isEnabled(): boolean {
    if (typeof window === 'undefined') return false;

    const testingMode = localStorage.getItem('socrates_testing_mode');
    const expires = localStorage.getItem('socrates_testing_mode_expires');

    if (testingMode !== 'enabled') return false;

    // Check if expired
    if (expires) {
      const expiresAt = parseInt(expires, 10);
      if (Date.now() > expiresAt) {
        // Expired, clean up
        localStorage.removeItem('socrates_testing_mode');
        localStorage.removeItem('socrates_testing_mode_expires');
        return false;
      }
    }

    return true;
  },

  /**
   * Enable testing mode for 24 hours
   */
  enable(): void {
    localStorage.setItem('socrates_testing_mode', 'enabled');
    localStorage.setItem('socrates_testing_mode_expires', (Date.now() + 24 * 60 * 60 * 1000).toString());
    console.log('[TestingMode] Enabled for 24 hours');
  },

  /**
   * Disable testing mode
   */
  disable(): void {
    localStorage.removeItem('socrates_testing_mode');
    localStorage.removeItem('socrates_testing_mode_expires');
    console.log('[TestingMode] Disabled');
  },

  /**
   * Get remaining time in testing mode (in ms)
   */
  getRemainingTime(): number {
    const expires = localStorage.getItem('socrates_testing_mode_expires');
    if (!expires) return 0;

    const expiresAt = parseInt(expires, 10);
    const remaining = expiresAt - Date.now();

    return remaining > 0 ? remaining : 0;
  },

  /**
   * Get remaining time as formatted string
   */
  getRemainingTimeFormatted(): string {
    const ms = this.getRemainingTime();
    if (ms <= 0) return 'Expired';

    const hours = Math.floor(ms / (1000 * 60 * 60));
    const minutes = Math.floor((ms % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) {
      return `${hours}h ${minutes}m remaining`;
    }
    return `${minutes}m remaining`;
  },
};
