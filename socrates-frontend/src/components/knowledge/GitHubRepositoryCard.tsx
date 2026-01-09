/**
 * GitHub Repository Card - Display imported GitHub repository
 *
 * Shows:
 * - Repository owner/name with link
 * - Repository description
 * - Chunk counts (README + code files)
 * - Technology stack preview
 * - Sync status
 */

import React from 'react';
import { Github, ExternalLink } from 'lucide-react';
import { Card } from '../common';
import { Button } from '../common';
import { Badge } from '../common';

interface GitHubRepositoryCardProps {
  repo: {
    id: string;
    title: string;
    source_type: string;
    url: string;
    owner: string;
    name: string;
    chunk_count: number;
    readme_chunks: number;
    code_chunks: number;
  };
  onSync?: () => void;
  onDelete?: () => void;
}

const formatDate = (dateString?: string) => {
  if (!dateString) return 'Unknown';
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(date);
  } catch {
    return dateString;
  }
};

export const GitHubRepositoryCard: React.FC<GitHubRepositoryCardProps> = ({
  repo,
  onSync,
  onDelete,
}) => {
  return (
    <Card className="p-4 hover:shadow-md transition-shadow">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Github className="h-5 w-5 text-gray-700 dark:text-gray-300" />
              <Badge variant="secondary" size="sm">
                GitHub Repository
              </Badge>
            </div>
            <a
              href={repo.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
            >
              {repo.title}
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </div>

        {/* Chunk Counts */}
        <div className="grid grid-cols-2 gap-2 text-sm bg-gray-50 dark:bg-gray-800 rounded p-3">
          <div>
            <div className="text-xs text-gray-600 dark:text-gray-400">README</div>
            <div className="font-semibold text-gray-900 dark:text-white">
              {repo.readme_chunks} chunks
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Code Files</div>
            <div className="font-semibold text-gray-900 dark:text-white">
              {repo.code_chunks} chunks
            </div>
          </div>
        </div>

        {/* Total Chunks */}
        <div className="flex items-center justify-between text-sm border-t border-gray-200 dark:border-gray-700 pt-3">
          <span className="text-gray-600 dark:text-gray-400">Total Chunks</span>
          <span className="font-semibold text-gray-900 dark:text-white">
            {repo.chunk_count}
          </span>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
          {onSync && (
            <Button
              variant="secondary"
              size="sm"
              className="flex-1"
              onClick={onSync}
            >
              Sync
            </Button>
          )}
          {onDelete && (
            <Button
              variant="secondary"
              size="sm"
              className="flex-1 text-red-600 dark:text-red-400"
              onClick={onDelete}
            >
              Remove
            </Button>
          )}
          <Button
            variant="primary"
            size="sm"
            className="flex-1"
            onClick={() => window.open(repo.url, '_blank')}
          >
            View
          </Button>
        </div>
      </div>
    </Card>
  );
};

export default GitHubRepositoryCard;
