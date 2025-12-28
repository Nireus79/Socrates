/**
 * Knowledge Base Store - Zustand state management
 *
 * Manages:
 * - Document list and metadata with filtering/sorting/pagination
 * - Search queries and results
 * - Import operations and bulk imports
 * - Knowledge entries
 * - Document selection and bulk operations
 * - Document details and analytics caching
 */

import { create } from 'zustand';
import { knowledgeAPI } from '../api/knowledge';
import type {
  DocumentMetadata,
  SearchResult,
  ImportResponse,
  DocumentListResponse,
  KnowledgeSearchResponse,
  DocumentListFilters,
  DocumentDetails,
  DocumentAnalytics,
} from '../api/knowledge';
import type { DocumentDetailsResponse, DocumentAnalyticsResponse } from '../types/models';

// Type for pagination state
interface PaginationState {
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

// Type for bulk operation progress
interface BulkOperationProgress {
  type: 'import' | 'delete' | null;
  current: number;
  total: number;
  completed: string[];
  failed: Array<{ id: string; reason: string }>;
}

interface KnowledgeState {
  // State - Existing
  documents: Map<string, DocumentMetadata>;
  searchResults: SearchResult[];
  currentQuery: string;
  isLoading: boolean;
  isImporting: boolean;
  isSearching: boolean;
  error: string | null;
  lastSearchedProject: string | null;

  // State - Filtering & Pagination (New)
  filters: DocumentListFilters;
  pagination: PaginationState;
  selectedDocuments: Set<string>;
  bulkOperationProgress: BulkOperationProgress;
  documentDetailsCache: Map<string, DocumentDetails>;
  documentAnalyticsCache: Map<string, DocumentAnalytics>;
  isBulkOperationLoading: boolean;

  // Actions - Existing
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

  // Actions - Filtering & Pagination (New)
  setFilters: (filters: Partial<DocumentListFilters>) => void;
  resetFilters: () => void;
  loadDocuments: (projectId?: string) => Promise<void>;
  loadNextPage: (projectId?: string) => Promise<void>;
  resetPagination: () => void;

  // Actions - Document Selection (New)
  toggleDocumentSelection: (documentId: string) => void;
  setDocumentSelection: (documentIds: string[]) => void;
  clearSelection: () => void;
  selectAll: () => void;
  unselectAll: () => void;

  // Actions - Document Details & Analytics (New)
  loadDocumentDetails: (documentId: string) => Promise<DocumentDetails>;
  loadDocumentAnalytics: (documentId: string) => Promise<DocumentAnalytics>;

  // Actions - Bulk Operations (New)
  bulkDeleteSelected: (projectId?: string) => Promise<void>;
  bulkImportFiles: (files: File[], projectId?: string) => Promise<void>;
}

export const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  // Initial state - Existing
  documents: new Map(),
  searchResults: [],
  currentQuery: '',
  isLoading: false,
  isImporting: false,
  isSearching: false,
  error: null,
  lastSearchedProject: null,

  // Initial state - Filtering & Pagination (New)
  filters: {
    projectId: undefined,
    documentType: undefined,
    searchQuery: '',
    sortBy: 'uploaded_at',
    sortOrder: 'desc',
  },
  pagination: {
    total: 0,
    limit: 50,
    offset: 0,
    hasMore: false,
  },
  selectedDocuments: new Set(),
  bulkOperationProgress: {
    type: null,
    current: 0,
    total: 0,
    completed: [],
    failed: [],
  },
  documentDetailsCache: new Map(),
  documentAnalyticsCache: new Map(),
  isBulkOperationLoading: false,

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

  // ========== NEW ACTIONS: FILTERING & PAGINATION ==========

  /**
   * Update document filters
   */
  setFilters: (newFilters: Partial<DocumentListFilters>) => {
    const state = get();
    set({
      filters: { ...state.filters, ...newFilters },
      pagination: { ...state.pagination, offset: 0 }, // Reset to first page
    });
  },

