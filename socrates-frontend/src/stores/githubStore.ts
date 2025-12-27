/**
 * GitHub Store - GitHub integration state management
 */

import { create } from 'zustand';
import * as githubAPI from '../api/github';

interface GitHubState {
  // State
  selectedProjectId: string | null;
  isLoading: boolean;
  error: string | null;
  syncStatus: any | null;
  isConnected: boolean;

  // Actions
  setSelectedProject: (projectId: string | null) => void;
  importRepository: (url: string, projectName?: string) => Promise<void>;
  pullFromGithub: (projectId: string) => Promise<void>;
  pushToGithub: (projectId: string, message?: string) => Promise<void>;
  syncWithGithub: (projectId: string) => Promise<void>;
  getStatus: (projectId: string) => Promise<void>;
  disconnect: (projectId: string) => Promise<void>;
  clearError: () => void;
}

export const useGithubStore = create<GitHubState>((set) => ({
  selectedProjectId: null,
  isLoading: false,
  error: null,
  syncStatus: null,
  isConnected: false,

  setSelectedProject: (projectId: string | null) => {
    set({ selectedProjectId: projectId });
  },

  importRepository: async (url: string, projectName?: string) => {
    set({ isLoading: true, error: null });
    try {
      const result = await githubAPI.importRepository({ url, project_name: projectName });
      set({
        isLoading: false,
        isConnected: true,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to import repository';
      set({ error: message, isLoading: false });
    }
  },

  pullFromGithub: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      await githubAPI.pullFromGithub(projectId);
      set({ isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to pull from GitHub';
      set({ error: message, isLoading: false });
    }
  },

  pushToGithub: async (projectId: string, message?: string) => {
    set({ isLoading: true, error: null });
    try {
      await githubAPI.pushToGithub(projectId, message);
      set({ isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to push to GitHub';
      set({ error: message, isLoading: false });
    }
  },

  syncWithGithub: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      await githubAPI.syncWithGithub(projectId);
      set({ isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to sync with GitHub';
      set({ error: message, isLoading: false });
    }
  },

  getStatus: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const status = await githubAPI.getGithubStatus(projectId);
      set({
        syncStatus: status,
        isLoading: false,
        isConnected: status.status === 'synced',
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to get status';
      set({ error: message, isLoading: false });
    }
  },

  disconnect: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      await githubAPI.disconnectGithub(projectId);
      set({
        isLoading: false,
        isConnected: false,
        syncStatus: null,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to disconnect';
      set({ error: message, isLoading: false });
    }
  },

  clearError: () => {
    set({ error: null });
  },
}));
