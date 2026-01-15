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
  ChevronDown,
  Loader,
  Lock,
  Unlock,
  Github,
} from 'lucide-react';
import { publishToGitHub } from '@/api/projects';
import type { Project } from '@/types';

interface GitHubPublishProps {
  project: Project;
  onSuccess?: (repoUrl: string) => void;
  onError?: (error: string) => void;
}

interface PublishFormData {
  repoName: string;
  description: string;
  isPrivate: boolean;
  githubToken: string;
}

export const GitHubPublish: React.FC<GitHubPublishProps> = ({
  project,
  onSuccess,
  onError,
}) => {
  const [formData, setFormData] = useState<PublishFormData>({
    repoName: project.name.toLowerCase().replace(/\s+/g, '-'),
    description: project.description || '',
    isPrivate: true,
    githubToken: '',
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [successData, setSuccessData] = useState<{
    repoUrl: string;
    cloneUrl: string;
    githubUser: string;
  } | null>(null);
  const [showTokenHelp, setShowTokenHelp] = useState(false);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target;
    if (type === 'checkbox') {
      setFormData((prev) => ({
        ...prev,
        [name]: (e.target as HTMLInputElement).checked,
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  const validateForm = (): boolean => {
    if (!formData.repoName.trim()) {
      setError('Repository name is required');
      return false;
    }
    if (!formData.githubToken.trim()) {
      setError('GitHub Personal Access Token is required');
      return false;
    }
    if (!/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/.test(formData.repoName)) {
      setError(
        'Repository name can only contain lowercase letters, numbers, and hyphens'
      );
      return false;
    }
    return true;
  };

  const handlePublish = async () => {
    setError(null);
    setSuccess(false);

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await publishToGitHub(
        project.id,
        formData.repoName,
        formData.description,
        formData.isPrivate,
        formData.githubToken
      );

      if (response.success) {
        setSuccess(true);
        setSuccessData({
          repoUrl: response.data.repo_url,
          cloneUrl: response.data.clone_url,
          githubUser: response.data.github_user,
        });
        onSuccess?.(response.data.repo_url);

        // Clear form and success message after 5 seconds
        setTimeout(() => {
          setSuccess(false);
          setFormData({
            repoName: project.name.toLowerCase().replace(/\s+/g, '-'),
            description: project.description || '',
            isPrivate: true,
            githubToken: '',
          });
        }, 5000);
      } else {
        setError(response.message || 'Failed to publish to GitHub');
        onError?.(response.message || 'Failed to publish to GitHub');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to publish to GitHub';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  if (success && successData) {
    return (
      <div className="space-y-4">
        {/* Success Message */}
        <div className="rounded-md bg-green-50 dark:bg-green-900/20 p-6 border border-green-200 dark:border-green-800">
          <div className="flex items-start gap-4">
            <Check className="h-6 w-6 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-green-900 dark:text-green-200 mb-2">
                Project Published Successfully!
              </h3>
              <p className="text-sm text-green-800 dark:text-green-300 mb-4">
                Your project has been created on GitHub and code has been pushed.
              </p>

              {/* Repository Details */}
              <div className="space-y-3 bg-white dark:bg-gray-800 rounded p-4">
                <div>
                  <label className="text-xs font-medium text-gray-600 dark:text-gray-400">
                    GitHub User
                  </label>
                  <p className="text-sm font-mono text-gray-900 dark:text-white mt-1">
                    {successData.githubUser}
                  </p>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 dark:text-gray-400">
                    Repository URL
                  </label>
                  <a
                    href={successData.repoUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-mono text-blue-600 dark:text-blue-400 hover:underline mt-1 block break-all"
                  >
                    {successData.repoUrl}
                  </a>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 dark:text-gray-400">
                    Clone URL
                  </label>
                  <code className="text-sm text-gray-900 dark:text-white mt-1 block bg-gray-100 dark:bg-gray-700 p-2 rounded break-all">
                    {successData.cloneUrl}
                  </code>
                </div>
              </div>

              {/* Next Steps */}
              <div className="mt-4 space-y-2 text-sm text-green-800 dark:text-green-300">
                <p className="font-medium">Next steps:</p>
                <ol className="list-decimal list-inside space-y-1 ml-2">
                  <li>Clone the repository locally</li>
                  <li>Make your changes and commits</li>
                  <li>GitHub Actions will automatically run tests on push</li>
                  <li>Push to main branch for CI/CD pipeline</li>
                </ol>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <a
            href={successData.repoUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-gray-900 hover:bg-gray-800 dark:bg-gray-100 dark:hover:bg-white text-white dark:text-gray-900 font-medium rounded-lg transition-colors"
          >
            <Github className="h-4 w-4" />
            View on GitHub
          </a>
          <button
            onClick={() => setSuccess(false)}
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-medium rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Publish to GitHub
        </h3>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Create a GitHub repository and push your project code
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-800 dark:text-red-200">
            <p className="font-medium">Error</p>
            <p className="mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Repository Name */}
      <div>
        <label htmlFor="repoName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Repository Name
        </label>
        <input
          type="text"
          id="repoName"
          name="repoName"
          value={formData.repoName}
          onChange={handleInputChange}
          disabled={isLoading}
          placeholder="my-awesome-project"
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          Lowercase letters, numbers, and hyphens only
        </p>
      </div>

      {/* Description */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Repository Description
        </label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleInputChange}
          disabled={isLoading}
          placeholder="A brief description of your project"
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Visibility */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Visibility
        </label>
        <div className="space-y-2">
          <label className="flex items-center gap-3">
            <input
              type="radio"
              name="visibility"
              value="private"
              checked={formData.isPrivate}
              onChange={() => setFormData((prev) => ({ ...prev, isPrivate: true }))}
              disabled={isLoading}
              className="cursor-pointer"
            />
            <div className="flex items-center gap-2">
              <Lock className="h-4 w-4 text-gray-600 dark:text-gray-400" />
              <div>
                <div className="font-medium text-gray-900 dark:text-white">Private</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Only you and collaborators can access
                </div>
              </div>
            </div>
          </label>
          <label className="flex items-center gap-3">
            <input
              type="radio"
              name="visibility"
              value="public"
              checked={!formData.isPrivate}
              onChange={() => setFormData((prev) => ({ ...prev, isPrivate: false }))}
              disabled={isLoading}
              className="cursor-pointer"
            />
            <div className="flex items-center gap-2">
              <Unlock className="h-4 w-4 text-gray-600 dark:text-gray-400" />
              <div>
                <div className="font-medium text-gray-900 dark:text-white">Public</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Anyone can view
                </div>
              </div>
            </div>
          </label>
        </div>
      </div>

      {/* GitHub Token */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label htmlFor="githubToken" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            GitHub Personal Access Token
          </label>
          <button
            type="button"
            onClick={() => setShowTokenHelp(!showTokenHelp)}
            className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            {showTokenHelp ? 'Hide' : 'How to get token?'}
          </button>
        </div>

        <input
          type="password"
          id="githubToken"
          name="githubToken"
          value={formData.githubToken}
          onChange={handleInputChange}
          disabled={isLoading}
          placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        {showTokenHelp && (
          <div className="mt-3 rounded-md bg-blue-50 dark:bg-blue-900/20 p-4 text-sm text-blue-800 dark:text-blue-200 space-y-2">
            <p className="font-medium">To generate a GitHub token:</p>
            <ol className="list-decimal list-inside space-y-1 ml-2">
              <li>Go to GitHub Settings → Developer settings → Personal access tokens</li>
              <li>Click "Generate new token"</li>
              <li>Select scopes: <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">repo</code></li>
              <li>Copy the token (you won't see it again!)</li>
              <li>Paste it here</li>
            </ol>
            <p className="text-xs mt-2">
              🔒 Your token is sent only to create the repository and is never stored.
            </p>
          </div>
        )}
      </div>

      {/* Publish Button */}
      <button
        onClick={handlePublish}
        disabled={isLoading}
        className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 bg-gray-900 hover:bg-gray-800 disabled:bg-gray-400 dark:bg-gray-100 dark:hover:bg-white dark:disabled:bg-gray-600 text-white dark:text-gray-900 font-medium rounded-lg transition-colors"
      >
        {isLoading ? (
          <>
            <Loader className="h-4 w-4 animate-spin" />
            Creating Repository...
          </>
        ) : (
          <>
            <Github className="h-4 w-4" />
            Publish to GitHub
          </>
        )}
      </button>

      {/* Info Box */}
      <div className="rounded-md bg-gray-50 dark:bg-gray-900/50 p-4 text-sm text-gray-700 dark:text-gray-300 space-y-2">
        <p className="font-medium">This will:</p>
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>Create a new GitHub repository with your settings</li>
          <li>Initialize git in your project directory</li>
          <li>Push your code to GitHub</li>
          <li>Activate GitHub Actions workflows</li>
        </ul>
      </div>
    </div>
  );
};

export default GitHubPublish;
