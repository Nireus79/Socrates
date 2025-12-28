/**
 * Unit tests for notification store
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useNotificationStore, showSuccess, showError, showInfo, showWarning } from './notificationStore';

describe('Notification Store', () => {
  beforeEach(() => {
    // Reset store before each test
    useNotificationStore.setState({
      notifications: [],
    });
  });

  it('should add a success notification', () => {
    showSuccess('Test Title', 'Test Message');

    const state = useNotificationStore.getState();
    expect(state.notifications).toHaveLength(1);
    expect(state.notifications[0]).toMatchObject({
      type: 'success',
      title: 'Test Title',
      message: 'Test Message',
    });
  });

  it('should add an error notification', () => {
    showError('Error Title', 'Error Message');

    const state = useNotificationStore.getState();
    expect(state.notifications).toHaveLength(1);
    expect(state.notifications[0]).toMatchObject({
      type: 'error',
      title: 'Error Title',
      message: 'Error Message',
    });
  });

  it('should add info and warning notifications', () => {
    showInfo('Info Title', 'Info Message');
    showWarning('Warning Title', 'Warning Message');

    const state = useNotificationStore.getState();
    expect(state.notifications).toHaveLength(2);
    expect(state.notifications[0].type).toBe('info');
    expect(state.notifications[1].type).toBe('warning');
  });

  it('should remove a notification by id', () => {
    showSuccess('Title 1', 'Message 1');
    showSuccess('Title 2', 'Message 2');

    const state = useNotificationStore.getState();
    const firstId = state.notifications[0].id;

    useNotificationStore.getState().removeNotification(firstId);

    const updatedState = useNotificationStore.getState();
    expect(updatedState.notifications).toHaveLength(1);
    expect(updatedState.notifications[0].id).not.toBe(firstId);
  });

  it('should clear all notifications', () => {
    showSuccess('Title 1', 'Message 1');
    showError('Title 2', 'Message 2');
    showInfo('Title 3', 'Message 3');

    expect(useNotificationStore.getState().notifications).toHaveLength(3);

    useNotificationStore.getState().clearAll();

    expect(useNotificationStore.getState().notifications).toHaveLength(0);
  });

  it('should generate unique IDs for notifications', () => {
    showSuccess('Title 1', 'Message 1');
    showSuccess('Title 2', 'Message 2');
    showSuccess('Title 3', 'Message 3');

    const state = useNotificationStore.getState();
    const ids = state.notifications.map((n) => n.id);
    const uniqueIds = new Set(ids);

    expect(uniqueIds.size).toBe(3);
  });
});
