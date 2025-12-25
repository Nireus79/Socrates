/**
 * Notification Store - Manages toast/notification messages
 */

import { create } from 'zustand';

interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message: string;
}

interface NotificationStore {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

export const useNotificationStore = create<NotificationStore>((set) => ({
  notifications: [],

  addNotification: (notification) => {
    const id = Math.random().toString(36).substr(2, 9);
    set((state) => ({
      notifications: [...state.notifications, { ...notification, id }],
    }));

    // Don't auto-dismiss - let user close notifications manually with the X button
    // This ensures users have time to read and interact with the message
  },

  removeNotification: (id) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  clearAll: () => {
    set({ notifications: [] });
  },
}));

// Helper functions
export const showSuccess = (title: string, message: string) => {
  useNotificationStore.getState().addNotification({
    type: 'success',
    title,
    message,
  });
};

export const showError = (title: string, message: string) => {
  useNotificationStore.getState().addNotification({
    type: 'error',
    title,
    message,
  });
};

export const showInfo = (title: string, message: string) => {
  useNotificationStore.getState().addNotification({
    type: 'info',
    title,
    message,
  });
};

export const showWarning = (title: string, message: string) => {
  useNotificationStore.getState().addNotification({
    type: 'warning',
    title,
    message,
  });
};
