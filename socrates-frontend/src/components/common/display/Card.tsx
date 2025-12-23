/**
 * Card Component - Container for content
 * Provides consistent styling and padding
 */

import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  padding?: 'sm' | 'md' | 'lg' | 'none';
  shadow?: 'sm' | 'md' | 'lg' | 'none';
  border?: boolean;
  hoverable?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      padding = 'md',
      shadow = 'md',
      border = true,
      hoverable = false,
      className = '',
      children,
      ...props
    },
    ref
  ) => {
    const paddingStyles = {
      sm: 'p-3',
      md: 'p-6',
      lg: 'p-8',
      none: 'p-0',
    };

    const shadowStyles = {
      sm: 'shadow-sm',
      md: 'shadow-md',
      lg: 'shadow-lg',
      none: 'shadow-none',
    };

    const baseStyles = 'bg-white dark:bg-gray-900 rounded-lg transition-all duration-200';
    const borderStyle = border ? 'border border-gray-200 dark:border-gray-800' : '';
    const hoverStyle = hoverable ? 'hover:shadow-lg hover:scale-105 dark:hover:shadow-xl cursor-pointer' : '';

    return (
      <div
        ref={ref}
        className={`${baseStyles} ${paddingStyles[padding]} ${shadowStyles[shadow]} ${borderStyle} ${hoverStyle} ${className}`.trim()}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';
