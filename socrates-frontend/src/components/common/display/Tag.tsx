/**
 * Tag Component - Colored tag for categories
 */

import React from 'react';

type TagColor = 'blue' | 'purple' | 'pink' | 'green' | 'yellow' | 'red';

interface TagProps extends React.HTMLAttributes<HTMLSpanElement> {
  color?: TagColor;
  icon?: React.ReactNode;
  size?: 'sm' | 'md';
}

const colors: Record<TagColor, string> = {
  blue: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  purple:
    'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  pink: 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300',
  green: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  yellow:
    'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  red: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
};

const sizes = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-3 py-1',
};

export const Tag = React.forwardRef<HTMLSpanElement, TagProps>(
  (
    { color = 'blue', icon, size = 'md', className = '', children, ...props },
    ref
  ) => {
    return (
      <span
        ref={ref}
        className={`inline-flex items-center gap-1 font-medium rounded-md ${colors[color]} ${sizes[size]} ${className}`.trim()}
        {...props}
      >
        {icon && <span>{icon}</span>}
        {children}
      </span>
    );
  }
);

Tag.displayName = 'Tag';
