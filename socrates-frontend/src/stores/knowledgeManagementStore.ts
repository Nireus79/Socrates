/**
 * Knowledge Management Store - Zustand state management
 *
 * Manages Phase 4 knowledge management endpoints:
 * - Add knowledge items
 * - List and filter knowledge
 * - Search knowledge base
 * - Remember/pin items
 * - Remove items
 * - Export/import functionality
 */

import { create } from 'zustand';
import { apiClient } from '../api/client';
import type { SuccessResponse } from '../api/types';

interface KnowledgeItem {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  created_at: string;
  created_by: string;
  pinned: boolean;
  usage_count: number;
}

interface KnowledgeManagementState {
  // State
  knowledgeItems: KnowledgeItem[];
  filteredItems: KnowledgeItem[];
  isLoading: boolean;
  isSearching: boolean;
  error: string | null;
  currentProjectId: string | null;
  currentFilter: {
    category?: string;
    tag?: string;
    pinnedOnly: boolean;
  };

  // Actions
  addKnowledge: (
    projectId: string,
    title: string,
    content: string,
    category?: string,
    tags?: string[]
  ) => Promise<void>;
  listKnowledge: (projectId: string, category?: string, tag?: string) => Promise<void>;
  searchKnowledge: (projectId: string, query: string, limit?: number) => Promise<void>;
  rememberKnowledge: (projectId: string, knowledgeId: string) => Promise<void>;
  removeKnowledge: (projectId: string, knowledgeId: string) => Promise<void>;
  exportKnowledge: (
    projectId: string,
    format?: 'json' | 'markdown' | 'csv'
  ) => Promise<void>;
  importKnowledge: (projectId: string, items: KnowledgeItem[], merge?: boolean) => Promise<void>;
  setPinnedOnly: (pinnedOnly: boolean) => Promise<void>;
  clearError: () => void;
}

export const useKnowledgeManagementStore = create<KnowledgeManagementState>(
  (set, get) => ({
    // Initial state
    knowledgeItems: [],
    filteredItems: [],
    isLoading: false,
    isSearching: false,
    error: null,
    currentProjectId: null,
    currentFilter: {
      pinnedOnly: false,
    },

    // Add knowledge item
    addKnowledge: async (
      projectId: string,
      title: string,
      content: string,
      category = 'general',
      tags = []
    ) => {
      set({ isLoading: true, error: null });
      try {
        const response = await apiClient.post<SuccessResponse>(
          `/projects/${projectId}/knowledge/add`,
          {
            title,
            content,
            category,
            tags,
          }
        );

        if (response.success) {
          // Refresh knowledge list
          await get().listKnowledge(projectId);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to add knowledge';
        set({ error: message, isLoading: false });
        throw err;
      }
    },

    // List knowledge items
    listKnowledge: async (projectId: string, category?: string, tag?: string) => {
      set({ isLoading: true, error: null, currentProjectId: projectId });
      try {
        let url = `/projects/${projectId}/knowledge/list`;
        const params = new URLSearchParams();

        if (category) params.append('category', category);
        if (tag) params.append('tag', tag);
        if (get().currentFilter.pinnedOnly) params.append('pinned_only', 'true');

        if (params.toString()) {
          url += `?${params.toString()}`;
        }

        const response = await apiClient.get<SuccessResponse>(url);

        if (response.success && response.data) {
          set({
            knowledgeItems: response.data.items || [],
            filteredItems: response.data.items || [],
            isLoading: false,
          });
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to list knowledge';
        set({ error: message, isLoading: false });
        throw err;
      }
    },

    // Search knowledge
    searchKnowledge: async (projectId: string, query: string, limit = 10) => {
      set({ isSearching: true, error: null });
      try {
        const response = await apiClient.post<SuccessResponse>(
          `/projects/${projectId}/knowledge/search`,
          {
            query,
            limit,
          }
        );

        if (response.success && response.data) {
          set({
            filteredItems: response.data.results || [],
            isSearching: false,
          });
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to search knowledge';
        set({ error: message, isSearching: false });
        throw err;
      }
    },

    // Remember/pin knowledge item
    rememberKnowledge: async (projectId: string, knowledgeId: string) => {
      set({ isLoading: true, error: null });
      try {
        await apiClient.post(`/projects/${projectId}/knowledge/remember`, {
          knowledge_id: knowledgeId,
        });

        // Refresh list
        await get().listKnowledge(projectId);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to remember knowledge';
        set({ error: message, isLoading: false });
        throw err;
      }
    },

    // Remove knowledge item
    removeKnowledge: async (projectId: string, knowledgeId: string) => {
      set({ isLoading: true, error: null });
      try {
        await apiClient.delete(`/projects/${projectId}/knowledge/${knowledgeId}`);

        // Update local state
        const { knowledgeItems, filteredItems } = get();
        set({
          knowledgeItems: knowledgeItems.filter((item) => item.id !== knowledgeId),
          filteredItems: filteredItems.filter((item) => item.id !== knowledgeId),
          isLoading: false,
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to remove knowledge';
        set({ error: message, isLoading: false });
        throw err;
      }
    },

    // Export knowledge
    exportKnowledge: async (projectId: string, format = 'json') => {
      set({ isLoading: true, error: null });
      try {
        const response = await apiClient.post<SuccessResponse>(
          `/projects/${projectId}/knowledge/export`,
          {
            format,
          }
        );

        if (response.success && response.data) {
          // Trigger download
          const dataStr = JSON.stringify(response.data.export_data, null, 2);
          const dataBlob = new Blob([dataStr], { type: 'application/json' });
          const url = URL.createObjectURL(dataBlob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `knowledge-export-${new Date().toISOString()}.${format}`;
          link.click();
          URL.revokeObjectURL(url);

          set({ isLoading: false });
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to export knowledge';
        set({ error: message, isLoading: false });
        throw err;
      }
    },

    // Import knowledge
    importKnowledge: async (projectId: string, items: KnowledgeItem[], merge = true) => {
      set({ isLoading: true, error: null });
      try {
        const response = await apiClient.post<SuccessResponse>(
          `/projects/${projectId}/knowledge/import`,
          {
            knowledge_items: items,
            merge,
          }
        );

        if (response.success) {
          // Refresh knowledge list
          await get().listKnowledge(projectId);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to import knowledge';
        set({ error: message, isLoading: false });
        throw err;
      }
    },

    // Set pinned only filter
    setPinnedOnly: async (pinnedOnly: boolean) => {
      set((state) => ({
        currentFilter: {
          ...state.currentFilter,
          pinnedOnly,
        },
      }));

      // Refresh if project is loaded
      const { currentProjectId } = get();
      if (currentProjectId) {
        await get().listKnowledge(currentProjectId);
      }
    },

    // Clear error
    clearError: () => {
      set({ error: null });
    },
  })
);
