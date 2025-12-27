/**
 * GitHub Import Modal - Import repository as project
 */

import React from 'react';
import { AlertCircle, GitBranch, Plus } from 'lucide-react';
import { useGithubStore } from '../../stores';
import { Modal } from '../common';
import { Button } from '../common';
import { Input } from '../common';
import { Card } from '../common';
import { showSuccess, showError } from '../../stores/notificationStore';

interface GitHubImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (projectId: string) => void;
}

export const GitHubImportModal: React.FC<GitHubImportModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { importRepository, isImporting, error } = useGithubStore();
  const [url, setUrl] = React.useState('');
  const [projectName, setProjectName] = React.useState('');
  const [branch, setBranch] = React.useState('main');
  const [validationError, setValidationError] = React.useState<string | null>(null);

  const handleImport = async () => {
    // Validate URL
    if (!url.trim()) {
      setValidationError('GitHub URL is required');
      return;
    }

    if (!url.includes('github.com')) {
      setValidationError('Please enter a valid GitHub repository URL');
      return;
    }

    setValidationError(null);

    try {
      await importRepository(url.trim(), projectName.trim() || undefined);

      // Reset form
      setUrl('');
      setProjectName('');
      setBranch('main');
      showSuccess('Repository Imported', 'GitHub repository has been successfully imported as a new project');
      onClose();
      onSuccess?.(url); // Pass URL as reference
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to import repository. Please check the URL and try again.';
      showError('Failed to Import Repository', errorMessage);
      console.error('Import failed:', err);
    }
  };

  const handleClose = () => {
    setUrl('');
    setProjectName('');
    setBranch('main');
    setValidationError(null);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Import GitHub Repository"
      size="md"
    >
      <div className="space-y-4">
        {/* Error Alert */}
        {(validationError || error) && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md flex gap-2">
            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700 dark:text-red-300">
              {validationError || error}
            </p>
          </div>
        )}

        {/* GitHub URL Input */}
        <div>
          <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
            Repository URL
          </label>
          <Input
            type="text"
            placeholder="https://github.com/user/repository"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isImporting}
            icon={<GitBranch className="h-4 w-4" />}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Example: https://github.com/facebook/react
          </p>
        </div>

        {/* Project Name Input */}
        <div>
          <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
            Project Name (optional)
          </label>
          <Input
            type="text"
            placeholder="Leave blank to use repository name"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            disabled={isImporting}
          />
        </div>

        {/* Branch Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
            Branch
          </label>
          <Input
            type="text"
            placeholder="main"
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            disabled={isImporting}
          />
        </div>

        {/* Info Box */}
        <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <div className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
            <p className="font-medium">What happens next:</p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Repository will be cloned and analyzed</li>
              <li>Code validation will run automatically</li>
              <li>Project will be created with repository linked</li>
              <li>You can pull and push changes anytime</li>
            </ul>
          </div>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-800">
          <Button
            variant="secondary"
            onClick={handleClose}
            disabled={isImporting}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleImport}
            isLoading={isImporting}
          >
            Import
          </Button>
        </div>
      </div>
    </Modal>
  );
};
