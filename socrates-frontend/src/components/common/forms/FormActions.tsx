/**
 * FormActions Component - Submit and Cancel buttons for forms
 */

import React from 'react';
import { Button } from '../interactive';

interface FormActionsProps {
  onSubmit?: () => void;
  onCancel?: () => void;
  submitLabel?: string;
  cancelLabel?: string;
  isLoading?: boolean;
  isDisabled?: boolean;
  variant?: 'default' | 'compact';
}

export const FormActions: React.FC<FormActionsProps> = ({
  onSubmit,
  onCancel,
  submitLabel = 'Submit',
  cancelLabel = 'Cancel',
  isLoading = false,
  isDisabled = false,
  variant = 'default',
}) => {
  const buttonClass = variant === 'compact' ? 'gap-2' : 'gap-3';

  return (
    <div className={`flex justify-end ${buttonClass}`}>
      {onCancel && (
        <Button
          variant="ghost"
          onClick={onCancel}
          disabled={isLoading || isDisabled}
        >
          {cancelLabel}
        </Button>
      )}
      <Button
        variant="primary"
        onClick={onSubmit}
        isLoading={isLoading}
        disabled={isLoading || isDisabled}
      >
        {submitLabel}
      </Button>
    </div>
  );
};

FormActions.displayName = 'FormActions';
