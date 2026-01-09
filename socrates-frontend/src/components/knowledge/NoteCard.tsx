/**
 * Note Card - Display individual project note
 *
 * Shows:
 * - Note title and type
 * - Content preview
 * - Creation date
 * - Chunk count
 * - Delete and edit actions
 */

import React from 'react';
import { Trash2, FileText, Type } from 'lucide-react';
import { Card } from '../common';
import { Button } from '../common';
import { Badge } from '../common';

interface NoteCardProps {
  note: {
    id: string;
    title: string;
    source_type: string;
    note_type: string;
    content_preview: string;
    created_at: string;
    chunk_count: number;
  };
  onDelete?: () => void;
  onEdit?: () => void;
}

const getNoteTypeIcon = (noteType?: string) => {
  switch (noteType?.toLowerCase()) {
    case 'research':
      return <FileText className="h-4 w-4" />;
    case 'question':
      return <Type className="h-4 w-4" />;
    default:
      return <FileText className="h-4 w-4" />;
  }
};

const getNoteTypeLabel = (noteType?: string) => {
  if (!noteType) return 'Note';
  return noteType.charAt(0).toUpperCase() + noteType.slice(1);
};

const formatDate = (dateString: string) => {
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

export const NoteCard: React.FC<NoteCardProps> = ({
  note,
  onDelete,
  onEdit,
}) => {
  return (
    <Card className="p-4 hover:shadow-md transition-shadow">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              {getNoteTypeIcon(note.note_type)}
              <Badge variant="secondary" size="sm">
                {getNoteTypeLabel(note.note_type)}
              </Badge>
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-white line-clamp-2">
              {note.title}
            </h3>
          </div>
        </div>

        {/* Content Preview */}
        <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
          {note.content_preview}
        </p>

        {/* Metadata */}
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-700 pt-3">
          <span>{formatDate(note.created_at)}</span>
          <span className="font-medium">{note.chunk_count} chunks</span>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
          {onEdit && (
            <Button
              variant="secondary"
              size="sm"
              className="flex-1"
              onClick={onEdit}
            >
              Edit
            </Button>
          )}
          {onDelete && (
            <Button
              variant="secondary"
              size="sm"
              icon={<Trash2 className="h-4 w-4" />}
              onClick={onDelete}
              className="text-red-600 dark:text-red-400"
            >
              Delete
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
};

export default NoteCard;
