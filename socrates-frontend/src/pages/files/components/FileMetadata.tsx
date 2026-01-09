/**
 * FileMetadata Component - Display file information
 */

import React from 'react';
import { Download, Copy, CheckCircle } from 'lucide-react';
import { Card } from '../../../components/common';
import type { FileNode } from '../../../stores/projectStore';

interface FileMetadataProps {
  file: FileNode | null;
  content: string;
}

const formatDate = (dateString?: string): string => {
  if (!dateString) return 'Unknown';
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return 'Invalid date';
  }
};

const formatFileSize = (bytes?: number): string => {
  if (!bytes) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export const FileMetadata: React.FC<FileMetadataProps> = ({ file, content }) => {
  const [copiedToClipboard, setCopiedToClipboard] = React.useState(false);

  const handleDownload = () => {
    if (!file || !content) return;

    const element = document.createElement('a');
    element.setAttribute('href', `data:text/plain;charset=utf-8,${encodeURIComponent(content)}`);
    element.setAttribute('download', file.name);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleCopyToClipboard = async () => {
    if (!content) return;

    try {
      await navigator.clipboard.writeText(content);
      setCopiedToClipboard(true);
      setTimeout(() => setCopiedToClipboard(false), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  if (!file) {
    return (
      <Card className="p-4 bg-gray-50 dark:bg-gray-800">
        <p className="text-sm text-gray-500 dark:text-gray-400">Select a file to view details</p>
      </Card>
    );
  }

  return (
    <Card className="p-4 space-y-4 bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800">
      {/* File Information */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">File Information</h3>

        <div className="space-y-2">
          <div>
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">File Name</p>
            <p className="text-sm text-gray-900 dark:text-white break-all">{file.name}</p>
          </div>

          <div>
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Path</p>
            <p className="text-sm text-gray-700 dark:text-gray-300 break-all font-mono text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded">
              {file.path}
            </p>
          </div>

          {file.language && (
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Language</p>
              <p className="text-sm text-gray-900 dark:text-white capitalize">{file.language}</p>
            </div>
          )}

          {file.size !== undefined && (
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400">File Size</p>
              <p className="text-sm text-gray-900 dark:text-white">
                {formatFileSize(file.size)} ({file.size?.toLocaleString()} bytes)
              </p>
            </div>
          )}

          {file.createdAt && (
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Created</p>
              <p className="text-sm text-gray-900 dark:text-white">{formatDate(file.createdAt)}</p>
            </div>
          )}

          {file.updatedAt && (
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Last Modified</p>
              <p className="text-sm text-gray-900 dark:text-white">{formatDate(file.updatedAt)}</p>
            </div>
          )}

          {content && (
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Lines of Code</p>
              <p className="text-sm text-gray-900 dark:text-white">{content.split('\n').length}</p>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="border-t border-gray-200 dark:border-gray-800 pt-4 space-y-2">
        <button
          onClick={handleDownload}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors text-sm font-medium"
        >
          <Download className="w-4 h-4" />
          Download
        </button>

        <button
          onClick={handleCopyToClipboard}
          className={`w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg transition-colors text-sm font-medium ${
            copiedToClipboard
              ? 'bg-green-500 hover:bg-green-600 text-white'
              : 'bg-gray-200 hover:bg-gray-300 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-900 dark:text-white'
          }`}
        >
          {copiedToClipboard ? (
            <>
              <CheckCircle className="w-4 h-4" />
              Copied!
            </>
          ) : (
            <>
              <Copy className="w-4 h-4" />
              Copy Code
            </>
          )}
        </button>
      </div>
    </Card>
  );
};

export default FileMetadata;
