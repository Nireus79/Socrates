/**
 * Collaboration Store - Team collaboration and presence state
 */

import { create } from 'zustand';
import type {
  Collaborator,
  ProjectPresence,
  CollaboratorRole,
  Invitation,
  UserPresence,
  Activity as APIActivity,
} from '../types/models';
import { collaborationAPI } from '../api';

export interface Activity {
  id: string;
  type: string;
  user: { name: string };
  action: string;
  timestamp: Date;
}

export interface PaginationState {
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

interface CollaborationState {
  // State - Existing
  collaborators: Collaborator[];
  activePresence: ProjectPresence[];
  activities: Activity[];
  currentProjectId: string | null;
  isLoading: boolean;
  error: string | null;

  // State - Invitations (New)
  invitations: Invitation[];
  isLoadingInvitations: boolean;
  invitationError: string | null;

  // State - Real-time (New)
  activeUsers: Map<string, UserPresence>;
  typingUsers: Set<string>;
  wsConnected: boolean;
  lastSyncTime: Date | null;

  // State - Pagination (New)
  activitiesPagination: PaginationState;

  // Actions - Existing
  loadCollaborators: (projectId: string) => Promise<void>;
  addCollaborator: (projectId: string, username: string, role: CollaboratorRole) => Promise<void>;
  updateCollaboratorRole: (projectId: string, username: string, role: CollaboratorRole) => Promise<void>;
  removeCollaborator: (projectId: string, username: string) => Promise<void>;
  fetchPresence: (projectId: string) => Promise<void>;
  fetchActivities: (projectId: string, limit?: number, offset?: number) => Promise<void>;
  recordActivity: (projectId: string, activityType: string, data?: any) => Promise<void>;
  setCurrentProject: (projectId: string) => void;
  clearError: () => void;

  // Actions - Invitations (New)
  createInvitation: (projectId: string, email: string, role: CollaboratorRole) => Promise<void>;
  loadInvitations: (projectId: string) => Promise<void>;
  cancelInvitation: (projectId: string, invitationId: string) => Promise<void>;
  acceptInvitation: (token: string) => Promise<void>;
  clearInvitationError: () => void;

