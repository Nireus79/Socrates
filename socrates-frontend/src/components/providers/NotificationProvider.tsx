/**
 * NotificationProvider - Displays notifications from the notification store
 */

import React from 'react';
import { useNotificationStore } from '../../stores/notificationStore';
import { Toast } from '../common';

export const NotificationProvider: React.FC = () => {
  const notifications = useNotificationStore((state) => state.notifications);
  const removeNotification = useNotificationStore((state) => state.removeNotification);

  return (
    <div
      className="fixed top-4 right-4 z-50 space-y-3 pointer-events-none"
      aria-live="polite"
      aria-atomic="true"
    >
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className="pointer-events-auto"
        >
          <Toast
            type={notification.type}
            message={notification.title}
            description={notification.message}
            onClose={() => removeNotification(notification.id)}
            duration={0} // NotificationStore handles duration
          />
        </div>
      ))}
    </div>
  );
};

NotificationProvider.displayName = 'NotificationProvider';
