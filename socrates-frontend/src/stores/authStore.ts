/**
 * Authentication Store - Manages user authentication state
 * Uses Zustand for state management
 * FIXED: Uses centralized apiClient instance for all requests
 */

import { create } from 'zustand';
import axios from 'axios';
import { apiClient } from '../api/client';
import type { User } from '../types/models';

interface AuthStore {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  deleteAccount: () => Promise<void>;
  setTestingMode: (enabled: boolean) => Promise<void>;
  clearError: () => void;
  setUser: (user: User | null) => void;
  restoreAuthFromStorage: () => void;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Helper function to extract user-friendly error message from axios errors
const getErrorMessage = (err: unknown): string => {
  if (axios.isAxiosError(err)) {
    // Check if there's a detail message from the API
    if (err.response?.data?.detail) {
      return err.response.data.detail;
    }
    // Check status code for common errors
    if (err.response?.status === 401) {
      return 'Invalid username or password';
    }
    if (err.response?.status === 400) {
      return err.response.data?.detail || 'Invalid request';
    }
    if (err.response?.status === 500) {
      return 'Server error. Please try again later';
    }
    if (err.message) {
      return err.message;
    }
  }
  if (err instanceof Error) {
    return err.message;
  }
  return 'An error occurred';
};

// Helper function to set auth tokens and user data in both axios and apiClient
const setAuthTokens = (accessToken: string, refreshToken?: string, user?: User | null) => {
  axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
  apiClient.setTokens(accessToken, refreshToken || '');
  localStorage.setItem('access_token', accessToken);
  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken);
  }
  // Persist user data for authentication restoration
  if (user) {
    localStorage.setItem('user', JSON.stringify(user));
  }
};

// Helper function to clear auth tokens and user data
const clearAuthTokens = () => {
  delete axios.defaults.headers.common['Authorization'];
  apiClient.logout();
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isLoading: false,
  error: null,
  isAuthenticated: false,

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      // Create a temporary axios instance for login (no auth header needed)
      const response = await axios.post(`${API_URL}/auth/login`, {
        username,
        password,
      });

      const user: User = response.data.user;
      const accessToken = response.data.access_token;
      const refreshToken = response.data.refresh_token;

      // Store tokens with correct keys in both axios and apiClient
      if (accessToken) {
        setAuthTokens(accessToken, refreshToken, user);
        set({ user, isLoading: false, isAuthenticated: true });
        // Log for debugging
        console.log('[Auth] Login successful, tokens stored:', {
          hasAccessToken: !!localStorage.getItem('access_token'),
          hasRefreshToken: !!localStorage.getItem('refresh_token'),
          apiClientAuthenticated: apiClient.isAuthenticated()
        });
      } else {
        throw new Error('No access token in response');
      }
    } catch (err) {
      const message = getErrorMessage(err);
      set({ error: message, isLoading: false, user: null, isAuthenticated: false });
      throw err;
    }
  },

  register: async (username: string, email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.post(`${API_URL}/auth/register`, {
        username,
        email,
        password,
      });

      const user: User = response.data.user;
      const accessToken = response.data.access_token;
      const refreshToken = response.data.refresh_token;

      // Store tokens with correct keys in both axios and apiClient
      if (accessToken) {
        setAuthTokens(accessToken, refreshToken, user);
        set({ user, isLoading: false, isAuthenticated: true });
      } else {
        throw new Error('No access token in response');
      }
    } catch (err) {
      const message = getErrorMessage(err);
      set({ error: message, isLoading: false, user: null, isAuthenticated: false });
      throw err;
    }
  },

  logout: async () => {
    try {
      // Call logout endpoint
      await axios.post(`${API_URL}/auth/logout`);
    } catch (err) {
      // Even if logout fails, clear local state
      console.warn('Logout API call failed:', err);
    } finally {
      // Clear all auth data locally
      clearAuthTokens();
      set({ user: null, error: null, isAuthenticated: false });
    }
  },

  deleteAccount: async () => {
    set({ isLoading: true, error: null });
    try {
      // Call delete account endpoint
      await apiClient.delete('/auth/me');

      // Clear all auth data locally
      clearAuthTokens();
      set({
        user: null,
        error: null,
        isAuthenticated: false,
        isLoading: false,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete account';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  setTestingMode: async (enabled: boolean) => {
    set({ isLoading: true, error: null });
    try {
      // Call set testing mode endpoint
      await apiClient.put(`/auth/me/testing-mode?enabled=${enabled}`, {});

      // Update user object with testing_mode flag
      set((state) => ({
        user: state.user
          ? {
              ...state.user,
              testing_mode: enabled,
            }
          : null,
        isLoading: false,
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update testing mode';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  clearError: () => {
    set({ error: null });
  },

  setUser: (user: User | null) => {
    set({ user, isAuthenticated: user !== null });
  },

  restoreAuthFromStorage: () => {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    const userData = localStorage.getItem('user');

    if (accessToken) {
      let user: User | null = null;

      // Try to restore user data from localStorage
      if (userData) {
        try {
          user = JSON.parse(userData);
        } catch (e) {
          console.warn('Failed to parse stored user data:', e);
        }
      }

      setAuthTokens(accessToken, refreshToken || undefined, user || undefined);
      set({ user, isAuthenticated: true });
    }
  },
}));

// Restore authentication from storage on app load
useAuthStore.getState().restoreAuthFromStorage();
