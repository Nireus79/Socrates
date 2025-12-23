/**
 * RadioGroup Component - Radio button group
 */

import React from 'react';

interface RadioOption {
  value: string;
  label: string;
  description?: string;
}

interface RadioGroupProps {
  name: string;
  options: RadioOption[];
  value?: string;
  onChange?: (value: string) => void;
  label?: string;
  orientation?: 'vertical' | 'horizontal';
}

export const RadioGroup: React.FC<RadioGroupProps> = ({
  name,
  options,
  value,
  onChange,
  label,
  orientation = 'vertical',
}) => {
  const orientationClass = orientation === 'horizontal' ? 'flex gap-6' : 'space-y-3';

  return (
    <fieldset>
      {label && (
        <legend className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          {label}
        </legend>
      )}
      <div className={orientationClass}>
        {options.map((option) => (
          <label
            key={option.value}
            className="flex items-start gap-3 cursor-pointer"
          >
            <div className="relative mt-1">
              <input
                type="radio"
                name={name}
                value={option.value}
                checked={value === option.value}
                onChange={(e) => onChange?.(e.target.value)}
                className="sr-only"
              />
              <div
                className={`w-5 h-5 rounded-full border-2 transition-colors ${
                  value === option.value
                    ? 'bg-blue-600 dark:bg-blue-500 border-blue-600 dark:border-blue-500'
                    : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
                }`.trim()}
              >
                {value === option.value && (
                  <div className="absolute top-1 left-1 w-1.5 h-1.5 bg-white rounded-full" />
                )}
              </div>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {option.label}
              </p>
              {option.description && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {option.description}
                </p>
              )}
            </div>
          </label>
        ))}
      </div>
    </fieldset>
  );
};

RadioGroup.displayName = 'RadioGroup';
