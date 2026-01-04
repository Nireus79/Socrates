/**
 * Debug Store - Global debug mode state management
 */

import { create } from 'zustand';

interface DebugState {
  debugEnabled: boolean;
  lastToggleTime: string | null;

  // Actions
  setDebugMode: (enabled: boolean) => void;
  toggleDebugMode: () => void;
  reset: () => void;
}

export const useDebugStore = create<DebugState>((set) => ({
  // Initial state
  debugEnabled: false,
  lastToggleTime: null,

  // Set debug mode explicitly
  setDebugMode: (enabled: boolean) => {
    set({
      debugEnabled: enabled,
      lastToggleTime: new Date().toISOString(),
    });
  },

  // Toggle debug mode
  toggleDebugMode: () => {
    set((state) => ({
      debugEnabled: !state.debugEnabled,
      lastToggleTime: new Date().toISOString(),
    }));
  },

  // Reset state
  reset: () => {
    set({
      debugEnabled: false,
      lastToggleTime: null,
    });
  },
}));
