/**
 * GitHub Sync Status Widget - Display project's GitHub sync status
 */

import React from 'react';
import { GitBranch, RefreshCw, Upload, Download, Check, AlertCircle } from 'lucide-react';
import { useGitHubStore } from '../../stores';
import { Button } from '../common';
import { Card } from '../common';

interface SyncStatusWidgetProps {
  projectId: string;
  repositoryUrl?: string;
  onSync?: (projectId: string) => void;
}

export const SyncStatusWidget: React.FC<SyncStatusWidgetProps> = ({
  projectId,
  repositoryUrl,
  onSync,
}) => {
  const { getSyncStatus, syncProject, pullChanges, pushChanges, isLoading, syncStatuses } =
    useGitHubStore();
  const [isRefreshing, setIsRefreshing] = React.useState(false);

  const syncStatus = syncStatuses.get(projectId);
  const isLinked = syncStatus?.is_linked ?? false;

  React.useEffect(() => {
    if (projectId && isLinked) {
      getSyncStatus(projectId).catch(console.error);
    }
  }, [projectId, isLinked, getSyncStatus]);

  const handleSync = async () => {
    try {
      await syncProject(projectId);
      onSync?.(projectId);
    } catch (error) {
      console.error('Sync failed:', error);
    }
  };

  const handlePull = async () => {
    try {
      await pullChanges(projectId);
    } catch (error) {
      console.error('Pull failed:', error);
    }
  };

  const handlePush = async () => {
    try {
      await pushChanges(projectId);
    } catch (error) {
      console.error('Push failed:', error);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await getSyncStatus(projectId);
    } finally {
      setIsRefreshing(false);
    }
  };

  if (!isLinked) {
    return null;
  }

  return (
    <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200 dark:border-blue-800">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <h3 className="font-medium text-gray-900 dark:text-white">GitHub Sync</h3>
            {!isLoading && !isRefreshing && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <span className="text-xs text-green-700 dark:text-green-400">Connected</span>
              </div>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            icon={<RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />}
            onClick={handleRefresh}
            disabled={isLoading || isRefreshing}
          >
            {isRefreshing ? '' : 'Refresh'}
          </Button>
        </div>

        {/* Repository URL */}
        {repositoryUrl && (
          <div className="text-sm text-gray-600 dark:text-gray-400 truncate">
            {repositoryUrl}
          </div>
        )}

        {/* Status Info */}
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <Check className="h-4 w-4 text-green-600 dark:text-green-400" />
          <span>Up to date</span>
          {syncStatus?.repository_imported_at && (
            <span className="text-xs">
              (Synced{' '}
              {new Date(syncStatus.repository_imported_at).toLocaleDateString()})
            </span>
          )}
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-3 gap-2 pt-2">
          <Button
            variant="secondary"
            size="sm"
            fullWidth
            icon={<Download className="h-4 w-4" />}
            onClick={handlePull}
            disabled={isLoading}
          >
            Pull
          </Button>
          <Button
            variant="secondary"
            size="sm"
            fullWidth
            icon={<Upload className="h-4 w-4" />}
            onClick={handlePush}
            disabled={isLoading}
          >
            Push
          </Button>
          <Button
            variant="primary"
            size="sm"
            fullWidth
            icon={<RefreshCw className="h-4 w-4" />}
            onClick={handleSync}
            disabled={isLoading}
            isLoading={isLoading}
          >
            Sync
          </Button>
        </div>

        {/* Help Text */}
        <div className="text-xs text-gray-600 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-700">
          Manage code changes with GitHub directly from Socrates
        </div>
      </div>
    </Card>
  );
};
