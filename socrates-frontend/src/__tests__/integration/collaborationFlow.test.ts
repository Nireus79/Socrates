/**
 * Integration tests for full collaboration workflows
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useCollaborationStore } from '../../stores/collaborationStore';
import { useNotificationStore } from '../../stores/notificationStore';
import * as collaborationAPI from '../../api/collaboration';

// Mock the API
vi.mock('../../api/collaboration');

describe('Collaboration Workflow Integration Tests', () => {
  beforeEach(() => {
    // Reset stores
    useCollaborationStore.setState({
      collaborators: [
        {
          username: 'owner',
          email: 'owner@example.com',
          role: 'owner',
          status: 'active',
          joined_at: new Date().toISOString(),
        },
      ],
      invitations: [],
      error: null,
      isLoading: false,
      isLoadingInvitations: false,
    });

    useNotificationStore.setState({ notifications: [] });

    vi.clearAllMocks();
  });

  describe('Add Collaborator Flow', () => {
    it('should handle complete add collaborator flow with success', async () => {
      const mockCollaborator = {
        username: 'newuser',
        email: 'newuser@example.com',
        role: 'editor' as const,
        status: 'active',
        joined_at: new Date().toISOString(),
      };

      vi.mocked(collaborationAPI.addCollaborator).mockResolvedValue({
        success: true,
        collaborator: mockCollaborator,
      });

      let state = useCollaborationStore.getState();
      expect(state.collaborators).toHaveLength(1);

      // Perform the add collaborator action
      const { addCollaborator } = useCollaborationStore.getState();
      await addCollaborator('project-123', 'newuser', 'editor');

      // Verify collaborator was added
      state = useCollaborationStore.getState();
      expect(state.collaborators).toHaveLength(2);
      expect(state.collaborators[1].username).toBe('newuser');
      expect(state.error).toBeNull();
      expect(state.isLoading).toBe(false);

      // Verify API was called correctly
      expect(collaborationAPI.addCollaborator).toHaveBeenCalledWith(
        'project-123',
        'newuser',
        'editor'
      );
    });

    it('should handle add collaborator with error gracefully', async () => {
      const errorMessage = 'User not found';
      vi.mocked(collaborationAPI.addCollaborator).mockRejectedValue(
        new Error(errorMessage)
      );

      const { addCollaborator } = useCollaborationStore.getState();

      try {
        await addCollaborator('project-123', 'nonexistent', 'editor');
      } catch (error) {
        // Expected to throw
      }

      const state = useCollaborationStore.getState();
      expect(state.collaborators).toHaveLength(1); // Should not have added
      expect(state.error).toBe(errorMessage);
    });
  });

  describe('Remove Collaborator Flow (Optimistic)', () => {
    beforeEach(() => {
      // Add more collaborators for removal test
      useCollaborationStore.setState({
        collaborators: [
          {
            username: 'owner',
            email: 'owner@example.com',
            role: 'owner',
            status: 'active',
            joined_at: new Date().toISOString(),
          },
          {
            username: 'editor1',
            email: 'editor1@example.com',
            role: 'editor',
            status: 'active',
            joined_at: new Date().toISOString(),
          },
          {
            username: 'viewer1',
            email: 'viewer1@example.com',
            role: 'viewer',
            status: 'offline',
            joined_at: new Date().toISOString(),
          },
        ],
      });
    });

    it('should remove collaborator optimistically then confirm', async () => {
      vi.mocked(collaborationAPI.removeCollaborator).mockResolvedValue({
        success: true,
      });

      let state = useCollaborationStore.getState();
      expect(state.collaborators).toHaveLength(3);

      const { removeCollaborator } = useCollaborationStore.getState();

      // Initiate removal
      const removePromise = removeCollaborator('project-123', 'editor1');

      // Immediately after, should show optimistic removal
      state = useCollaborationStore.getState();
      expect(state.collaborators).toHaveLength(2);
      expect(
        state.collaborators.find((c) => c.username === 'editor1')
      ).toBeUndefined();

      await removePromise;

      // After promise resolves, state should remain the same
      state = useCollaborationStore.getState();
      expect(state.collaborators).toHaveLength(2);
      expect(state.isLoading).toBe(false);
    });

    it('should restore collaborator if removal fails', async () => {
      const errorMessage = 'Cannot remove project owner';
      vi.mocked(collaborationAPI.removeCollaborator).mockRejectedValue(
        new Error(errorMessage)
      );

      const originalState = useCollaborationStore.getState().collaborators;

      const { removeCollaborator } = useCollaborationStore.getState();

      try {
        await removeCollaborator('project-123', 'editor1');
      } catch (error) {
        // Expected to throw
      }

      const state = useCollaborationStore.getState();
      // Should be restored to original state
      expect(state.collaborators).toHaveLength(originalState.length);
      expect(state.error).toBe(errorMessage);
    });
  });

  describe('Invitation Management Flow', () => {
    it('should load invitations', async () => {
      const mockInvitations = [
        {
          id: 'inv-1',
          email: 'user1@example.com',
          role: 'editor' as const,
          status: 'pending' as const,
          created_at: new Date().toISOString(),
          expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 'inv-2',
          email: 'user2@example.com',
          role: 'viewer' as const,
          status: 'accepted' as const,
          created_at: new Date().toISOString(),
          expires_at: null,
        },
      ];

      vi.mocked(collaborationAPI.listInvitations).mockResolvedValue({
        invitations: mockInvitations,
        total: 2,
      });

      const { loadInvitations } = useCollaborationStore.getState();
      await loadInvitations('project-123');

      const state = useCollaborationStore.getState();
      expect(state.invitations).toHaveLength(2);
      expect(state.invitations[0].status).toBe('pending');
      expect(state.invitations[1].status).toBe('accepted');
    });

    it('should create invitation', async () => {
      const mockInvitation = {
        id: 'inv-3',
        email: 'newuser@example.com',
        role: 'editor' as const,
        status: 'pending' as const,
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      };

      vi.mocked(collaborationAPI.createInvitation).mockResolvedValue({
        success: true,
        invitation: mockInvitation,
      });

      const { createInvitation } = useCollaborationStore.getState();
      await createInvitation('project-123', 'newuser@example.com', 'editor');

      expect(collaborationAPI.createInvitation).toHaveBeenCalledWith(
        'project-123',
        'newuser@example.com',
        'editor'
      );
    });

    it('should cancel invitation', async () => {
      useCollaborationStore.setState({
        invitations: [
          {
            id: 'inv-1',
            email: 'user@example.com',
            role: 'editor' as const,
            status: 'pending' as const,
            created_at: new Date().toISOString(),
            expires_at: new Date().toISOString(),
          },
        ],
      });

      vi.mocked(collaborationAPI.cancelInvitation).mockResolvedValue({
        success: true,
      });

      const { cancelInvitation } = useCollaborationStore.getState();
      await cancelInvitation('project-123', 'inv-1');

      expect(collaborationAPI.cancelInvitation).toHaveBeenCalledWith(
        'project-123',
        'inv-1'
      );
    });
  });

  describe('Update Role Flow', () => {
    beforeEach(() => {
      useCollaborationStore.setState({
        collaborators: [
          {
            username: 'owner',
            email: 'owner@example.com',
            role: 'owner',
            status: 'active',
            joined_at: new Date().toISOString(),
          },
          {
            username: 'editor1',
            email: 'editor1@example.com',
            role: 'editor',
            status: 'active',
            joined_at: new Date().toISOString(),
          },
        ],
      });
    });

    it('should update collaborator role', async () => {
      const updatedCollaborator = {
        username: 'editor1',
        email: 'editor1@example.com',
        role: 'viewer' as const,
        status: 'active',
        joined_at: new Date().toISOString(),
      };

      vi.mocked(collaborationAPI.updateCollaboratorRole).mockResolvedValue({
        success: true,
        collaborator: updatedCollaborator,
      });

      const { updateCollaboratorRole } = useCollaborationStore.getState();
      await updateCollaboratorRole('project-123', 'editor1', 'viewer');

      const state = useCollaborationStore.getState();
      const updatedUser = state.collaborators.find(
        (c) => c.username === 'editor1'
      );
      expect(updatedUser?.role).toBe('viewer');
    });
  });
});
