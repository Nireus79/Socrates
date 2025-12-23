/**
 * Checkbox Component - Checkbox input
 */

import React from 'react';
import { Check } from 'lucide-react';

interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  description?: string;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, description, className = '', ...props }, ref) => {
    const [isChecked, setIsChecked] = React.useState(props.checked || false);

    return (
      <label className="flex items-start gap-3 cursor-pointer">
        <div className="relative mt-1">
          <input
            ref={ref}
            type="checkbox"
            checked={isChecked}
            onChange={(e) => {
              setIsChecked(e.target.checked);
              props.onChange?.(e);
            }}
            className="sr-only"
            {...props}
          />
          <div
            className={`w-5 h-5 rounded border-2 transition-colors ${
              isChecked
                ? 'bg-blue-600 dark:bg-blue-500 border-blue-600 dark:border-blue-500'
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
            }`.trim()}
          >
            {isChecked && (
              <Check size={16} className="text-white absolute top-0.5 left-0.5" />
            )}
          </div>
        </div>
        {(label || description) && (
          <div className="flex-1">
            {label && (
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {label}
              </p>
            )}
            {description && (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {description}
              </p>
            )}
          </div>
        )}
      </label>
    );
  }
);

Checkbox.displayName = 'Checkbox';
