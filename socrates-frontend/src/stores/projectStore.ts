/**
 * Project Store - Project management state
 */

import { create } from 'zustand';
import type { Project, ProjectStats, ProjectMaturity, ProjectPhase } from '../types/models';
import { projectsAPI, codeGenerationAPI } from '../api';

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  language?: string;
  size?: number;
  children?: FileNode[];
  content?: string;
  createdAt?: string;
  updatedAt?: string;
  id?: string;
}

interface ProjectState {
  // State
  projects: Project[];
  currentProject: Project | null;
  projectStats: ProjectStats | null;
  projectMaturity: ProjectMaturity | null;
  isLoading: boolean;
  error: string | null;

  // File management
  files: FileNode[];
  selectedFile: FileNode | null;
  fileContent: string;
  codeHistory: any[];

  // Undo/Redo
  history: Project[];
  historyIndex: number;
  pendingUpdates: Map<string, any>;

  // Actions
  listProjects: (owner?: string) => Promise<void>;
  getProject: (projectId: string) => Promise<void>;
  setCurrentProject: (project: Project | null) => void;
  createProject: (name: string, description?: string, knowledgeBase?: string) => Promise<Project>;
  updateProject: (projectId: string, name?: string, phase?: ProjectPhase) => Promise<Project>;
  deleteProject: (projectId: string) => Promise<void>;
  restoreProject: (projectId: string) => Promise<Project>;
  fetchStats: (projectId: string) => Promise<void>;
  fetchMaturity: (projectId: string) => Promise<void>;
  advancePhase: (projectId: string, newPhase: ProjectPhase) => Promise<void>;
  getOrCreateOnboardingProject: () => Promise<string>;

  // File management actions
  fetchProjectFiles: (projectId: string) => Promise<void>;
  selectFile: (file: FileNode | null) => void;
  clearFiles: () => void;
  setFileContent: (content: string) => void;

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
  files: [],
  selectedFile: null,
  fileContent: '',
  codeHistory: [],
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
  createProject: async (name: string, description?: string, knowledgeBase?: string) => {
    set({ isLoading: true, error: null });
    try {
      const newProject = await projectsAPI.createProject({
        name,
        description,
        knowledge_base_content: knowledgeBase,
      });
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

  // Fetch project files
  fetchProjectFiles: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const filesResponse = await projectsAPI.getProjectFiles(projectId);
      const codeHistoryResponse = await codeGenerationAPI.getCodeHistory(projectId);

      // Build file nodes from files, with content from code history
      const fileNodes: FileNode[] = (filesResponse.files || []).map((file: any) => {
        let content = '';

        // Try to find matching code from code history
        if (codeHistoryResponse.generations && codeHistoryResponse.generations.length > 0) {
          // Method 1: Try to match by file ID (most reliable)
          let codeItem = codeHistoryResponse.generations.find((c: any) => c.file_id === file.id);

          // Method 2: Try to match by generation ID extracted from filename
          if (!codeItem) {
            const match = file.name.match(/(?:generated|refactored)_(.+)\.\w+/);
            const generationId = match ? match[1] : null;
            if (generationId) {
              codeItem = codeHistoryResponse.generations.find((c: any) => c.generation_id === generationId);
            }
          }

          // Method 3: Try to match by filename pattern as last resort
          if (!codeItem && file.name) {
            codeItem = codeHistoryResponse.generations.find((c: any) => {
              const codeFileName = c.filename || c.file_name || '';
              return codeFileName === file.name || codeFileName.includes(file.name);
            });
          }

          if (codeItem) {
            content = codeItem.code || codeItem.refactored_code || '';
          }
        }

        return {
          id: file.id,
          name: file.name,
          path: file.path,
          type: 'file',
          language: file.type,
          size: file.size,
          createdAt: file.created_at,
          updatedAt: file.updated_at,
          content,
        };
      });

      set({
        files: fileNodes,
        codeHistory: codeHistoryResponse.generations || [],
        isLoading: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch files',
        isLoading: false,
      });
      throw error;
    }
  },

  // Select a file
  selectFile: (file: FileNode | null) => {
    set({
      selectedFile: file,
      fileContent: file?.content || '',
    });
  },

  // Clear files
  clearFiles: () => {
    set({
      files: [],
      selectedFile: null,
      fileContent: '',
      codeHistory: [],
    });
  },

  // Set file content
  setFileContent: (content: string) => {
    set({ fileContent: content });
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

export type { FileNode };
