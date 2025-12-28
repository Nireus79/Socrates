/**
 * OnlineIndicator Component
 *
 * Small status badge showing user presence state
 */

import React from 'react';

interface OnlineIndicatorProps {
  status?: 'active' | 'idle' | 'offline';
  size?: 'sm' | 'md';
}

export default function OnlineIndicator({ status = 'offline', size = 'md' }: OnlineIndicatorProps) {
  const sizeClasses = size === 'sm' ? 'w-2 h-2' : 'w-3 h-3';
  const positionClasses = size === 'sm' ? 'bottom-0 right-0' : 'bottom-0 right-0';

  const statusColors = {
    active: 'bg-green-500',
    idle: 'bg-yellow-500',
    offline: 'bg-gray-400 dark:bg-gray-600',
  };

  return (
    <div
      className={`absolute ${positionClasses} ${sizeClasses} ${statusColors[status]} rounded-full border-2 border-white dark:border-gray-800`}
      title={status}
    />
  );
}