  /**
   * Reset all filters to defaults
   */
  resetFilters: () => {
    set({
      filters: {
        projectId: undefined,
        documentType: undefined,
        searchQuery: '',
        sortBy: 'uploaded_at',
        sortOrder: 'desc',
      },
      pagination: {
        total: 0,
        limit: 50,
        offset: 0,
        hasMore: false,
      },
    });
  },

  /**
   * Load documents with current filters and pagination
   */
  loadDocuments: async (projectId?: string) => {
    set({ isLoading: true, error: null });
    try {
      const state = get();
      const filters = {
        ...state.filters,
        projectId: projectId || state.filters.projectId,
      };

      const response = await knowledgeAPI.listDocuments(filters);
      const documentsMap = new Map<string, DocumentMetadata>();

      // Handle different response formats
      const documents = response?.documents || response?.data?.documents || [];
      const docArray = Array.isArray(documents) ? documents : [];

      docArray.forEach((doc: any) => {
        if (doc.id) {
          documentsMap.set(doc.id, doc);
        }
      });

      // Extract pagination info
      const paginationData = response?.pagination || response?.data?.pagination;
      const pagination: PaginationState = {
        total: paginationData?.total || response?.total || 0,
        limit: state.pagination.limit,
        offset: state.pagination.offset,
        hasMore: paginationData?.has_more ?? (state.pagination.offset + state.pagination.limit < (paginationData?.total || response?.total || 0)),
      };

      set({
        documents: documentsMap,
        pagination,
        isLoading: false,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load documents';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  /**
   * Load next page of documents
   */
  loadNextPage: async (projectId?: string) => {
    const state = get();
    if (!state.pagination.hasMore) return;

    set({ isLoading: true, error: null });
    try {
      const newOffset = state.pagination.offset + state.pagination.limit;
      const filters = {
        ...state.filters,
        projectId: projectId || state.filters.projectId,
        limit: state.pagination.limit,
        offset: newOffset,
      };

      const response = await knowledgeAPI.listDocuments(filters);
      const documentsMap = new Map(state.documents);

      // Handle different response formats
      const documents = response?.documents || response?.data?.documents || [];
      const docArray = Array.isArray(documents) ? documents : [];

      docArray.forEach((doc: any) => {
        if (doc.id) {
          documentsMap.set(doc.id, doc);
        }
      });

      // Extract pagination info
      const paginationData = response?.pagination || response?.data?.pagination;
      const pagination: PaginationState = {
        total: paginationData?.total || response?.total || 0,
        limit: state.pagination.limit,
        offset: newOffset,
        hasMore: paginationData?.has_more ?? (newOffset + state.pagination.limit < (paginationData?.total || response?.total || 0)),
      };

      set({
        documents: documentsMap,
        pagination,
        isLoading: false,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load more documents';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  /**
   * Reset pagination to first page
   */
  resetPagination: () => {
    set({
      pagination: {
        total: 0,
        limit: 50,
        offset: 0,
        hasMore: false,
      },
    });
  },

  // ========== NEW ACTIONS: DOCUMENT SELECTION ==========

  /**
   * Toggle document selection
   */
  toggleDocumentSelection: (documentId: string) => {
    const state = get();
    const newSelected = new Set(state.selectedDocuments);
    if (newSelected.has(documentId)) {
      newSelected.delete(documentId);
    } else {
      newSelected.add(documentId);
    }
    set({ selectedDocuments: newSelected });
  },

  /**
   * Set document selection to specific IDs
   */
  setDocumentSelection: (documentIds: string[]) => {
    set({ selectedDocuments: new Set(documentIds) });
  },

  /**
   * Clear all document selections
   */
  clearSelection: () => {
    set({ selectedDocuments: new Set() });
  },

  /**
   * Select all current documents
   */
  selectAll: () => {
    const state = get();
    const allIds = Array.from(state.documents.keys());
    set({ selectedDocuments: new Set(allIds) });
  },

  /**
   * Deselect all documents
   */
  unselectAll: () => {
    set({ selectedDocuments: new Set() });
  },

  // ========== NEW ACTIONS: DOCUMENT DETAILS & ANALYTICS ==========

  /**
   * Load document details with caching
   */
  loadDocumentDetails: async (documentId: string) => {
    const state = get();

    // Return cached version if available
    const cached = state.documentDetailsCache.get(documentId);
    if (cached) {
      return cached;
    }

    try {
      const response = await knowledgeAPI.getDocumentDetails(documentId, true);
      const details = response.document || response;

      // Cache the result
      const newCache = new Map(state.documentDetailsCache);
      newCache.set(documentId, details);
      set({ documentDetailsCache: newCache });

      return details;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load document details';
      set({ error: message });
      throw err;
    }
  },

  /**
   * Load document analytics with caching
   */
  loadDocumentAnalytics: async (documentId: string) => {
    const state = get();

    // Return cached version if available
    const cached = state.documentAnalyticsCache.get(documentId);
    if (cached) {
      return cached;
    }

    try {
      const response = await knowledgeAPI.getDocumentAnalytics(documentId);
      const analytics = response.analytics || response;

      // Cache the result
      const newCache = new Map(state.documentAnalyticsCache);
      newCache.set(documentId, analytics);
      set({ documentAnalyticsCache: newCache });

      return analytics;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load analytics';
      set({ error: message });
      throw err;
    }
  },

  // ========== NEW ACTIONS: BULK OPERATIONS ==========

  /**
   * Delete all selected documents
   */
  bulkDeleteSelected: async (projectId?: string) => {
    const state = get();
    const selectedIds = Array.from(state.selectedDocuments);

    if (selectedIds.length === 0) return;

    set({
      isBulkOperationLoading: true,
      error: null,
      bulkOperationProgress: {
        type: 'delete',
        current: 0,
        total: selectedIds.length,
        completed: [],
        failed: [],
      },
    });

    try {
      const response = await knowledgeAPI.bulkDeleteDocuments(selectedIds);

      // Update documents map - remove deleted ones
      const newDocuments = new Map(state.documents);
      selectedIds.forEach((id) => {
        newDocuments.delete(id);
      });

      set({
        documents: newDocuments,
        selectedDocuments: new Set(),
        isBulkOperationLoading: false,
        bulkOperationProgress: {
          type: null,
          current: 0,
          total: 0,
          completed: response.deleted || selectedIds,
          failed: response.failed || [],
        },
      });

      // Refresh document list
      await get().loadDocuments(projectId);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to delete documents';
      set({
        error: message,
        isBulkOperationLoading: false,
        bulkOperationProgress: {
          type: null,
          current: 0,
          total: 0,
          completed: [],
          failed: selectedIds.map((id) => ({ id, reason: message })),
        },
      });
      throw err;
    }
  },

  /**
   * Import multiple files with progress tracking
   */
  bulkImportFiles: async (files: File[], projectId?: string) => {
    if (files.length === 0) return;

    set({
      isBulkOperationLoading: true,
      isImporting: true,
      error: null,
      bulkOperationProgress: {
        type: 'import',
        current: 0,
        total: files.length,
        completed: [],
        failed: [],
      },
    });

    try {
      const response = await knowledgeAPI.bulkImportDocuments(files, projectId);

      // Extract results
      const completed = response.results
        ?.filter((r: any) => r.status === 'success')
        .map((r: any) => r.file) || [];
      const failed = response.results
        ?.filter((r: any) => r.status === 'failed')
        .map((r: any) => ({
          id: r.file,
          reason: r.error || 'Import failed',
        })) || [];

      set({
        isBulkOperationLoading: false,
        isImporting: false,
        bulkOperationProgress: {
          type: null,
          current: 0,
          total: 0,
          completed,
          failed,
        },
      });

      // Refresh document list
      await get().loadDocuments(projectId);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Bulk import failed';
      set({
        error: message,
        isBulkOperationLoading: false,
        isImporting: false,
        bulkOperationProgress: {
          type: null,
          current: 0,
          total: 0,
          completed: [],
          failed: files.map((f) => ({ id: f.name, reason: message })),
        },
      });
      throw err;
    }
  },
}));
