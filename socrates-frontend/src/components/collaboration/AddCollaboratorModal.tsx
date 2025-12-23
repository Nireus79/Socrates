/**
 * AddCollaboratorModal Component - Form to add collaborator to project
 */

import React from 'react';
import { UserPlus } from 'lucide-react';
import {
  Modal,
  Input,
  Select,
  FormField,
  FormActions,
  Alert,
} from '../common';
import { showSuccess, showError } from '../../stores/notificationStore';

interface AddCollaboratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (email: string, role: string) => Promise<void>;
  isLoading?: boolean;
}

export const AddCollaboratorModal: React.FC<AddCollaboratorModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
}) => {
  const [email, setEmail] = React.useState('');
  const [role, setRole] = React.useState('editor');
  const [error, setError] = React.useState('');
  const [success, setSuccess] = React.useState('');

  const validateEmail = (email: string): boolean => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  };

  const handleSubmit = async () => {
    setError('');
    setSuccess('');

    if (!email.trim()) {
      setError('Email is required');
      return;
    }

    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }

    try {
      await onSubmit(email, role);
      setSuccess(`Invitation sent to ${email}`);
      showSuccess('Collaborator Invited', `Invitation sent to ${email}`);
      setTimeout(() => {
        setEmail('');
        setRole('editor');
        onClose();
      }, 1500);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to add collaborator. Please try again.';
      setError(errorMessage);
      showError('Failed to Add Collaborator', errorMessage);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add Collaborator"
      size="md"
    >
      <div className="space-y-4">
        {error && (
          <Alert type="error" title="Error">
            {error}
          </Alert>
        )}

        {success && (
          <Alert type="success" title="Success">
            {success}
          </Alert>
        )}

        <FormField
          label="Email Address"
          required
          help="Enter the email of the person you want to invite"
        >
          <Input
            type="email"
            placeholder="colleague@example.com"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setError('');
            }}
            disabled={isLoading}
            icon={<UserPlus className="h-4 w-4" />}
          />
        </FormField>

        <FormField
          label="Role"
          help="Choose what permissions this collaborator will have"
        >
          <Select
            options={[
              { value: 'viewer', label: 'Viewer - View only access' },
              { value: 'editor', label: 'Editor - Can edit and comment' },
            ]}
            value={role}
            onChange={(e) => setRole(e.target.value)}
            disabled={isLoading}
          />
        </FormField>

        {/* Role Permissions */}
        <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-medium text-gray-900 dark:text-white mb-3">
            Permissions for <span className="capitalize">{role}</span>:
          </p>
          <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
            <li>✓ View project details and progress</li>
            {role === 'editor' && (
              <>
                <li>✓ Contribute to dialogue sessions</li>
                <li>✓ Generate and review code</li>
                <li>✓ Add notes and comments</li>
              </>
            )}
          </ul>
        </div>

        <FormActions
          onSubmit={handleSubmit}
          onCancel={onClose}
          submitLabel="Send Invitation"
          isLoading={isLoading}
        />
      </div>
    </Modal>
  );
};

AddCollaboratorModal.displayName = 'AddCollaboratorModal';
