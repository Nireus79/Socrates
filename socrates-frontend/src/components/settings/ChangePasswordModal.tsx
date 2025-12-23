/**
 * Change Password Modal - Allow users to change their password
 */

import React from 'react';
import { AlertCircle, Lock, CheckCircle, Eye, EyeOff } from 'lucide-react';
import { Modal } from '../common';
import { Input } from '../common';
import { Alert } from '../common';
import { Button } from '../common';

interface ChangePasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm?: (currentPassword: string, newPassword: string) => Promise<void>;
  isLoading?: boolean;
}

export const ChangePasswordModal: React.FC<ChangePasswordModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  isLoading = false,
}) => {
  const [currentPassword, setCurrentPassword] = React.useState('');
  const [newPassword, setNewPassword] = React.useState('');
  const [confirmPassword, setConfirmPassword] = React.useState('');
  const [showPasswords, setShowPasswords] = React.useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [validationError, setValidationError] = React.useState<string | null>(null);
  const [isSuccess, setIsSuccess] = React.useState(false);

  const validatePassword = (password: string): string | null => {
    if (password.length < 8) {
      return 'Password must be at least 8 characters';
    }
    if (!/[A-Z]/.test(password)) {
      return 'Password must contain at least one uppercase letter';
    }
    if (!/\d/.test(password)) {
      return 'Password must contain at least one digit';
    }
    return null;
  };

  const handleChangePassword = async () => {
    setValidationError(null);

    if (!currentPassword.trim()) {
      setValidationError('Current password is required');
      return;
    }

    if (!newPassword.trim()) {
      setValidationError('New password is required');
      return;
    }

    const passwordError = validatePassword(newPassword);
    if (passwordError) {
      setValidationError(passwordError);
      return;
    }

    if (newPassword !== confirmPassword) {
      setValidationError('New passwords do not match');
      return;
    }

    if (currentPassword === newPassword) {
      setValidationError('New password must be different from current password');
      return;
    }

    try {
      await onConfirm?.(currentPassword, newPassword);
      setIsSuccess(true);
      setTimeout(() => {
        resetForm();
        onClose();
      }, 1500);
    } catch (err) {
      setValidationError(err instanceof Error ? err.message : 'Failed to change password');
    }
  };

  const resetForm = () => {
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setValidationError(null);
    setIsSuccess(false);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Change Password"
      size="md"
    >
      {isSuccess ? (
        <div className="text-center py-8">
          <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Password Changed
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Your password has been updated successfully
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {validationError && (
            <Alert type="error" closeable onClose={() => setValidationError(null)}>
              {validationError}
            </Alert>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
              Current Password
            </label>
            <div className="relative">
              <Input
                type={showPasswords.current ? 'text' : 'password'}
                placeholder="Enter your current password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                disabled={isLoading}
                icon={
                  <button
                    type="button"
                    onClick={() =>
                      setShowPasswords({
                        ...showPasswords,
                        current: !showPasswords.current,
                      })
                    }
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    {showPasswords.current ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                }
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
              New Password
            </label>
            <div className="relative">
              <Input
                type={showPasswords.new ? 'text' : 'password'}
                placeholder="Enter your new password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                disabled={isLoading}
                icon={
                  <button
                    type="button"
                    onClick={() =>
                      setShowPasswords({
                        ...showPasswords,
                        new: !showPasswords.new,
                      })
                    }
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    {showPasswords.new ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                }
              />
            </div>
            <div className="mt-2 text-xs text-gray-600 dark:text-gray-400 space-y-1">
              <p>Password must contain:</p>
              <ul className="list-disc pl-5">
                <li>At least 8 characters</li>
                <li>At least one uppercase letter</li>
                <li>At least one digit</li>
              </ul>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
              Confirm New Password
            </label>
            <Input
              type={showPasswords.confirm ? 'text' : 'password'}
              placeholder="Confirm your new password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isLoading}
              icon={
                <button
                  type="button"
                  onClick={() =>
                    setShowPasswords({
                      ...showPasswords,
                      confirm: !showPasswords.confirm,
                    })
                  }
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  {showPasswords.confirm ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              }
            />
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {!isSuccess && (
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-800 mt-4">
          <Button
            variant="secondary"
            onClick={handleClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleChangePassword}
            isLoading={isLoading}
          >
            Change Password
          </Button>
        </div>
      )}
    </Modal>
  );
};
