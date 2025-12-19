/**
 * Authentication Store - Manages user authentication state
 * Uses Zustand for state management
 * FIXED: Uses correct token keys (access_token/refresh_token) matching API response
 */

import { create } from 'zustand';
import axios from 'axios';

interface User {
  id: string;
  username: string;
  email: string;
  subscription_tier: string;
}

interface AuthStore {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  setUser: (user: User | null) => void;
  restoreAuthFromStorage: () => void;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Helper function to set auth headers
const setAuthHeaders = (accessToken: string) => {
  axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
  localStorage.setItem('access_token', accessToken);
};

// Helper function to clear auth headers
const clearAuthHeaders = () => {
  delete axios.defaults.headers.common['Authorization'];
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isLoading: false,
  error: null,
  isAuthenticated: false,

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        username,
        password,
      });

      const user: User = response.data.user;
      const accessToken = response.data.access_token;
      const refreshToken = response.data.refresh_token;

      // Store tokens with correct keys
      if (accessToken) {
        setAuthHeaders(accessToken);
        if (refreshToken) {
          localStorage.setItem('refresh_token', refreshToken);
        }
        set({ user, isLoading: false, isAuthenticated: true });
      } else {
        throw new Error('No access token in response');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
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

      // Store tokens with correct keys
      if (accessToken) {
        setAuthHeaders(accessToken);
        if (refreshToken) {
          localStorage.setItem('refresh_token', refreshToken);
        }
        set({ user, isLoading: false, isAuthenticated: true });
      } else {
        throw new Error('No access token in response');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed';
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
      clearAuthHeaders();
      set({ user: null, error: null, isAuthenticated: false });
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
    if (accessToken) {
      setAuthHeaders(accessToken);
      set({ isAuthenticated: true });
    }
  },
}));

// Restore authentication from storage on app load
useAuthStore.getState().restoreAuthFromStorage();
