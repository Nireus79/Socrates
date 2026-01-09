/**
 * FileList Component - Display project files in categorized list
 */

import React from 'react';
import { FileCode, File } from 'lucide-react';
import type { FileNode } from '../../../stores/projectStore';

interface FileListProps {
  files: FileNode[];
  selectedFile: FileNode | null;
  onFileSelect: (file: FileNode) => void;
  isLoading: boolean;
}

const getFileIcon = (language?: string) => {
  const iconClass = 'w-4 h-4';
  switch (language) {
    case 'python':
      return <span className="text-blue-500">🐍</span>;
    case 'javascript':
      return <span className="text-yellow-500">✓</span>;
    case 'typescript':
      return <span className="text-blue-600">TS</span>;
    case 'java':
      return <span className="text-red-500">☕</span>;
    case 'csharp':
      return <span className="text-purple-500">C#</span>;
    case 'cpp':
      return <span className="text-blue-500">C++</span>;
    case 'go':
      return <span className="text-cyan-500">Go</span>;
    case 'rust':
      return <span className="text-orange-600">⚙️</span>;
    case 'sql':
      return <span className="text-green-600">SQL</span>;
    default:
      return <FileCode className={iconClass} />;
  }
};

const formatFileSize = (bytes?: number): string => {
  if (!bytes) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export const FileList: React.FC<FileListProps> = ({
  files,
  selectedFile,
  onFileSelect,
  isLoading,
}) => {
  // Group files by category (generated vs refactored)
  const generatedFiles = files.filter((f) => f.path?.includes('generated_files'));
  const refactoredFiles = files.filter((f) => f.path?.includes('refactored_files'));

  const renderFileItem = (file: FileNode) => (
    <button
      key={file.id || file.path}
      onClick={() => onFileSelect(file)}
      className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center gap-2 ${
        selectedFile?.id === file.id || selectedFile?.path === file.path
          ? 'bg-blue-500 text-white'
          : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
      }`}
    >
      <span className="flex-shrink-0">{getFileIcon(file.language)}</span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium truncate">{file.name}</p>
        <p className="text-xs opacity-75 truncate">{formatFileSize(file.size)}</p>
      </div>
    </button>
  );

  if (isLoading) {
    return (
      <div className="p-4">
        <div className="animate-pulse space-y-2">
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded" />
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded" />
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
      {/* File list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Generated Files Section */}
        {generatedFiles.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide px-2 mb-2">
              Generated Files
            </h3>
            <div className="space-y-1">{generatedFiles.map(renderFileItem)}</div>
          </div>
        )}

        {/* Refactored Files Section */}
        {refactoredFiles.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide px-2 mb-2">
              Refactored Files
            </h3>
            <div className="space-y-1">{refactoredFiles.map(renderFileItem)}</div>
          </div>
        )}

        {/* Empty state */}
        {files.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <File className="w-8 h-8 text-gray-300 dark:text-gray-600 mb-2" />
            <p className="text-sm text-gray-500 dark:text-gray-400">No files found</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileList;
