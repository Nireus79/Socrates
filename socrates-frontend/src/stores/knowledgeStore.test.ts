/**
 * Unit tests for knowledge store - Optimistic updates for bulk operations
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useKnowledgeStore } from './knowledgeStore';
import * as knowledgeAPI from '../api/knowledge';

// Mock the API
vi.mock('../api/knowledge');

describe('Knowledge Store - Optimistic Updates', () => {
  beforeEach(() => {
    // Reset store before each test
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
      selectedDocuments: new Set(['doc1', 'doc2']),
      error: null,
      isBulkOperationLoading: false,
    });

    vi.clearAllMocks();
  });

  describe('bulkDeleteSelected', () => {
    it('should remove documents optimistically before API call', async () => {
      const { bulkDeleteSelected } = useKnowledgeStore.getState();

      // Mock successful API response
      vi.mocked(knowledgeAPI.bulkDeleteDocuments).mockResolvedValue({
        deleted: ['doc1', 'doc2'],
        failed: [],
        total: 2,
      });

      // Mock loadDocuments to prevent additional API call
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
      expect(state.selectedDocuments.size).toBe(2);

      await bulkDeleteSelected('project1');

      state = useKnowledgeStore.getState();
      // Documents should be removed
      expect(state.documents.size).toBe(1);
      expect(state.documents.has('doc1')).toBe(false);
      expect(state.documents.has('doc2')).toBe(false);
      expect(state.documents.has('doc3')).toBe(true);
      expect(state.selectedDocuments.size).toBe(0);
      expect(state.isBulkOperationLoading).toBe(false);
    });

    it('should rollback on API failure', async () => {
      const { bulkDeleteSelected } = useKnowledgeStore.getState();
      const originalDocuments = new Map(useKnowledgeStore.getState().documents);

      // Mock API failure
      vi.mocked(knowledgeAPI.bulkDeleteDocuments).mockRejectedValue(
        new Error('Delete failed')
      );

      const deletePromise = bulkDeleteSelected('project1');

      await expect(deletePromise).rejects.toThrow('Delete failed');

      const state = useKnowledgeStore.getState();
      // Documents should be restored
      expect(state.documents.size).toBe(originalDocuments.size);
      expect(state.error).toBe('Delete failed');
      expect(state.isBulkOperationLoading).toBe(false);
    });

    it('should update progress during operation', async () => {
      const { bulkDeleteSelected } = useKnowledgeStore.getState();

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
      expect(state.isBulkOperationLoading).toBe(false);

      const deletePromise = bulkDeleteSelected('project1');

      state = useKnowledgeStore.getState();
      expect(state.isBulkOperationLoading).toBe(true);
      expect(state.bulkOperationProgress.type).toBe('delete');
      expect(state.bulkOperationProgress.total).toBe(2);

      await deletePromise;

      state = useKnowledgeStore.getState();
      expect(state.isBulkOperationLoading).toBe(false);
    });
  });
});
