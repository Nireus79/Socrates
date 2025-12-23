/**
 * Badge Component - Status/tag badge
 */

import React from 'react';

type BadgeVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
}

const variants: Record<BadgeVariant, string> = {
  primary: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  secondary: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300',
  success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  info: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-300',
};

const sizes = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-1',
};

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  (
    { variant = 'primary', size = 'md', className = '', children, ...props },
    ref
  ) => {
    return (
      <span
        ref={ref}
        className={`inline-flex items-center font-medium rounded-full ${variants[variant]} ${sizes[size]} ${className}`.trim()}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';
