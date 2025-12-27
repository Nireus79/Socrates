/**
 * Knowledge Base Store - Zustand state management
 *
 * Manages:
 * - Document list and metadata
 * - Search queries and results
 * - Import operations
 * - Knowledge entries
 */

import { create } from 'zustand';
import { knowledgeAPI } from '../api/knowledge';
import type {
  DocumentMetadata,
  SearchResult,
  ImportResponse,
  DocumentListResponse,
  KnowledgeSearchResponse,
} from '../api/knowledge';

interface KnowledgeState {
  // State
  documents: Map<string, DocumentMetadata>;
  searchResults: SearchResult[];
  currentQuery: string;
  isLoading: boolean;
  isImporting: boolean;
  isSearching: boolean;
  error: string | null;
  lastSearchedProject: string | null;

  // Actions
  listDocuments: (projectId?: string) => Promise<void>;
  importFile: (file: File, projectId?: string) => Promise<ImportResponse>;
  importURL: (url: string, projectId?: string) => Promise<ImportResponse>;
  importText: (
    title: string,
    content: string,
    projectId?: string
  ) => Promise<ImportResponse>;
  searchKnowledge: (
    query: string,
    projectId?: string,
    topK?: number
  ) => Promise<void>;
  deleteDocument: (documentId: string) => Promise<void>;
  addKnowledgeEntry: (
    content: string,
    category: string,
    projectId?: string
  ) => Promise<void>;
  exportKnowledge: (projectId: string) => Promise<void>;
  clearError: () => void;
  clearSearch: () => void;
}

export const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  // Initial state
  documents: new Map(),
  searchResults: [],
  currentQuery: '',
  isLoading: false,
  isImporting: false,
  isSearching: false,
  error: null,
  lastSearchedProject: null,

  /**
   * List all documents in knowledge base
   */
  listDocuments: async (projectId?: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await knowledgeAPI.listDocuments(projectId);
      const documentsMap = new Map<string, DocumentMetadata>();

      // Handle different response formats
      const documents = response?.documents || response || [];
      const docArray = Array.isArray(documents) ? documents : [];

      docArray.forEach((doc: any) => {
        if (doc.id) {
          documentsMap.set(doc.id, doc);
        }
      });

      set({ documents: documentsMap, isLoading: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to list documents';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  /**
   * Import file to knowledge base
   */
  importFile: async (file: File, projectId?: string) => {
    set({ isImporting: true, error: null });
    try {
      const result = await knowledgeAPI.importFile(file, projectId);
      set({ isImporting: false });

      // Refresh document list
      await get().listDocuments(projectId);

      return result;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to import file';
      set({ error: message, isImporting: false });
      throw err;
    }
  },

  /**
   * Import content from URL
   */
  importURL: async (url: string, projectId?: string) => {
    set({ isImporting: true, error: null });
    try {
      const result = await knowledgeAPI.importURL(url, projectId);
      set({ isImporting: false });

      // Refresh document list
      await get().listDocuments(projectId);

      return result;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to import URL';
      set({ error: message, isImporting: false });
      throw err;
    }
  },

  /**
   * Import pasted text
   */
  importText: async (
    title: string,
    content: string,
    projectId?: string
  ) => {
    set({ isImporting: true, error: null });
    try {
      const result = await knowledgeAPI.importText(title, content, projectId);
      set({ isImporting: false });

      // Refresh document list
      await get().listDocuments(projectId);

      return result;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to import text';
      set({ error: message, isImporting: false });
      throw err;
    }
  },

  /**
   * Search knowledge base
   */
  searchKnowledge: async (
    query: string,
    projectId?: string,
    topK: number = 10
  ) => {
    set({ isSearching: true, currentQuery: query, error: null });
    try {
      const response = await knowledgeAPI.searchKnowledge(query, projectId, topK);
      set({
        searchResults: response.results,
        isSearching: false,
        lastSearchedProject: projectId || null,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to search knowledge base';
      set({ error: message, isSearching: false });
      throw err;
    }
  },

  /**
   * Delete document from knowledge base
   */
  deleteDocument: async (documentId: string) => {
    set({ isLoading: true, error: null });
    try {
      await knowledgeAPI.deleteDocument(documentId);

      // Update documents map
      const { documents } = get();
      const newDocuments = new Map(documents);
      newDocuments.delete(documentId);
      set({ documents: newDocuments, isLoading: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to delete document';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  /**
   * Add knowledge entry
   */
  addKnowledgeEntry: async (
    content: string,
    category: string,
    projectId?: string
  ) => {
    set({ isLoading: true, error: null });
    try {
      await knowledgeAPI.addKnowledgeEntry(content, category, projectId);
      set({ isLoading: false });

      // Refresh document list
      await get().listDocuments(projectId);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to add knowledge entry';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  /**
   * Export knowledge base for project
   */
  exportKnowledge: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      await knowledgeAPI.exportKnowledge(projectId);
      set({ isLoading: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to export knowledge base';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  /**
   * Clear error message
   */
  clearError: () => {
    set({ error: null });
  },

  /**
   * Clear search results
   */
  clearSearch: () => {
    set({ searchResults: [], currentQuery: '' });
  },
}));
