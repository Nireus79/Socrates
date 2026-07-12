/**
 * GitHub Integration Settings Component
 *
 * Allows users to link their GitHub account for:
 * - Real-time sponsorship verification
 * - Private repository access
 * - GitHub integration features
 */

import React, { useState, useEffect } from 'react';
import {
  Github,
  Key,
  Check,
  AlertCircle,
  Loader,
  Eye,
  EyeOff,
  Trash2,
  Plus,
  RefreshCw,
} from 'lucide-react';
import { Card, Button, Input, Alert, Badge } from '../common';
import { apiClient } from '../../api/client';
import { showSuccess, showError } from '../../stores';

interface GitHubStatus {
  linked: boolean;
  github_username?: string;
  token_valid?: boolean;
  scopes?: string[];
  verification_status?: string;
  last_verified_at?: string;
  sponsorship?: {
    active: boolean;
    tier?: string;
    amount_usd?: number;
    expires_at?: string;
  };
}

export const GitHubIntegrationSection: React.FC = () => {
  const [githubToken, setGithubToken] = useState('');
  const [showToken, setShowToken] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [status, setStatus] = useState<GitHubStatus | null>(null);
  const [error, setError] = useState('');

  // Load GitHub status on mount
  useEffect(() => {
    loadGitHubStatus();
  }, []);

  const loadGitHubStatus = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await apiClient.get<any>('/github/auth/status');
      if (response.success) {
        setStatus(response.data as GitHubStatus);
      } else {
        setStatus({ linked: false });
      }
    } catch (err: any) {
      setStatus({ linked: false });
      logger?.debug(`GitHub status check: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLinkAccount = async () => {
    if (!githubToken.trim()) {
      setError('Please enter a GitHub Personal Access Token');
      return;
    }

    setIsSaving(true);
    setError('');

    try {
      const response = await apiClient.post<any>('/github/link-account', {
        token: githubToken,
      });

      // Note: Response interceptor unwraps APIResponse and returns just the data
      // So we check for the presence of data, not response.success
      if (response && response.github_username) {
        showSuccess('Success', `GitHub account linked: ${response.github_username}`);
        setGithubToken('');
        await loadGitHubStatus();
      } else {
        setError('Failed to link GitHub account - unexpected response format');
      }
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to link GitHub account');
    } finally {
      setIsSaving(false);
    }
  };

  const handleUnlinkAccount = async () => {
    if (!confirm('Are you sure? This will revoke your GitHub token.')) {
      return;
    }

    setIsSaving(true);
    setError('');

    try {
      const response = await apiClient.delete<any>('/github/unlink');

      if (response) {
        showSuccess('Success', 'GitHub account unlinked');
        await loadGitHubStatus();
      } else {
        setError('Failed to unlink GitHub account');
      }
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to unlink GitHub account');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRefreshVerification = async () => {
    setIsSaving(true);
    setError('');

    try {
      const response = await apiClient.post<any>('/github/refresh-verification', {});

      if (response) {
        showSuccess('Success', 'Sponsorship verified with GitHub');
        await loadGitHubStatus();
      } else {
        setError('Failed to verify sponsorship');
      }
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to verify sponsorship');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card>
      <div className="flex items-center gap-2 mb-4">
        <Github className="w-5 h-5" />
        <h3 className="text-lg font-semibold">GitHub Integration</h3>
      </div>

      <Alert type="info" title="Why Link GitHub?">
        <ul className="list-disc list-inside mt-2 text-sm space-y-1">
          <li>Verify your GitHub Sponsors donation in real-time</li>
          <li>Import code from your private repositories</li>
          <li>Link private repo code to your knowledge base</li>
          <li>Sync Socrates projects back to your repos</li>
        </ul>
      </Alert>

      {error && (
        <Alert type="error" title="Error" className="mt-4">
          {error}
        </Alert>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader className="w-5 h-5 animate-spin" />
        </div>
      ) : status?.linked ? (
        // Linked state
        <div className="space-y-4 mt-4">
          <div className="p-4 bg-green-50 dark:bg-green-900 rounded-lg border border-green-200 dark:border-green-800">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Check className="w-5 h-5 text-green-600 dark:text-green-400" />
                <span className="font-medium text-green-900 dark:text-green-100">
                  Linked as: {status.github_username}
                </span>
              </div>
              <Badge variant="success">Active</Badge>
            </div>

            {status.scopes && (
              <p className="text-sm text-green-800 dark:text-green-200 mb-2">
                Scopes: {status.scopes.join(', ')}
              </p>
            )}

            {status.last_verified_at && (
              <p className="text-xs text-green-700 dark:text-green-300">
                Last verified: {new Date(status.last_verified_at).toLocaleString()}
              </p>
            )}

            {status.sponsorship && (
              <div className="mt-3 p-3 bg-white dark:bg-gray-800 rounded border border-green-200 dark:border-green-700">
                <p className="font-medium text-gray-900 dark:text-white">
                  Sponsorship Status:
                </p>
                {status.sponsorship.active ? (
                  <div className="mt-2 text-sm space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="success">{status.sponsorship.tier}</Badge>
                      <span>Active</span>
                    </div>
                    <p className="text-gray-600 dark:text-gray-400">
                      Amount: ${status.sponsorship.amount_usd}/month
                    </p>
                    <p className="text-gray-600 dark:text-gray-400">
                      Expires: {new Date(status.sponsorship.expires_at || '').toLocaleDateString()}
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                    No active sponsorship found
                  </p>
                )}
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={handleRefreshVerification}
              isLoading={isSaving}
            >
              <RefreshCw className="w-4 h-4" />
              Refresh Verification
            </Button>
            <Button
              variant="danger"
              onClick={handleUnlinkAccount}
              isLoading={isSaving}
            >
              <Trash2 className="w-4 h-4" />
              Unlink Account
            </Button>
          </div>
        </div>
      ) : (
        // Unlinked state
        <div className="space-y-4 mt-4">
          <Alert type="warning" title="Not Linked">
            Your GitHub account is not linked. Link it to enable GitHub features.
          </Alert>

          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-white">
                GitHub Personal Access Token
              </label>
              <div className="flex gap-2">
                <Input
                  type={showToken ? 'text' : 'password'}
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                  disabled={isSaving}
                  className="flex-1"
                />
                <Button
                  variant="ghost"
                  onClick={() => setShowToken(!showToken)}
                  disabled={isSaving}
                >
                  {showToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </Button>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                <a
                  href="https://github.com/settings/tokens"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Generate a token
                </a>
                {' '}with scopes: <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">user, repo</code>
              </p>
            </div>

            <Button
              onClick={handleLinkAccount}
              isLoading={isSaving}
              disabled={!githubToken.trim()}
              className="w-full"
            >
              <Plus className="w-4 h-4" />
              Link GitHub Account
            </Button>
          </div>

          <Alert type="info" title="How to Generate Token">
            <ol className="list-decimal list-inside space-y-1 text-sm mt-2">
              <li>
                Go to{' '}
                <a
                  href="https://github.com/settings/tokens"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 dark:text-blue-400 underline"
                >
                  github.com/settings/tokens
                </a>
              </li>
              <li>Click "Generate new token (classic)"</li>
              <li>Name: "Socrates"</li>
              <li>
                Select scopes:{' '}
                <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-xs">
                  user
                </code>
                {' '}and{' '}
                <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-xs">
                  repo
                </code>
              </li>
              <li>Generate token and paste it above</li>
            </ol>
          </Alert>
        </div>
      )}
    </Card>
  );
};

// Simple logger for debugging (in case showError/showSuccess don't exist)
const logger = {
  debug: (msg: string) => console.debug(msg),
};
