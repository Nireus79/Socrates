/**
 * Search Store - Manages search state and results
 */

import { create } from 'zustand';
import * as searchAPI from '../api/search';

export interface SearchResult {
  id: string;
  type: 'project' | 'conversation' | 'knowledge' | 'note';
  title: string;
  description?: string;
  content?: string;
  projectId?: string;
  createdAt?: string;
  score?: number;
}

type SearchType = 'all' | 'conversations' | 'knowledge' | 'notes';

interface SearchState {
  // State
  query: string;
  searchType: SearchType;
  results: SearchResult[];
  isLoading: boolean;
  error: string | null;
  totalResults: number;

  // Actions
  setQuery: (query: string) => void;
  setSearchType: (type: SearchType) => void;
  search: (query: string, type?: SearchType) => Promise<void>;
  globalSearch: (query: string) => Promise<void>;
  searchConversations: (query: string, projectId?: string) => Promise<void>;
  searchKnowledge: (query: string, projectId?: string) => Promise<void>;
  searchNotes: (query: string, projectId?: string) => Promise<void>;
  clear: () => void;
  clearError: () => void;
}

export const useSearchStore = create<SearchState>((set, get) => ({
  // Initial state
  query: '',
  searchType: 'all',
  results: [],
  isLoading: false,
  error: null,
  totalResults: 0,

  // Set query
  setQuery: (query: string) => {
    set({ query });
  },

  // Set search type
  setSearchType: (type: SearchType) => {
    set({ searchType: type });
  },

  // Generic search
  search: async (query: string, type?: SearchType) => {
    set({ isLoading: true, error: null, query });
    try {
      const searchTypeToUse = type || get().searchType;

      let response;
      if (searchTypeToUse === 'all') {
        response = await searchAPI.globalSearch(query);
      } else if (searchTypeToUse === 'conversations') {
        response = await searchAPI.searchConversations(query);
      } else if (searchTypeToUse === 'knowledge') {
        response = await searchAPI.searchKnowledge(query);
      } else if (searchTypeToUse === 'notes') {
        response = await searchAPI.searchNotes(query);
      } else {
        response = await searchAPI.globalSearch(query);
      }

      set({
        results: response.results || [],
        totalResults: response.total || 0,
        isLoading: false,
        searchType: searchTypeToUse,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Search failed';
      set({ error: message, isLoading: false });
    }
  },

  // Global search
  globalSearch: async (query: string) => {
    set({ isLoading: true, error: null, query });
    try {
      const response = await searchAPI.globalSearch(query);
      set({
        results: response.results || [],
        totalResults: response.total || 0,
        isLoading: false,
        searchType: 'all',
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Global search failed';
      set({ error: message, isLoading: false });
    }
  },

  // Search conversations
  searchConversations: async (query: string, projectId?: string) => {
    set({ isLoading: true, error: null, query });
    try {
      const response = await searchAPI.searchConversations(query, projectId);
      set({
        results: response.results || [],
        totalResults: response.total || 0,
        isLoading: false,
        searchType: 'conversations',
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Conversation search failed';
      set({ error: message, isLoading: false });
    }
  },

  // Search knowledge
  searchKnowledge: async (query: string, projectId?: string) => {
    set({ isLoading: true, error: null, query });
    try {
      const response = await searchAPI.searchKnowledge(query, projectId);
      set({
        results: response.results || [],
        totalResults: response.total || 0,
        isLoading: false,
        searchType: 'knowledge',
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Knowledge search failed';
      set({ error: message, isLoading: false });
    }
  },

  // Search notes
  searchNotes: async (query: string, projectId?: string) => {
    set({ isLoading: true, error: null, query });
    try {
      const response = await searchAPI.searchNotes(query, projectId);
      set({
        results: response.results || [],
        totalResults: response.total || 0,
        isLoading: false,
        searchType: 'notes',
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Notes search failed';
      set({ error: message, isLoading: false });
    }
  },

  // Clear results
  clear: () => {
    set({
      query: '',
      results: [],
      totalResults: 0,
      error: null,
    });
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },
}));
