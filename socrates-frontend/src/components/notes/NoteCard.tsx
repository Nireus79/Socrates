/**
 * NoteCard - Displays individual note
 */

import React from 'react';
import { Trash2, Tag } from 'lucide-react';
import { Button } from '../common';
import type { Note } from '../../api/notes';

interface NoteCardProps {
  note: Note;
  onDelete: (noteId: string) => void;
  isDeleting?: boolean;
}

export const NoteCard: React.FC<NoteCardProps> = ({ note, onDelete, isDeleting = false }) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md dark:hover:shadow-lg transition-shadow">
      {/* Title */}
      <h3 className="font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
        {note.title}
      </h3>

      {/* Content Preview */}
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-3">
        {note.content}
      </p>

      {/* Tags */}
      {note.tags && note.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {note.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs rounded"
            >
              <Tag className="h-3 w-3" />
              {tag}
            </span>
          ))}
          {note.tags.length > 3 && (
            <span className="inline-flex items-center px-2 py-1 text-xs text-gray-600 dark:text-gray-400">
              +{note.tags.length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Meta Info */}
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-3 border-t border-gray-100 dark:border-gray-700 pt-3">
        <span>{formatDate(note.created_at)}</span>
        <span className="text-gray-400 dark:text-gray-600">by {note.created_by}</span>
      </div>

      {/* Delete Button */}
      <Button
        variant="outline"
        size="sm"
        icon={<Trash2 className="h-4 w-4" />}
        onClick={() => onDelete(note.id)}
        disabled={isDeleting}
        className="w-full"
      >
        Delete
      </Button>
    </div>
  );
};
