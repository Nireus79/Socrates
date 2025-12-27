/**
 * Notes Store - Manages project notes state
 */

import { create } from 'zustand';
import * as notesAPI from '../api/notes';

export interface Note {
  id: string;
  title: string;
  content: string;
  tags: string[];
  created_at: string;
  created_by: string;
}

interface NotesState {
  // State
  notes: Note[];
  selectedProjectId: string | null;
  isLoading: boolean;
  error: string | null;
  searchQuery: string;
  searchResults: Note[];

  // Actions
  setSelectedProject: (projectId: string | null) => void;
  fetchNotes: (projectId: string) => Promise<void>;
  createNote: (projectId: string, title: string, content: string, tags: string[]) => Promise<void>;
  deleteNote: (projectId: string, noteId: string) => Promise<void>;
  searchNotes: (projectId: string, query: string) => Promise<void>;
  clearError: () => void;
  clearSearch: () => void;
}

export const useNotesStore = create<NotesState>((set, get) => ({
  // Initial state
  notes: [],
  selectedProjectId: null,
  isLoading: false,
  error: null,
  searchQuery: '',
  searchResults: [],

  // Set selected project
  setSelectedProject: (projectId: string | null) => {
    set({ selectedProjectId: projectId });
    if (projectId) {
      get().fetchNotes(projectId);
    }
  },

  // Fetch notes
  fetchNotes: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await notesAPI.getNotes(projectId);
      set({
        notes: response.notes || [],
        selectedProjectId: projectId,
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch notes';
      set({ error: message, isLoading: false });
    }
  },

  // Create note
  createNote: async (projectId: string, title: string, content: string, tags: string[] = []) => {
    set({ isLoading: true, error: null });
    try {
      const newNote = await notesAPI.createNote(projectId, title, content, tags);
      if (newNote) {
        set((state) => ({
          notes: [...state.notes, newNote],
          isLoading: false,
        }));
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create note';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  // Delete note
  deleteNote: async (projectId: string, noteId: string) => {
    set({ isLoading: true, error: null });
    try {
      const success = await notesAPI.deleteNote(projectId, noteId);
      if (success) {
        set((state) => ({
          notes: state.notes.filter((n) => n.id !== noteId),
          isLoading: false,
        }));
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete note';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  // Search notes
  searchNotes: async (projectId: string, query: string) => {
    set({ isLoading: true, error: null, searchQuery: query });
    try {
      if (!query.trim()) {
        set({ searchResults: [], isLoading: false, searchQuery: '' });
        return;
      }

      const response = await notesAPI.searchNotes(projectId, query);
      set({
        searchResults: response.results || [],
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to search notes';
      set({ error: message, isLoading: false });
    }
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },

  // Clear search
  clearSearch: () => {
    set({ searchQuery: '', searchResults: [] });
  },
}));
