/**
 * CreateProjectModal Component - Form to create new project
 */

import React from 'react';
import { Modal, Input, TextArea, Select, FormField, FormActions, Alert } from '../common';
import { showError, showSuccess } from '../../stores/notificationStore';

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ProjectFormData) => Promise<void>;
  isLoading?: boolean;
}

export interface ProjectFormData {
  name: string;
  type: string;
  description: string;
  knowledgeBase?: string;
}

const projectTypes = [
  { value: 'software', label: 'Software Development' },
  { value: 'business', label: 'Business Strategy' },
  { value: 'creative', label: 'Creative Project' },
  { value: 'research', label: 'Research' },
  { value: 'marketing', label: 'Marketing Campaign' },
  { value: 'educational', label: 'Educational Content' },
];

export const CreateProjectModal: React.FC<CreateProjectModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
}) => {
  const [formData, setFormData] = React.useState<ProjectFormData>({
    name: '',
    type: 'software',
    description: '',
    knowledgeBase: '',
  });
  const [errors, setErrors] = React.useState<Record<string, string>>({});
  const [apiError, setApiError] = React.useState<string | null>(null);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Project name is required';
    }
    if (!formData.type) {
      newErrors.type = 'Project type is required';
    }
    if (!formData.description.trim()) {
      newErrors.description = 'Project description/topic is required to generate questions';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (validateForm()) {
      setApiError(null);
      try {
        await onSubmit(formData);
        setFormData({ name: '', type: 'software', description: '', knowledgeBase: '' });
        showSuccess('Success', 'Project created successfully');
        onClose();
      } catch (error) {
        let errorMessage = error instanceof Error ? error.message : 'Failed to create project';
        const newErrors: Record<string, string> = {};

        // Parse error message to identify which field failed
        if (errorMessage.includes('name') || errorMessage.includes('Project name')) {
          newErrors.name = 'Project name is required';
        } else if (errorMessage.includes('description') || errorMessage.includes('topic')) {
          newErrors.description = 'Project description/topic is required to generate questions';
        } else if (errorMessage.includes('type')) {
          newErrors.type = 'Project type is required';
        }

        // If we identified field errors, show them; otherwise show generic error
        if (Object.keys(newErrors).length > 0) {
          setErrors(newErrors);
        } else {
          // Format error message for better readability
          let displayMessage = errorMessage;
          if (errorMessage.includes('limit') && errorMessage.includes('free tier')) {
            displayMessage = `${errorMessage}\n\nUpgrade your account to create more projects or delete an existing project.`;
          }
          setApiError(displayMessage);
        }

        showError('Failed to Create Project', errorMessage);
        console.error('Error creating project:', error);
      }
    }
  };

  const handleFieldChange = (field: keyof ProjectFormData, value: string) => {
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
      title="Create New Project"
      size="md"
    >
      <div className="space-y-4">
        {apiError && (
          <Alert type="error" title="Error">
            <p>{apiError}</p>
          </Alert>
        )}

        <FormField
          label="Project Name"
          required
          error={errors.name}
        >
          <Input
            placeholder="e.g., AI Chat Application"
            value={formData.name}
            onChange={(e) => handleFieldChange('name', e.target.value)}
            disabled={isLoading}
          />
        </FormField>

        <FormField
          label="Project Type"
          required
          error={errors.type}
        >
          <Select
            options={projectTypes}
            value={formData.type}
            onChange={(e) => handleFieldChange('type', e.target.value)}
            disabled={isLoading}
          />
        </FormField>

        <FormField
          label="Description"
          required
          help="Brief description of your project topic (needed to generate questions)"
          error={errors.description}
        >
          <TextArea
            placeholder="Describe your project goals and context..."
            value={formData.description}
            onChange={(e) => handleFieldChange('description', e.target.value)}
            rows={4}
            disabled={isLoading}
          />
        </FormField>

        <FormField
          label="Initial Knowledge Base"
          help="Paste any initial context, documentation, or requirements"
        >
          <TextArea
            placeholder="Add any existing documentation, requirements, or context..."
            value={formData.knowledgeBase}
            onChange={(e) => handleFieldChange('knowledgeBase', e.target.value)}
            rows={4}
            disabled={isLoading}
          />
        </FormField>

        <FormActions
          onSubmit={handleSubmit}
          onCancel={onClose}
          submitLabel="Create Project"
          isLoading={isLoading}
        />
      </div>
    </Modal>
  );
};

CreateProjectModal.displayName = 'CreateProjectModal';
