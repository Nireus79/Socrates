/**
 * Integration tests for full knowledge base workflows
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useKnowledgeStore } from '../../stores/knowledgeStore';
import { useNotificationStore } from '../../stores/notificationStore';
import * as knowledgeAPI from '../../api/knowledge';

// Mock the API
vi.mock('../../api/knowledge');

describe('Knowledge Base Workflow Integration Tests', () => {
  beforeEach(() => {
    const documents = new Map();
    documents.set('doc1', {
      id: 'doc1',
      title: 'Document 1',
      type: 'text',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      content: 'Content 1',
      source: 'manual',
    });
    documents.set('doc2', {
      id: 'doc2',
      title: 'Document 2',
      type: 'file',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      content: 'Content 2',
      source: 'upload',
    });
    documents.set('doc3', {
      id: 'doc3',
      title: 'Document 3',
      type: 'url',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      content: 'Content 3',
      source: 'url',
    });

    useKnowledgeStore.setState({
      documents,
      selectedDocuments: new Set(),
      error: null,
      isLoading: false,
      filters: {
        documentType: null,
        searchQuery: '',
        sortBy: 'created_at',
        sortOrder: 'desc',
      },
    });

    useNotificationStore.setState({ notifications: [] });

    vi.clearAllMocks();
  });

  describe('Document Filtering Flow', () => {
    it('should filter documents by type', async () => {
      const filteredDocs = [
        {
          id: 'doc1',
          title: 'Document 1',
          type: 'text',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          content: 'Content 1',
          source: 'manual',
        },
      ];

      vi.mocked(knowledgeAPI.listDocuments).mockResolvedValue({
        documents: filteredDocs,
        total: 1,
        limit: 50,
        offset: 0,
      });

      const { setFilters, loadDocuments } = useKnowledgeStore.getState();

      setFilters({ documentType: 'text' });
      await loadDocuments('project-123');

      const state = useKnowledgeStore.getState();
      expect(state.filters.documentType).toBe('text');
      expect(knowledgeAPI.listDocuments).toHaveBeenCalled();
    });

    it('should search documents', async () => {
      const searchResults = [
        {
          id: 'doc2',
          title: 'Document 2',
          type: 'file',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          content: 'Content matching search',
          source: 'upload',
        },
      ];

      vi.mocked(knowledgeAPI.listDocuments).mockResolvedValue({
        documents: searchResults,
        total: 1,
        limit: 50,
        offset: 0,
      });

      const { setFilters, loadDocuments } = useKnowledgeStore.getState();

      setFilters({ searchQuery: 'search term' });
      await loadDocuments('project-123');

      const state = useKnowledgeStore.getState();
      expect(state.filters.searchQuery).toBe('search term');
    });

    it('should sort documents', async () => {
      const { setFilters } = useKnowledgeStore.getState();

      setFilters({ sortBy: 'title', sortOrder: 'asc' });

      const state = useKnowledgeStore.getState();
      expect(state.filters.sortBy).toBe('title');
      expect(state.filters.sortOrder).toBe('asc');
    });

    it('should reset filters', async () => {
      const { setFilters } = useKnowledgeStore.getState();

      setFilters({ documentType: 'text', searchQuery: 'test' });
      let state = useKnowledgeStore.getState();
      expect(state.filters.documentType).toBe('text');

      // Reset filters
      const { resetFilters } = useKnowledgeStore.getState();
      resetFilters();

      state = useKnowledgeStore.getState();
      expect(state.filters.documentType).toBeNull();
      expect(state.filters.searchQuery).toBe('');
    });
  });

  describe('Selection & Bulk Operations Flow', () => {
    it('should select and deselect documents', () => {
      const { toggleDocumentSelection, selectAll, clearSelection } =
        useKnowledgeStore.getState();

      toggleDocumentSelection('doc1');
      let state = useKnowledgeStore.getState();
      expect(state.selectedDocuments.has('doc1')).toBe(true);

      toggleDocumentSelection('doc1');
      state = useKnowledgeStore.getState();
      expect(state.selectedDocuments.has('doc1')).toBe(false);
    });

    it('should select all documents', () => {
      const { selectAll } = useKnowledgeStore.getState();

      selectAll();

      const state = useKnowledgeStore.getState();
      expect(state.selectedDocuments.size).toBe(3);
      expect(state.selectedDocuments.has('doc1')).toBe(true);
      expect(state.selectedDocuments.has('doc2')).toBe(true);
      expect(state.selectedDocuments.has('doc3')).toBe(true);
    });

    it('should clear selection', () => {
      const { selectAll, clearSelection } = useKnowledgeStore.getState();

      selectAll();
      let state = useKnowledgeStore.getState();
      expect(state.selectedDocuments.size).toBe(3);

      clearSelection();
      state = useKnowledgeStore.getState();
      expect(state.selectedDocuments.size).toBe(0);
    });
  });

  describe('Bulk Delete Flow (Optimistic)', () => {
    beforeEach(() => {
      useKnowledgeStore.setState({
        selectedDocuments: new Set(['doc1', 'doc2']),
      });
    });

    it('should delete selected documents with optimistic update', async () => {
      vi.mocked(knowledgeAPI.bulkDeleteDocuments).mockResolvedValue({
        deleted: ['doc1', 'doc2'],
        failed: [],
        total: 2,
      });

      vi.mocked(knowledgeAPI.listDocuments).mockResolvedValue({
        documents: [
          {
            id: 'doc3',
            title: 'Document 3',
            type: 'url',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            content: 'Content 3',
            source: 'url',
          },
        ],
        total: 1,
        limit: 50,
        offset: 0,
      });

      let state = useKnowledgeStore.getState();
      expect(state.documents.size).toBe(3);

      const { bulkDeleteSelected } = useKnowledgeStore.getState();

      // Start deletion (optimistic)
      const deletePromise = bulkDeleteSelected('project-123');

      // Immediately check optimistic state
      state = useKnowledgeStore.getState();
      expect(state.documents.size).toBe(1);
      expect(state.documents.has('doc1')).toBe(false);
      expect(state.documents.has('doc2')).toBe(false);

      await deletePromise;

      state = useKnowledgeStore.getState();
      expect(state.isBulkOperationLoading).toBe(false);
      expect(state.selectedDocuments.size).toBe(0);
    });

    it('should restore documents on bulk delete failure', async () => {
      const errorMessage = 'Deletion failed';
      vi.mocked(knowledgeAPI.bulkDeleteDocuments).mockRejectedValue(
        new Error(errorMessage)
      );

      const originalDocuments = new Map(
        useKnowledgeStore.getState().documents
      );

      const { bulkDeleteSelected } = useKnowledgeStore.getState();

      try {
        await bulkDeleteSelected('project-123');
      } catch (error) {
        // Expected
      }

      const state = useKnowledgeStore.getState();
      // Documents should be restored
      expect(state.documents.size).toBe(originalDocuments.size);
      expect(state.error).toBe(errorMessage);
    });

    it('should track bulk operation progress', async () => {
      vi.mocked(knowledgeAPI.bulkDeleteDocuments).mockResolvedValue({
        deleted: ['doc1', 'doc2'],
        failed: [],
        total: 2,
      });

      vi.mocked(knowledgeAPI.listDocuments).mockResolvedValue({
        documents: [],
        total: 0,
        limit: 50,
        offset: 0,
      });

      const { bulkDeleteSelected } = useKnowledgeStore.getState();

      const deletePromise = bulkDeleteSelected('project-123');

      let state = useKnowledgeStore.getState();
      expect(state.bulkOperationProgress.type).toBe('delete');
      expect(state.bulkOperationProgress.total).toBe(2);
      expect(state.isBulkOperationLoading).toBe(true);

      await deletePromise;

      state = useKnowledgeStore.getState();
      expect(state.isBulkOperationLoading).toBe(false);
    });
  });

  describe('Bulk Import Flow', () => {
    it('should import multiple files with progress tracking', async () => {
      const mockFiles = [
        new File(['content 1'], 'file1.txt', { type: 'text/plain' }),
        new File(['content 2'], 'file2.pdf', { type: 'application/pdf' }),
      ];

      vi.mocked(knowledgeAPI.bulkImportDocuments).mockResolvedValue({
        imported: 2,
        failed: 0,
        total: 2,
        documents: [
          {
            id: 'doc4',
            title: 'file1.txt',
            type: 'file',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            content: 'content 1',
            source: 'upload',
          },
          {
            id: 'doc5',
            title: 'file2.pdf',
            type: 'file',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            content: 'content 2',
            source: 'upload',
          },
        ],
      });

      const { bulkImportFiles } = useKnowledgeStore.getState();

      const importPromise = bulkImportFiles(mockFiles, 'project-123');

      let state = useKnowledgeStore.getState();
      expect(state.isBulkOperationLoading).toBe(true);

      await importPromise;

      state = useKnowledgeStore.getState();
      expect(state.isBulkOperationLoading).toBe(false);
      expect(knowledgeAPI.bulkImportDocuments).toHaveBeenCalled();
    });
  });

  describe('Document Details & Analytics', () => {
    it('should load document details', async () => {
      const mockDetails = {
        id: 'doc1',
        title: 'Document 1',
        type: 'text' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        content: 'Full content here',
        source: 'manual',
        word_count: 150,
        character_count: 890,
      };

      vi.mocked(knowledgeAPI.getDocumentDetails).mockResolvedValue(mockDetails);

      const { loadDocumentDetails } = useKnowledgeStore.getState();

      await loadDocumentDetails('doc1', true);

      expect(knowledgeAPI.getDocumentDetails).toHaveBeenCalledWith('doc1', true);
    });

    it('should load document analytics', async () => {
      const mockAnalytics = {
        id: 'doc1',
        views: 42,
        searches: 15,
        last_accessed: new Date().toISOString(),
        estimated_reading_time: 5,
      };

      vi.mocked(knowledgeAPI.getDocumentAnalytics).mockResolvedValue(mockAnalytics);

      const { loadDocumentAnalytics } = useKnowledgeStore.getState();

      await loadDocumentAnalytics('doc1');

      expect(knowledgeAPI.getDocumentAnalytics).toHaveBeenCalledWith('doc1');
    });
  });

  describe('Pagination Flow', () => {
    it('should load next page of documents', async () => {
      const page2Docs = [
        {
          id: 'doc4',
          title: 'Document 4',
          type: 'text',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          content: 'Content 4',
          source: 'manual',
        },
      ];

      vi.mocked(knowledgeAPI.listDocuments).mockResolvedValue({
        documents: page2Docs,
        total: 4,
        limit: 50,
        offset: 50,
      });

      const { loadNextPage } = useKnowledgeStore.getState();

      await loadNextPage('project-123');

      expect(knowledgeAPI.listDocuments).toHaveBeenCalled();
    });

    it('should reset pagination', () => {
      useKnowledgeStore.setState({
        pagination: {
          total: 100,
          limit: 50,
          offset: 50,
          hasMore: true,
        },
      });

      const { resetPagination } = useKnowledgeStore.getState();
      resetPagination();

      const state = useKnowledgeStore.getState();
      expect(state.pagination.offset).toBe(0);
      expect(state.pagination.hasMore).toBe(true);
    });
  });
});
