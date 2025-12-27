/**
 * GitHubSyncWidget - GitHub sync status and controls
 */

import React from 'react';
import { GitBranch, RefreshCw, Upload, Download, AlertCircle, CheckCircle } from 'lucide-react';
import { Button } from '../common';

interface GitHubSyncWidgetProps {
  isConnected?: boolean;
  lastSync?: string;
  changesCount?: number;
  isLoading?: boolean;
  onSync?: () => void;
  onPull?: () => void;
  onPush?: () => void;
  onDisconnect?: () => void;
}

export const GitHubSyncWidget: React.FC<GitHubSyncWidgetProps> = ({
  isConnected = false,
  lastSync,
  changesCount = 0,
  isLoading = false,
  onSync,
  onPull,
  onPush,
  onDisconnect,
}) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <GitBranch className="h-5 w-5" />
          GitHub Sync Status
        </h3>
        {isConnected && (
          <span className="flex items-center gap-2 text-sm font-medium text-green-600 dark:text-green-400">
            <CheckCircle className="h-4 w-4" />
            Connected
          </span>
        )}
      </div>

      {!isConnected && (
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          No GitHub repository connected yet
        </p>
      )}

      {isConnected && (
        <div className="space-y-3 mb-4">
          {lastSync && (
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Last sync: {new Date(lastSync).toLocaleString()}
              </p>
            </div>
          )}
          {changesCount > 0 && (
            <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded text-sm text-yellow-800 dark:text-yellow-200 flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              {changesCount} pending changes
            </div>
          )}
        </div>
      )}

      {isConnected && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <Button
            variant="secondary"
            size="sm"
            icon={<RefreshCw className="h-4 w-4" />}
            onClick={onSync}
            disabled={isLoading}
            className="justify-center"
          >
            Sync
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={<Download className="h-4 w-4" />}
            onClick={onPull}
            disabled={isLoading}
            className="justify-center"
          >
            Pull
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={<Upload className="h-4 w-4" />}
            onClick={onPush}
            disabled={isLoading}
            className="justify-center"
          >
            Push
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onDisconnect}
            disabled={isLoading}
            className="justify-center"
          >
            Disconnect
          </Button>
        </div>
      )}
    </div>
  );
};
