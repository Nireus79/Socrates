/**
 * EditProjectModal Component - Form to edit existing project
 */

import React from 'react';
import { Modal, Input, TextArea, FormField, FormActions } from '../common';
import type { Project } from '../../types/models';

interface EditProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: EditProjectData) => Promise<void>;
  project: Project | null;
  isLoading?: boolean;
}

export interface EditProjectData {
  name: string;
  description: string;
}

export const EditProjectModal: React.FC<EditProjectModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  project,
  isLoading = false,
}) => {
  const [formData, setFormData] = React.useState<EditProjectData>({
    name: '',
    description: '',
  });
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  // Initialize form with project data when modal opens
  React.useEffect(() => {
    if (isOpen && project) {
      setFormData({
        name: project.name,
        description: project.description || '',
      });
      setErrors({});
    }
  }, [isOpen, project]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Project name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (validateForm()) {
      try {
        await onSubmit(formData);
        onClose();
      } catch (error) {
        console.error('Error updating project:', error);
      }
    }
  };

  const handleFieldChange = (field: keyof EditProjectData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Edit Project"
      size="md"
    >
      <div className="space-y-4">
        <FormField
          label="Project Name"
          required
          error={errors.name}
        >
          <Input
            placeholder="Enter project name"
            value={formData.name}
            onChange={(e) => handleFieldChange('name', e.target.value)}
            disabled={isLoading}
          />
        </FormField>

        <FormField
          label="Description"
          help="Brief description of your project"
        >
          <TextArea
            placeholder="Describe your project goals and context..."
            value={formData.description}
            onChange={(e) => handleFieldChange('description', e.target.value)}
            rows={4}
            disabled={isLoading}
          />
        </FormField>

        <FormActions
          onSubmit={handleSubmit}
          onCancel={onClose}
          submitLabel="Save Changes"
          isLoading={isLoading}
        />
      </div>
    </Modal>
  );
};

EditProjectModal.displayName = 'EditProjectModal';
