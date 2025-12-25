/**
 * Project Store - Project management state
 */

import { create } from 'zustand';
import type { Project, ProjectStats, ProjectMaturity, ProjectPhase } from '../types/models';
import { projectsAPI } from '../api';

interface ProjectState {
  // State
  projects: Project[];
  currentProject: Project | null;
  projectStats: ProjectStats | null;
  projectMaturity: ProjectMaturity | null;
  isLoading: boolean;
  error: string | null;

  // Undo/Redo
  history: Project[];
  historyIndex: number;
  pendingUpdates: Map<string, any>;

  // Actions
  listProjects: (owner?: string) => Promise<void>;
  getProject: (projectId: string) => Promise<void>;
  setCurrentProject: (project: Project | null) => void;
  createProject: (name: string, description?: string) => Promise<Project>;
  updateProject: (projectId: string, name?: string, phase?: ProjectPhase) => Promise<Project>;
  deleteProject: (projectId: string) => Promise<void>;
  restoreProject: (projectId: string) => Promise<Project>;
  fetchStats: (projectId: string) => Promise<void>;
  fetchMaturity: (projectId: string) => Promise<void>;
  advancePhase: (projectId: string, newPhase: ProjectPhase) => Promise<void>;
  getOrCreateOnboardingProject: () => Promise<string>;
  undo: () => void;
  redo: () => void;
  clearError: () => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  // Initial state
  projects: [],
  currentProject: null,
  projectStats: null,
  projectMaturity: null,
  isLoading: false,
  error: null,
  history: [],
  historyIndex: -1,
  pendingUpdates: new Map(),

  // List projects
  listProjects: async (owner?: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await projectsAPI.listProjects(owner);
      set({ projects: response.projects, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to list projects',
        isLoading: false,
      });
      throw error;
    }
  },

  // Get project
  getProject: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const project = await projectsAPI.getProject(projectId);
      set({ currentProject: project, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to get project',
        isLoading: false,
      });
      throw error;
    }
  },

  // Set current project
  setCurrentProject: (project: Project | null) => {
    set({ currentProject: project });
  },

  // Create project
  createProject: async (name: string, description?: string) => {
    set({ isLoading: true, error: null });
    try {
      const newProject = await projectsAPI.createProject({ name, description });
      set((state) => ({
    projects: [...state.projects, newProject],
    currentProject: newProject,
    isLoading: false,
    }));

      return newProject;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to create project',
        isLoading: false,
      });
      throw error;
    }
  },

  // Update project
  updateProject: async (projectId: string, name?: string, phase?: ProjectPhase) => {
    set((state) => {
      // Optimistic update
      if (state.currentProject?.project_id === projectId) {
        const optimisticProject = {
          ...state.currentProject,
          ...(name && { name }),
          ...(phase && { phase }),
        };
        state.pendingUpdates.set(projectId, { name, phase });
        return {
          currentProject: optimisticProject,
          projects: state.projects.map((p) =>
            p.project_id === projectId ? optimisticProject : p
          ),
        };
      }
      return state;
    });

    try {
      const updated = await projectsAPI.updateProject(projectId, { name, phase });
      set((state) => {
        state.pendingUpdates.delete(projectId);
        return {
          projects: state.projects.map((p) => (p.project_id === projectId ? updated : p)),
          currentProject: state.currentProject?.project_id === projectId ? updated : state.currentProject,
          isLoading: false,
        };
      });
      return updated;
    } catch (error) {
      set((state) => {
        state.pendingUpdates.delete(projectId);
        return {
          error: error instanceof Error ? error.message : 'Failed to update project',
          isLoading: false,
        };
      });
      throw error;
    }
  },

  // Delete (archive) project
  deleteProject: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      await projectsAPI.deleteProject(projectId);
      set((state) => ({
        projects: state.projects.map((p) =>
          p.project_id === projectId ? { ...p, is_archived: true } : p
        ),
        currentProject: state.currentProject?.project_id === projectId ? null : state.currentProject,
        isLoading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to delete project',
        isLoading: false,
      });
      throw error;
    }
  },

  // Restore project
  restoreProject: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const restored = await projectsAPI.restoreProject(projectId);
      set((state) => ({
        projects: state.projects.map((p) =>
          p.project_id === projectId ? restored : p
        ),
        isLoading: false,
      }));
      return restored;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to restore project',
        isLoading: false,
      });
      throw error;
    }
  },

  // Fetch stats
  fetchStats: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const stats = await projectsAPI.getProjectStats(projectId);
      set({ projectStats: stats, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch stats',
        isLoading: false,
      });
      throw error;
    }
  },

  // Fetch maturity
  fetchMaturity: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const maturity = await projectsAPI.getProjectMaturity(projectId);
      set({ projectMaturity: maturity, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch maturity',
        isLoading: false,
      });
      throw error;
    }
  },

  // Advance phase
  advancePhase: async (projectId: string, newPhase: ProjectPhase) => {
    set({ isLoading: true, error: null });
    try {
      const updated = await projectsAPI.advancePhase(projectId, newPhase);
      set((state) => ({
        projects: state.projects.map((p) => (p.project_id === projectId ? updated : p)),
        currentProject: state.currentProject?.project_id === projectId ? updated : state.currentProject,
        isLoading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to advance phase',
        isLoading: false,
      });
      throw error;
    }
  },

  // Get or create onboarding project for pre-session chat
  getOrCreateOnboardingProject: async () => {
    try {
      const state = useProjectStore.getState();

      // Check if onboarding project already exists
      const onboarding = state.projects.find(
        (p) => p.name === 'Onboarding Chat' && !p.is_archived
      );

      if (onboarding) {
        return onboarding.project_id;
      }

      // Create onboarding project
      const newProject = await projectsAPI.createProject({
        name: 'Onboarding Chat',
        description: 'Explore Socrates features and ask questions before creating your first project',
      });

      // Add to projects list
      set((state) => ({
        projects: [...state.projects, newProject],
      }));

      return newProject.project_id;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create onboarding project';
      set({ error: message });
      throw error;
    }
  },

  // Undo
  undo: () => {
    set((state) => {
      if (state.historyIndex > 0) {
        const newIndex = state.historyIndex - 1;
        return {
          currentProject: state.history[newIndex] || null,
          historyIndex: newIndex,
        };
      }
      return state;
    });
  },

  // Redo
  redo: () => {
    set((state) => {
      if (state.historyIndex < state.history.length - 1) {
        const newIndex = state.historyIndex + 1;
        return {
          currentProject: state.history[newIndex] || null,
          historyIndex: newIndex,
        };
      }
      return state;
    });
  },

  // Clear error
  clearError: () => set({ error: null }),
}));