  // Actions - Real-time (New)
  connectWebSocket: (projectId: string) => Promise<void>;
  disconnectWebSocket: () => void;
  handleUserJoined: (username: string, presence: UserPresence) => void;
  handleUserLeft: (username: string) => void;
  handleTypingIndicator: (username: string, isTyping: boolean) => void;
  handleActivityBroadcast: (activity: APIActivity) => void;
  updatePresence: (users: UserPresence[]) => void;
  loadMoreActivities: (projectId: string) => Promise<void>;
}

export const useCollaborationStore = create<CollaborationState>((set, get) => ({
  // Initial state - Existing
  collaborators: [],
  activePresence: [],
  activities: [],
  currentProjectId: null,
  isLoading: false,
  error: null,

  // Initial state - Invitations (New)
  invitations: [],
  isLoadingInvitations: false,
  invitationError: null,

  // Initial state - Real-time (New)
  activeUsers: new Map(),
  typingUsers: new Set(),
  wsConnected: false,
  lastSyncTime: null,

  // Initial state - Pagination (New)
  activitiesPagination: {
    total: 0,
    limit: 50,
    offset: 0,
    hasMore: false,
  },

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
    // Optimistic update: remove immediately from UI
    const previousCollaborators = get().collaborators;
    set((state) => ({
      collaborators: state.collaborators.filter((c) => c.username !== username),
      isLoading: true,
      error: null,
    }));

    try {
      await collaborationAPI.removeCollaborator(projectId, username);
      set({ isLoading: false });
    } catch (error) {
      // Rollback: restore the collaborator on failure
      set({
        collaborators: previousCollaborators,
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

  // Fetch activities with pagination
  fetchActivities: async (projectId: string, limit: number = 50, offset: number = 0) => {
    set({ isLoading: true, error: null });
    try {
      const response = await collaborationAPI.getActivities(projectId, limit, offset);
      const activities: Activity[] = (response.activities || []).map((a: any) => ({
        id: a.id,
        type: a.activity_type || a.type,
        user: { name: a.user_id || 'Unknown' },
        action: a.activity_type || a.description || a.action,
        timestamp: new Date(a.created_at || a.timestamp),
      }));

      // Update pagination state
      const pagination = {
        total: response.total || 0,
        limit,
        offset,
        hasMore: offset + limit < (response.total || 0),
      };

      set({
        activities: offset === 0 ? activities : [...get().activities, ...activities],
        activitiesPagination: pagination,
        isLoading: false,
      });
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

  // ========== NEW ACTIONS: INVITATIONS ==========

  // Create invitation
  createInvitation: async (projectId: string, email: string, role: CollaboratorRole) => {
    set({ isLoadingInvitations: true, invitationError: null });
    try {
      const response = await collaborationAPI.createInvitation(projectId, email, role);
      // Convert response to Invitation type
      const invitation: Invitation = {
        id: response.id || response.invitation_id || '',
        project_id: projectId,
        inviter_id: '',
        invitee_email: response.email || email,
        role: response.role || role,
        token: response.token,
        status: response.status as 'pending' | 'accepted' | 'cancelled' | 'expired',
        created_at: response.created_at,
        expires_at: response.expires_at,
      };
      set((state) => ({
        invitations: [...state.invitations, invitation],
        isLoadingInvitations: false,
      }));
    } catch (error) {
      set({
        invitationError: error instanceof Error ? error.message : 'Failed to create invitation',
        isLoadingInvitations: false,
      });
      throw error;
    }
  },

  // Load invitations
  loadInvitations: async (projectId: string) => {
    set({ isLoadingInvitations: true, invitationError: null });
    try {
      const response = await collaborationAPI.listInvitations(projectId);
      set({
        invitations: response.invitations || [],
        isLoadingInvitations: false,
      });
    } catch (error) {
      set({
        invitationError: error instanceof Error ? error.message : 'Failed to load invitations',
        isLoadingInvitations: false,
      });
      throw error;
    }
  },

  // Cancel invitation
  cancelInvitation: async (projectId: string, invitationId: string) => {
    set({ isLoadingInvitations: true, invitationError: null });
    try {
      await collaborationAPI.cancelInvitation(projectId, invitationId);
      set((state) => ({
        invitations: state.invitations.filter((inv) => inv.id !== invitationId),
        isLoadingInvitations: false,
      }));
    } catch (error) {
      set({
        invitationError: error instanceof Error ? error.message : 'Failed to cancel invitation',
        isLoadingInvitations: false,
      });
      throw error;
    }
  },

  // Accept invitation
  acceptInvitation: async (token: string) => {
    set({ isLoadingInvitations: true, invitationError: null });
    try {
      await collaborationAPI.acceptInvitation(token);
      set({ isLoadingInvitations: false });
    } catch (error) {
      set({
        invitationError: error instanceof Error ? error.message : 'Failed to accept invitation',
        isLoadingInvitations: false,
      });
      throw error;
    }
  },

  // Clear invitation error
  clearInvitationError: () => set({ invitationError: null }),

  // ========== NEW ACTIONS: REAL-TIME ==========

  // Connect WebSocket
  connectWebSocket: async (projectId: string) => {
    set({ wsConnected: true, lastSyncTime: new Date() });
    // WebSocket implementation will be in a separate service
    // This action just manages the connection state in Zustand
  },

  // Disconnect WebSocket
  disconnectWebSocket: () => {
    set({ wsConnected: false, activeUsers: new Map(), typingUsers: new Set() });
  },

  // Handle user joined
  handleUserJoined: (username: string, presence: UserPresence) => {
    set((state) => {
      const newActiveUsers = new Map(state.activeUsers);
      newActiveUsers.set(username, presence);
      return { activeUsers: newActiveUsers };
    });
  },

  // Handle user left
  handleUserLeft: (username: string) => {
    set((state) => {
      const newActiveUsers = new Map(state.activeUsers);
      newActiveUsers.delete(username);
      return { activeUsers: newActiveUsers };
    });
  },

  // Handle typing indicator
  handleTypingIndicator: (username: string, isTyping: boolean) => {
    set((state) => {
      const newTypingUsers = new Set(state.typingUsers);
      if (isTyping) {
        newTypingUsers.add(username);
      } else {
        newTypingUsers.delete(username);
      }
      return { typingUsers: newTypingUsers };
    });
  },

  // Handle activity broadcast
  handleActivityBroadcast: (activity: APIActivity) => {
    set((state) => {
      const newActivity: Activity = {
        id: activity.id,
        type: activity.activity_type,
        user: { name: activity.user_id },
        action: activity.activity_type,
        timestamp: new Date(activity.created_at),
      };
      return {
        activities: [newActivity, ...state.activities],
        lastSyncTime: new Date(),
      };
    });
  },

  // Update presence
  updatePresence: (users: UserPresence[]) => {
    set(() => {
      const newActiveUsers = new Map<string, UserPresence>();
      users.forEach((user) => {
        newActiveUsers.set(user.username, user);
      });
      return { activeUsers: newActiveUsers };
    });
  },

  // Load more activities
  loadMoreActivities: async (projectId: string) => {
    const state = get();
    const { limit, offset } = state.activitiesPagination;
    if (state.activitiesPagination.hasMore) {
      await state.fetchActivities(projectId, limit, offset + limit);
    }
  },
}));
