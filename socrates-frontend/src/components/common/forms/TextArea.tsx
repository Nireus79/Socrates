/**
 * TextArea Component - Multi-line text input
 */

import React from 'react';

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helpText?: string;
  fullWidth?: boolean;
  resize?: 'none' | 'both' | 'horizontal' | 'vertical';
  rows?: number;
}

export const TextArea = React.forwardRef<HTMLTextAreaElement, TextAreaProps>(
  (
    {
      label,
      error,
      helpText,
      fullWidth = true,
      resize = 'vertical',
      rows = 4,
      disabled,
      className = '',
      ...props
    },
    ref
  ) => {
    const baseStyles = 'w-full px-4 py-2 rounded-lg border transition-colors duration-200 font-mono text-sm disabled:bg-gray-100 disabled:cursor-not-allowed dark:bg-gray-800 dark:text-white';

    const borderStyles = error
      ? 'border-red-500 focus:border-red-600 focus:ring-2 focus:ring-red-200 dark:focus:ring-red-900'
      : 'border-gray-300 dark:border-gray-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-900';

    const resizeStyles = {
      none: 'resize-none',
      both: 'resize',
      horizontal: 'resize-x',
      vertical: 'resize-y',
    };

    const widthStyle = fullWidth ? 'w-full' : '';

    return (
      <div className={widthStyle}>
        {label && (
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {label}
          </label>
        )}

        <textarea
          ref={ref}
          disabled={disabled}
          rows={rows}
          className={`${baseStyles} ${borderStyles} ${resizeStyles[resize]} ${className}`.trim()}
          {...props}
        />

        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
        )}

        {helpText && !error && (
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{helpText}</p>
        )}
      </div>
    );
  }
);

TextArea.displayName = 'TextArea';
