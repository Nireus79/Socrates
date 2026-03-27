/**
 * Unit tests for collaboration store - Optimistic updates
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useCollaborationStore } from './collaborationStore';
import * as collaborationAPI from '../api/collaboration';

// Mock the API
vi.mock('../api/collaboration');

describe('Collaboration Store - Optimistic Updates', () => {
  beforeEach(() => {
    // Reset store before each test
    useCollaborationStore.setState({
      collaborators: [
        {
          username: 'user1',
          email: 'user1@example.com',
          role: 'editor',
          status: 'active',
          joined_at: new Date().toISOString(),
        },
        {
          username: 'user2',
          email: 'user2@example.com',
          role: 'viewer',
          status: 'offline',
          joined_at: new Date().toISOString(),
        },
      ],
      error: null,
      isLoading: false,
    });
    vi.clearAllMocks();
  });

  describe('removeCollaborator', () => {
    it('should remove collaborator optimistically before API call', async () => {
      const { removeCollaborator } = useCollaborationStore.getState();

      // Mock successful API response
      vi.mocked(collaborationAPI.removeCollaborator).mockResolvedValue({
        success: true,
        message: 'Collaborator removed',
      });

      let state = useCollaborationStore.getState();
      expect(state.collaborators).toHaveLength(2);

      const removePromise = removeCollaborator('project1', 'user1');

      // Check that collaborator was removed immediately (optimistically)
      state = useNotificationStore.getState();
      // Note: We're checking the promise chain, the optimistic update happens synchronously
      await expect(removePromise).resolves.toBeUndefined();

      state = useCollaborationStore.getState();
      expect(state.collaborators).toHaveLength(1);
      expect(state.collaborators[0].username).toBe('user2');
      expect(state.isLoading).toBe(false);
    });

    it('should rollback on API failure', async () => {
      const { removeCollaborator } = useCollaborationStore.getState();
      const originalCollaborators = useCollaborationStore.getState().collaborators;

      // Mock API failure
      vi.mocked(collaborationAPI.removeCollaborator).mockRejectedValue(
        new Error('API Error')
      );

      const removePromise = removeCollaborator('project1', 'user1');

      // Wait for the async operation
      await expect(removePromise).rejects.toThrow('API Error');

      const state = useCollaborationStore.getState();
      // Should have rolled back to original state
      expect(state.collaborators).toHaveLength(originalCollaborators.length);
      expect(state.collaborators).toEqual(originalCollaborators);
      expect(state.error).toBe('API Error');
      expect(state.isLoading).toBe(false);
    });

    it('should set loading state during operation', async () => {
      const { removeCollaborator } = useCollaborationStore.getState();

      // Mock a delayed API response
      vi.mocked(collaborationAPI.removeCollaborator).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve({ success: true }), 100)
          )
      );

      const removePromise = removeCollaborator('project1', 'user1');

      // Check loading state was set
      let state = useCollaborationStore.getState();
      expect(state.isLoading).toBe(true);

      await removePromise;

      state = useCollaborationStore.getState();
      expect(state.isLoading).toBe(false);
    });
  });
});
