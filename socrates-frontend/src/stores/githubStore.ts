/**
 * GitHub Integration Store - Manages GitHub operations state
 * Uses Zustand for state management
 */

import { create } from 'zustand';
import { githubAPI } from '../api/github';
import type { GitHubImportRequest, GitHubSyncStatusResponse } from '../api/github';

interface GitHubState {
  // State
  isImporting: boolean;
  isLoading: boolean;
  error: string | null;
  syncStatuses: Map<string, GitHubSyncStatusResponse>;
  lastSyncedProject: string | null;

  // Actions
  importRepository: (request: GitHubImportRequest) => Promise<void>;
  pullChanges: (projectId: string) => Promise<void>;
  pushChanges: (projectId: string, commitMessage?: string) => Promise<void>;
  syncProject: (projectId: string, commitMessage?: string) => Promise<void>;
  getSyncStatus: (projectId: string) => Promise<void>;
  clearError: () => void;
}

export const useGitHubStore = create<GitHubState>((set, get) => ({
  // Initial state
  isImporting: false,
  isLoading: false,
  error: null,
  syncStatuses: new Map(),
  lastSyncedProject: null,

  // Import repository from GitHub
  importRepository: async (request: GitHubImportRequest) => {
    set({ isImporting: true, error: null });
    try {
      const result = await githubAPI.importRepository(request);
      set({
        isImporting: false,
        lastSyncedProject: result.project_id,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to import repository';
      set({ error: message, isImporting: false });
      throw err;
    }
  },

  // Pull latest changes from GitHub
  pullChanges: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      await githubAPI.pullChanges(projectId);
      set({ isLoading: false, lastSyncedProject: projectId });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to pull changes';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  // Push local changes to GitHub
  pushChanges: async (projectId: string, commitMessage?: string) => {
    set({ isLoading: true, error: null });
    try {
      await githubAPI.pushChanges(projectId, commitMessage);
      set({ isLoading: false, lastSyncedProject: projectId });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to push changes';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  // Sync with GitHub (pull then push)
  syncProject: async (projectId: string, commitMessage?: string) => {
    set({ isLoading: true, error: null });
    try {
      await githubAPI.syncProject(projectId, commitMessage);
      set({ isLoading: false, lastSyncedProject: projectId });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to sync with GitHub';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  // Get sync status for a project
  getSyncStatus: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const status = await githubAPI.getSyncStatus(projectId);
      set((state) => ({
        syncStatuses: new Map(state.syncStatuses).set(projectId, status),
        isLoading: false,
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get sync status';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  // Clear error message
  clearError: () => set({ error: null }),
}));

