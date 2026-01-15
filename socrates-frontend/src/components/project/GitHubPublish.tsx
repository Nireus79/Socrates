/**
 * GitHubPublish Component
 *
 * Allows users to publish generated projects directly to GitHub
 * with automatic repository creation and code push
 */

import React, { useState } from 'react';
import {
  AlertCircle,
  Check,
  Loader,
  Lock,
  Unlock,
  Github,
  X,
  ExternalLink,
} from 'lucide-react';
import { Dialog, Button, Alert, Input } from '../common';

interface GitHubPublishProps {
  projectId: string;
  projectName: string;
  onClose: () => void;
  onSuccess: (repoUrl: string) => void;
  onError: (error: string) => void;
}

interface PublishFormData {
  repoName: string;
  description: string;
  isPrivate: boolean;
  githubToken: string;
}

export const GitHubPublish: React.FC<GitHubPublishProps> = ({
  projectId,
  projectName,
  onClose,
  onSuccess,
  onError,
}) => {
  const [formData, setFormData] = useState<PublishFormData>({
    repoName: projectName.toLowerCase().replace(/\s+/g, '-'),
    description: '',
    isPrivate: true,
    githubToken: localStorage.getItem('github_token') || '',
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [successData, setSuccessData] = useState<{ repoUrl: string } | null>(null);

  const handleInputChange = (field: keyof PublishFormData, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handlePublish = async () => {
    // Validate required fields
    if (!formData.repoName.trim()) {
      setError('Repository name is required');
      return;
    }

    if (!formData.githubToken.trim()) {
      setError('GitHub token is required');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(false);

    try {
      // Save token for future use
      localStorage.setItem('github_token', formData.githubToken);

      // Call the publish API endpoint
      const response = await fetch(
        `/api/projects/${projectId}/publish-to-github`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`,
          },
          body: JSON.stringify({
            repo_name: formData.repoName,
            description: formData.description || undefined,
            private: formData.isPrivate,
            github_token: formData.githubToken,
          }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Publish failed: ${response.statusText}`);
      }

      const data = await response.json();
      const repoUrl = data.github_repo_url || `https://github.com/${data.github_username}/${formData.repoName}`;

      setSuccess(true);
      setSuccessData({ repoUrl });
      onSuccess(repoUrl);

      // Close dialog after 3 seconds
      setTimeout(() => onClose(), 3000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to publish to GitHub';
      setError(errorMessage);
      onError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  if (success && successData) {
    return (
      <Dialog isOpen={true} onClose={onClose}>
        <div className="max-w-md w-full text-center">
          <div className="mb-6">
            <div className="mx-auto w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-4">
              <Check className="h-8 w-8 text-green-600 dark:text-green-400" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Published to GitHub!
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Your project has been successfully created and pushed to GitHub.
            </p>
          </div>

          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-6 text-left">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">Repository URL:</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 text-sm font-mono text-gray-900 dark:text-white break-all">
                {successData.repoUrl}
              </code>
              <button
                onClick={() => navigator.clipboard.writeText(successData.repoUrl)}
                className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                title="Copy URL"
              >
                📋
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <Button
              variant="primary"
              fullWidth
              icon={<ExternalLink className="h-4 w-4" />}
              onClick={() => window.open(successData.repoUrl, '_blank')}
            >
              View on GitHub
            </Button>
            <Button variant="secondary" fullWidth onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </Dialog>
    );
  }

  return (
    <Dialog isOpen={true} onClose={onClose}>
      <div className="max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Publish to GitHub
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Description */}
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Create a new GitHub repository and push your project code. Your repository
            will include CI/CD workflows, tests, and all documentation.
          </p>

          {/* GitHub Token */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              GitHub Personal Access Token
            </label>
            <input
              type="password"
              value={formData.githubToken}
              onChange={(e) => handleInputChange('githubToken', e.target.value)}
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
              disabled={isLoading}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 disabled:bg-gray-100 dark:disabled:bg-gray-700"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              <a
                href="https://github.com/settings/tokens"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline"
              >
                Create a token →
              </a>
            </p>
          </div>

          {/* Repository Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Repository Name
            </label>
            <input
              type="text"
              value={formData.repoName}
              onChange={(e) => handleInputChange('repoName', e.target.value)}
              placeholder="my-project"
              disabled={isLoading}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 disabled:bg-gray-100 dark:disabled:bg-gray-700"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              Must contain only letters, numbers, hyphens, and underscores
            </p>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Repository Description (Optional)
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder="A brief description of your project..."
              disabled={isLoading}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 disabled:bg-gray-100 dark:disabled:bg-gray-700"
            />
          </div>

          {/* Visibility */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Repository Visibility
            </label>
            <div className="space-y-2">
              <label className="flex items-center p-3 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <input
                  type="radio"
                  checked={formData.isPrivate}
                  onChange={() => handleInputChange('isPrivate', true)}
                  disabled={isLoading}
                  className="cursor-pointer"
                />
                <Lock className="h-4 w-4 ml-3 text-gray-500" />
                <div className="ml-2">
                  <div className="font-medium text-gray-900 dark:text-white">
                    Private
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Only you can see it
                  </div>
                </div>
              </label>

              <label className="flex items-center p-3 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <input
                  type="radio"
                  checked={!formData.isPrivate}
                  onChange={() => handleInputChange('isPrivate', false)}
                  disabled={isLoading}
                  className="cursor-pointer"
                />
                <Unlock className="h-4 w-4 ml-3 text-gray-500" />
                <div className="ml-2">
                  <div className="font-medium text-gray-900 dark:text-white">
                    Public
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Anyone can see it
                  </div>
                </div>
              </label>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <Alert type="error" title="Publish Failed">
              {error}
            </Alert>
          )}

          {/* Info Box */}
          <div className="rounded-lg bg-blue-50 dark:bg-blue-900/20 p-4 border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>What happens next:</strong> We'll create the repository on GitHub,
              initialize git, and push your code automatically.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <Button
              variant="secondary"
              fullWidth
              onClick={onClose}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              fullWidth
              onClick={handlePublish}
              disabled={isLoading || !formData.repoName.trim() || !formData.githubToken.trim()}
              icon={isLoading ? <Loader className="h-4 w-4 animate-spin" /> : <Github className="h-4 w-4" />}
            >
              {isLoading ? 'Publishing...' : 'Publish'}
            </Button>
          </div>
        </div>
      </div>
    </Dialog>
  );
};

export default GitHubPublish;
