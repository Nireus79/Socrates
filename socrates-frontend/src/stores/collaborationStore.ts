/**
 * Collaboration Store - Team collaboration and presence state
 */

import { create } from 'zustand';
import type { Collaborator, ProjectPresence, CollaboratorRole } from '../types/models';
import { collaborationAPI } from '../api';

export interface Activity {
  id: string;
  type: string;
  user: { name: string };
  action: string;
  timestamp: Date;
}

interface CollaborationState {
  // State
  collaborators: Collaborator[];
  activePresence: ProjectPresence[];
  activities: Activity[];
  currentProjectId: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  loadCollaborators: (projectId: string) => Promise<void>;
  addCollaborator: (projectId: string, username: string, role: CollaboratorRole) => Promise<void>;
  updateCollaboratorRole: (projectId: string, username: string, role: CollaboratorRole) => Promise<void>;
  removeCollaborator: (projectId: string, username: string) => Promise<void>;
  fetchPresence: (projectId: string) => Promise<void>;
  fetchActivities: (projectId: string) => Promise<void>;
  recordActivity: (projectId: string, activityType: string, data?: any) => Promise<void>;
  setCurrentProject: (projectId: string) => void;
  clearError: () => void;
}

export const useCollaborationStore = create<CollaborationState>((set) => ({
  // Initial state
  collaborators: [],
  activePresence: [],
  activities: [],
  currentProjectId: null,
  isLoading: false,
  error: null,

  // Load collaborators
  loadCollaborators: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await collaborationAPI.listCollaborators(projectId);
      set({ collaborators: response.collaborators, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load collaborators',
        isLoading: false,
      });
      throw error;
    }
  },

  // Add collaborator
  addCollaborator: async (projectId: string, username: string, role: CollaboratorRole) => {
    set({ isLoading: true, error: null });
    try {
      const response = await collaborationAPI.addCollaborator(projectId, username, role);
      set((state) => ({
        collaborators: [...state.collaborators, response.collaborator],
        isLoading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to add collaborator',
        isLoading: false,
      });
      throw error;
    }
  },

  // Update collaborator role
  updateCollaboratorRole: async (projectId: string, username: string, role: CollaboratorRole) => {
    set({ isLoading: true, error: null });
    try {
      const response = await collaborationAPI.updateCollaboratorRole(projectId, username, role);
      set((state) => ({
        collaborators: state.collaborators.map((c) =>
          c.username === username ? response.collaborator : c
        ),
        isLoading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to update role',
        isLoading: false,
      });
      throw error;
    }
  },

  // Remove collaborator
  removeCollaborator: async (projectId: string, username: string) => {
    set({ isLoading: true, error: null });
    try {
      await collaborationAPI.removeCollaborator(projectId, username);
      set((state) => ({
        collaborators: state.collaborators.filter((c) => c.username !== username),
        isLoading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to remove collaborator',
        isLoading: false,
      });
      throw error;
    }
  },

  // Fetch presence
  fetchPresence: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await collaborationAPI.getPresence(projectId);
      set({ activePresence: response.active_collaborators, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch presence',
        isLoading: false,
      });
      throw error;
    }
  },

  // Fetch activities
  fetchActivities: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await collaborationAPI.getActivities(projectId);
      const activities: Activity[] = (response.activities || []).map((a: any) => ({
        id: a.id,
        type: a.type,
        user: { name: a.user_name || 'Unknown' },
        action: a.description || a.action,
        timestamp: new Date(a.timestamp),
      }));
      set({ activities, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch activities',
        isLoading: false,
      });
      // Don't throw - activity fetching is non-critical
    }
  },

  // Record activity
  recordActivity: async (projectId: string, activityType: string, data?: any) => {
    try {
      await collaborationAPI.recordActivity(projectId, activityType, data);
    } catch (error) {
      // Don't set error state for activity recording - it's non-critical
      console.error('Failed to record activity:', error);
    }
  },

  // Set current project
  setCurrentProject: (projectId: string) => {
    set({ currentProjectId: projectId });
  },

  // Clear error
  clearError: () => set({ error: null }),
}));
