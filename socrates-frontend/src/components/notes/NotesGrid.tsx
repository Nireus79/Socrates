/**
 * NotesGrid - Displays grid of notes
 */

import React from 'react';
import { Loader } from 'lucide-react';
import { NoteCard } from './NoteCard';
import type { Note } from '../../api/notes';

interface NotesGridProps {
  notes: Note[];
  isLoading?: boolean;
  onDelete: (noteId: string) => void;
}

export const NotesGrid: React.FC<NotesGridProps> = ({ notes, isLoading = false, onDelete }) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="h-8 w-8 text-gray-400 dark:text-gray-600 animate-spin" />
      </div>
    );
  }

  if (!notes || notes.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400 mb-2">No notes yet</p>
        <p className="text-sm text-gray-400 dark:text-gray-500">Create a note to get started</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {notes.map((note) => (
        <NoteCard
          key={note.id}
          note={note}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
};
