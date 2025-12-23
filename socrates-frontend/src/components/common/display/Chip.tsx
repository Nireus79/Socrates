/**
 * Chip Component - Small removable tag
 */

import React from 'react';
import { X } from 'lucide-react';

interface ChipProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  onRemove?: () => void;
  removable?: boolean;
  variant?: 'primary' | 'secondary' | 'outline';
  icon?: React.ReactNode;
}

const variants = {
  primary: 'bg-blue-600 dark:bg-blue-500 text-white',
  secondary: 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white',
  outline: 'border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300',
};

export const Chip = React.forwardRef<HTMLDivElement, ChipProps>(
  (
    {
      label,
      onRemove,
      removable = false,
      variant = 'primary',
      icon,
      className = '',
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all ${variants[variant]} ${className}`.trim()}
        {...props}
      >
        {icon && <span>{icon}</span>}
        <span>{label}</span>
        {removable && (
          <button
            onClick={onRemove}
            className="ml-1 hover:opacity-70 transition-opacity"
            aria-label={`Remove ${label}`}
          >
            <X size={16} />
          </button>
        )}
      </div>
    );
  }
);

Chip.displayName = 'Chip';
