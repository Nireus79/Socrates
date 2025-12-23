/**
 * UI Store - UI state management (modals, notifications, etc.)
 */

import { create } from 'zustand';

interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message: string;
  duration?: number;
}

interface UIState {
  // Modals
  modals: Record<string, boolean>;
  openModal: (name: string) => void;
  closeModal: (name: string) => void;
  toggleModal: (name: string) => void;

  // Notifications
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;

  // Loading states
  isPageLoading: boolean;
  setPageLoading: (loading: boolean) => void;

  // Sidebar
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  // Theme
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIState>((set) => ({
  // Modals
  modals: {},

  openModal: (name: string) => {
    set((state) => ({
      modals: { ...state.modals, [name]: true },
    }));
  },

  closeModal: (name: string) => {
    set((state) => ({
      modals: { ...state.modals, [name]: false },
    }));
  },

  toggleModal: (name: string) => {
    set((state) => ({
      modals: { ...state.modals, [name]: !state.modals[name] },
    }));
  },

  // Notifications
  notifications: [],

  addNotification: (notification: Omit<Notification, 'id'>) => {
    const id = `notification_${Date.now()}`;
    set((state) => ({
      notifications: [...state.notifications, { ...notification, id }],
    }));

    // Auto-remove notification after duration
    if (notification.duration !== undefined && notification.duration > 0) {
      setTimeout(() => {
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        }));
      }, notification.duration);
    }
  },

  removeNotification: (id: string) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  // Loading states
  isPageLoading: false,

  setPageLoading: (loading: boolean) => {
    set({ isPageLoading: loading });
  },

  // Sidebar
  isSidebarOpen: true,

  toggleSidebar: () => {
    set((state) => ({
      isSidebarOpen: !state.isSidebarOpen,
    }));
  },

  setSidebarOpen: (open: boolean) => {
    set({ isSidebarOpen: open });
  },

  // Theme
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

/**
 * Helper function to show success notification
 */
export const showSuccess = (title: string, message: string) => {
  useUIStore.getState().addNotification({
    type: 'success',
    title,
    message,
    duration: 3000,
  });
};

/**
 * Helper function to show error notification
 */
export const showError = (title: string, message: string) => {
  useUIStore.getState().addNotification({
    type: 'error',
    title,
    message,
    duration: 5000,
  });
};

/**
 * Helper function to show info notification
 */
export const showInfo = (title: string, message: string) => {
  useUIStore.getState().addNotification({
    type: 'info',
    title,
    message,
    duration: 3000,
  });
};

/**
 * Helper function to show warning notification
 */
export const showWarning = (title: string, message: string) => {
  useUIStore.getState().addNotification({
    type: 'warning',
    title,
    message,
    duration: 4000,
  });
};
