/**
 * Document Card - Display individual document metadata
 *
 * Shows:
 * - Selection checkbox for bulk operations
 * - Document title and source
 * - Creation date
 * - Chunk count and file size
 * - Analytics badge (views/searches)
 * - Delete and view actions
 */

import React, { useMemo, useCallback } from 'react';
import { Trash2, FileText, Link, Upload, Type, Eye } from 'lucide-react';
import type { DocumentMetadata } from '../../api/knowledge';
import { Card } from '../common';
import { Button } from '../common';
import { Badge } from '../common';

interface DocumentCardProps {
  document: DocumentMetadata;
  isSelected?: boolean;
  onSelect?: (selected: boolean) => void;
  onDelete?: () => void;
  onView?: () => void;
  analytics?: {
    views?: number;
    searches?: number;
  };
}

const getSourceIcon = (sourceType?: string) => {
  switch (sourceType) {
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

const getSourceLabel = (sourceType?: string) => {
  switch (sourceType) {
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

const DocumentCardComponent: React.FC<DocumentCardProps> = ({
  document,
  isSelected = false,
  onSelect,
  onDelete,
  onView,
  analytics,
}) => {
  // Memoize event handlers to prevent unnecessary re-renders of children
  const handleSelectChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      e.stopPropagation();
      onSelect?.(e.target.checked);
    },
    [onSelect]
  );

  const handleDeleteClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onDelete?.();
    },
    [onDelete]
  );

  // Memoize formatted values to avoid recomputation
  const formattedDate = useMemo(() => formatDate(document.created_at), [document.created_at]);
  const formattedSize = useMemo(() => formatSize(document.size), [document.size]);
  const sourceIcon = useMemo(() => getSourceIcon(document.source_type), [document.source_type]);
  const sourceLabel = useMemo(() => getSourceLabel(document.source_type), [document.source_type]);

  return (
    <Card
      className={`hover:shadow-md transition-all cursor-pointer ${
        isSelected ? 'ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-900' : ''
      }`}
      onClick={onView}
    >
      <div className="flex items-start gap-3">
        {/* Checkbox */}
        {onSelect && (
          <input
            type="checkbox"
            checked={isSelected}
            onChange={handleSelectChange}
            className="mt-1 h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer"
          />
        )}

        {/* Content */}
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
            <h3 className="font-semibold text-gray-900 dark:text-white truncate">
              {document.title}
            </h3>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="secondary">
              <span className="flex items-center gap-1 text-xs">
                {sourceIcon} {sourceLabel}
              </span>
            </Badge>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formattedDate}
            </span>
            {analytics && (analytics.views || 0) > 0 && (
              <Badge variant="outline" className="text-xs">
                <span className="flex items-center gap-1">
                  <Eye className="h-3 w-3" />
                  {analytics.views} views
                </span>
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
            <span>{document.chunk_count} chunks</span>
            {document.size && <span>{formattedSize}</span>}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            icon={<Trash2 className="h-4 w-4" />}
            onClick={handleDeleteClick}
            className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
          />
        </div>
      </div>
    </Card>
  );
};

// Export with React.memo to prevent unnecessary re-renders
export const DocumentCard = React.memo(DocumentCardComponent);
