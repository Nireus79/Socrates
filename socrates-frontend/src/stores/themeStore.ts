/**
 * Theme Store - Manages application theme (light/dark mode)
 */

import { create } from 'zustand';

interface ThemeStore {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useThemeStore = create<ThemeStore>((set) => ({
  theme: 'light',

  toggleTheme: () => {
    set((state) => ({
      theme: state.theme === 'light' ? 'dark' : 'light',
    }));
  },

  setTheme: (theme: 'light' | 'dark') => {
    set({ theme });
  },
}));
