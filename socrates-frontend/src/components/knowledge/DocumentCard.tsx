/**
 * Document Card - Display individual document metadata
 *
 * Shows:
 * - Document title and source
 * - Creation date
 * - Chunk count and file size
 * - Delete action
 */

import React from 'react';
import { Trash2, FileText, Link, Upload, Type } from 'lucide-react';
import type { DocumentMetadata } from '../../api/knowledge';
import { Card } from '../common';
import { Button } from '../common';
import { Badge } from '../common';

interface DocumentCardProps {
  document: DocumentMetadata;
  onDelete?: () => void;
  onView?: () => void;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({
  document,
  onDelete,
  onView,
}) => {
  const getSourceIcon = () => {
    switch (document.source_type) {
      case 'file':
        return <Upload className="h-4 w-4" />;
      case 'url':
        return <Link className="h-4 w-4" />;
      case 'text':
        return <Type className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getSourceLabel = () => {
    switch (document.source_type) {
      case 'file':
        return 'File Upload';
      case 'url':
        return 'Web URL';
      case 'text':
        return 'Pasted Text';
      default:
        return 'Document';
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  const formatSize = (bytes?: number) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <Card
      className="hover:shadow-md transition-shadow cursor-pointer"
      onClick={onView}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {document.title}
            </h3>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="secondary">
              <span className="flex items-center gap-1">
                {getSourceIcon()} {getSourceLabel()}
              </span>
            </Badge>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formatDate(document.created_at)}
            </span>
          </div>

          <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
            <span>{document.chunk_count} chunks</span>
            {document.size && <span>{formatSize(document.size)}</span>}
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          icon={<Trash2 className="h-4 w-4" />}
          onClick={(e) => {
            e.stopPropagation();
            onDelete?.();
          }}
          className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
        >
          Delete
        </Button>
      </div>
    </Card>
  );
};
