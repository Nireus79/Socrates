/**
 * Input Component - Text input field
 * Supports label, error state, and help text
 */

import React from 'react';
import { AlertCircle } from 'lucide-react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helpText?: string;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helpText,
      icon,
      iconPosition = 'left',
      fullWidth = false,
      disabled,
      className = '',
      ...props
    },
    ref
  ) => {
    const inputBaseStyles = 'w-full px-4 py-2 rounded-lg border transition-colors duration-200 disabled:bg-gray-100 disabled:cursor-not-allowed dark:bg-gray-800 dark:text-white';

    const inputBorderStyles = error
      ? 'border-red-500 focus:border-red-600 focus:ring-2 focus:ring-red-200 dark:focus:ring-red-900'
      : 'border-gray-300 dark:border-gray-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-900';

    const containerWidth = fullWidth ? 'w-full' : '';
    const iconContainerStyle = icon ? (iconPosition === 'left' ? 'pl-10' : 'pr-10') : '';
    const relativePadding = icon ? 'relative' : '';

    return (
      <div className={containerWidth}>
        {label && (
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {label}
          </label>
        )}

        <div className={relativePadding}>
          {icon && iconPosition === 'left' && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400">
              {icon}
            </div>
          )}

          <input
            ref={ref}
            disabled={disabled}
            className={`${inputBaseStyles} ${inputBorderStyles} ${iconContainerStyle} ${className}`.trim()}
            {...props}
          />

          {icon && iconPosition === 'right' && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400">
              {icon}
            </div>
          )}
        </div>

        {error && (
          <div className="flex items-center gap-1 mt-2 text-red-600 dark:text-red-400 text-sm">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {helpText && !error && (
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{helpText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
