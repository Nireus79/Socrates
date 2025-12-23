/**
 * LoadingSpinner Component - Animated loading indicator
 */

import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'white' | 'gray';
  fullScreen?: boolean;
  message?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  color = 'primary',
  fullScreen = false,
  message,
}) => {
  const sizeStyles = {
    sm: 'w-6 h-6 border-2',
    md: 'w-12 h-12 border-3',
    lg: 'w-16 h-16 border-4',
  };

  const colorStyles = {
    primary: 'border-blue-600 border-t-transparent dark:border-blue-400',
    white: 'border-white border-t-transparent',
    gray: 'border-gray-400 border-t-transparent dark:border-gray-600',
  };

  const spinner = (
    <div className="flex flex-col items-center gap-4">
      <div
        className={`animate-spin rounded-full ${sizeStyles[size]} ${colorStyles[color]}`.trim()}
      />
      {message && (
        <p className="text-gray-600 dark:text-gray-400 text-sm">{message}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm z-50">
        {spinner}
      </div>
    );
  }

  return (
    <div className="flex justify-center items-center py-8">
      {spinner}
    </div>
  );
};

LoadingSpinner.displayName = 'LoadingSpinner';
