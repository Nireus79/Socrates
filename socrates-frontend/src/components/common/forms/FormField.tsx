/**
 * FormField Component - Wrapper for label + input + error message
 */

import React from 'react';

interface FormFieldProps {
  label?: string;
  error?: string;
  help?: string;
  required?: boolean;
  children: React.ReactNode;
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  error,
  help,
  required,
  children,
}) => {
  return (
    <div className="w-full space-y-1">
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
          {required && <span className="ml-1 text-red-500">*</span>}
        </label>
      )}

      <div>{children}</div>

      {error && (
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      )}

      {help && !error && (
        <p className="text-sm text-gray-500 dark:text-gray-400">{help}</p>
      )}
    </div>
  );
};

FormField.displayName = 'FormField';
