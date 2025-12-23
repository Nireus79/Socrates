/**
 * Comprehensive Auth Store Tests - Covers all critical paths
 * Tests token persistence, user restoration, and error handling
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import axios from 'axios';
import { useAuthStore } from '../../stores/authStore';

// Mock axios
vi.mock('axios');

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('useAuthStore - Critical Paths', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    // Reset the auth store state
    const state = useAuthStore.getState();
    state.clearError();
  });

  describe('Login Flow', () => {
    it('should successfully login and persist user + tokens to localStorage', async () => {
      const mockUser = {
        username: 'testuser',
        email: 'test@example.com',
        subscription_tier: 'free',
        testing_mode: false,
      };

      const mockResponse = {
        data: {
          user: mockUser,
          access_token: 'access_token_123',
          refresh_token: 'refresh_token_456',
          token_type: 'bearer',
          expires_in: 900,
        },
      };

      vi.mocked(axios.post).mockResolvedValueOnce(mockResponse);

      const { login } = useAuthStore.getState();
      await login('testuser', 'password123');

      const state = useAuthStore.getState();

      // Check store state
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
      expect(state.error).toBeNull();

      // Check localStorage persistence
      expect(localStorage.getItem('access_token')).toBe('access_token_123');
      expect(localStorage.getItem('refresh_token')).toBe('refresh_token_456');
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockUser));
    });

    it('should show user-friendly error message for invalid credentials (401)', async () => {
      const axiosError = {
        response: {
          status: 401,
          data: {},
        },
        message: 'Request failed with status code 401',
      };

      vi.mocked(axios.post).mockRejectedValueOnce(axiosError);

      const { login } = useAuthStore.getState();

      try {
        await login('testuser', 'wrongpassword');
      } catch (e) {
        // Expected to throw
      }

      const state = useAuthStore.getState();

      // Should show user-friendly message, not raw error
      expect(state.error).toBe('Invalid username or password');
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });

    it('should show error for server error (500)', async () => {
      const axiosError = {
        response: {
          status: 500,
          data: {},
        },
        message: 'Server error',
      };

      vi.mocked(axios.post).mockRejectedValueOnce(axiosError);

      const { login } = useAuthStore.getState();

      try {
        await login('testuser', 'password');
      } catch (e) {
        // Expected
      }

      const state = useAuthStore.getState();
      expect(state.error).toBe('Server error. Please try again later');
    });
  });

  describe('Register Flow', () => {
    it('should successfully register and persist user + tokens', async () => {
      const mockUser = {
        username: 'newuser',
        email: 'new@example.com',
        subscription_tier: 'free',
        testing_mode: false,
      };

      const mockResponse = {
        data: {
          user: mockUser,
          access_token: 'access_token_789',
          refresh_token: 'refresh_token_012',
          token_type: 'bearer',
          expires_in: 900,
        },
      };

      vi.mocked(axios.post).mockResolvedValueOnce(mockResponse);

      const { register } = useAuthStore.getState();
      await register('newuser', 'new@example.com', 'password123');

      const state = useAuthStore.getState();

      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockUser));
    });

    it('should handle registration with duplicate username', async () => {
      const axiosError = {
        response: {
          status: 400,
          data: { detail: 'Username already exists' },
        },
      };

      vi.mocked(axios.post).mockRejectedValueOnce(axiosError);

      const { register } = useAuthStore.getState();

      try {
        await register('existinguser', 'test@example.com', 'password');
      } catch (e) {
        // Expected
      }

      const state = useAuthStore.getState();
      expect(state.error).toBe('Username already exists');
    });
  });

  describe('Token and User Persistence', () => {
    it('should restore user and token from localStorage on app init', () => {
      const mockUser = {
        username: 'persisteduser',
        email: 'persisted@example.com',
        subscription_tier: 'pro',
        testing_mode: true,
      };

      // Simulate previous login
      localStorage.setItem('access_token', 'saved_token_123');
      localStorage.setItem('refresh_token', 'saved_refresh_456');
      localStorage.setItem('user', JSON.stringify(mockUser));

      // Restore auth from storage
      const { restoreAuthFromStorage } = useAuthStore.getState();
      restoreAuthFromStorage();

      const state = useAuthStore.getState();

      // User should be restored
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);

      // Token should be in localStorage
      expect(localStorage.getItem('access_token')).toBe('saved_token_123');
    });

    it('should NOT restore user if localStorage has invalid JSON', () => {
      localStorage.setItem('access_token', 'token_123');
      localStorage.setItem('user', 'INVALID JSON {{{');

      const { restoreAuthFromStorage } = useAuthStore.getState();
      restoreAuthFromStorage();

      const state = useAuthStore.getState();

      // Should not crash, just not restore user
      expect(state.isAuthenticated).toBe(true); // token exists
      expect(state.user).toBeNull(); // user couldn't be parsed
    });

    it('should clear user from localStorage on logout', async () => {
      const mockUser = { username: 'user', email: 'test@example.com', subscription_tier: 'free', testing_mode: false };
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('access_token', 'token_123');

      vi.mocked(axios.post).mockResolvedValueOnce({});

      const { logout } = useAuthStore.getState();
      await logout();

      // All auth data should be cleared
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('Page Refresh Scenario', () => {
    it('should maintain authentication after simulated page refresh', () => {
      // 1. User logs in
      const mockUser = {
        username: 'refreshuser',
        email: 'refresh@example.com',
        subscription_tier: 'free',
        testing_mode: false,
      };

      localStorage.setItem('access_token', 'token_after_login');
      localStorage.setItem('user', JSON.stringify(mockUser));

      // 2. Page refreshes - restore auth
      const { restoreAuthFromStorage } = useAuthStore.getState();
      restoreAuthFromStorage();

      const state = useAuthStore.getState();

      // 3. User should still be authenticated
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);

      // 4. Can access protected resources
      expect(state.user?.username).toBe('refreshuser');
    });
  });

  describe('Error Handling', () => {
    it('should clear error when clearError is called', () => {
      const state = useAuthStore.getState();
      // Manually set error for test
      useAuthStore.setState({ error: 'Some error' });

      state.clearError();

      const updatedState = useAuthStore.getState();
      expect(updatedState.error).toBeNull();
    });

    it('should handle network errors gracefully', async () => {
      const networkError = {
        message: 'Network Error',
        code: 'ERR_NETWORK',
      };

      vi.mocked(axios.post).mockRejectedValueOnce(networkError);

      const { login } = useAuthStore.getState();

      try {
        await login('user', 'pass');
      } catch (e) {
        // Expected
      }

      const state = useAuthStore.getState();
      expect(state.error).toBe('Network Error');
    });
  });

  describe('Edge Cases', () => {
    it('should handle login with special characters in credentials', async () => {
      const mockUser = { username: 'user@domain.com', email: 'special@char.com', subscription_tier: 'free', testing_mode: false };
      const mockResponse = {
        data: {
          user: mockUser,
          access_token: 'token_special_123',
          refresh_token: 'refresh_special_456',
          token_type: 'bearer',
          expires_in: 900,
        },
      };

      vi.mocked(axios.post).mockResolvedValueOnce(mockResponse);

      const { login } = useAuthStore.getState();
      await login('user@domain.com', 'p@ssw0rd!#$%');

      const state = useAuthStore.getState();
      expect(state.user?.username).toBe('user@domain.com');
    });

    it('should handle concurrent login attempts', async () => {
      const mockUser = { username: 'concurrentuser', email: 'concurrent@example.com', subscription_tier: 'free', testing_mode: false };
      const mockResponse = {
        data: {
          user: mockUser,
          access_token: 'token_concurrent',
          refresh_token: 'refresh_concurrent',
          token_type: 'bearer',
          expires_in: 900,
        },
      };

      vi.mocked(axios.post).mockResolvedValue(mockResponse);

      const { login } = useAuthStore.getState();

      // Attempt concurrent logins
      const promise1 = login('concurrentuser', 'pass1');
      const promise2 = login('concurrentuser', 'pass2');

      await Promise.all([promise1, promise2]);

      // Should end in consistent state
      const state = useAuthStore.getState();
      expect(state.user).not.toBeNull();
      expect(state.isAuthenticated).toBe(true);
    });
  });
});
