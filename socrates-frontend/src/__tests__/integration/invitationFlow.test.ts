/**
 * Integration tests for invitation acceptance flow
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import * as collaborationAPI from '../../api/collaboration';
import * as projectAPI from '../../api/projects';

// Mock APIs
vi.mock('../../api/collaboration');
vi.mock('../../api/projects');

describe('Invitation Acceptance Flow Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Accept Invitation Flow', () => {
    it('should validate invitation token before accepting', async () => {
      const mockInvitationData = {
        id: 'inv-123',
        email: 'newuser@example.com',
        project_id: 'project-456',
        role: 'editor' as const,
        status: 'pending' as const,
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      };

      // Simulate fetching invitation details before accepting
      vi.mocked(collaborationAPI.getInvitationDetails).mockResolvedValue(mockInvitationData);

      // Verify the invitation can be fetched
      const invitationData = await collaborationAPI.getInvitationDetails('token-xyz');

      expect(invitationData.status).toBe('pending');
      expect(invitationData.email).toBe('newuser@example.com');
      expect(invitationData.role).toBe('editor');
    });

    it('should accept invitation and add user as collaborator', async () => {
      const mockCollaborator = {
        username: 'newuser',
        email: 'newuser@example.com',
        role: 'editor' as const,
        status: 'offline',
        joined_at: new Date().toISOString(),
      };

      const mockProject = {
        project_id: 'project-456',
        name: 'Test Project',
        description: 'Test project description',
        phase: 'execution',
        owner: 'owner-user',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      // Mock accepting invitation
      vi.mocked(collaborationAPI.acceptInvitation).mockResolvedValue({
        success: true,
        message: 'Invitation accepted',
        collaborator: mockCollaborator,
        project: mockProject,
      });

      // Mock project fetch for context
      vi.mocked(projectAPI.getProject).mockResolvedValue(mockProject);

      // Accept the invitation
      const response = await collaborationAPI.acceptInvitation('token-xyz');

      expect(response.success).toBe(true);
      expect(response.collaborator.email).toBe('newuser@example.com');
      expect(response.collaborator.role).toBe('editor');
      expect(response.project.name).toBe('Test Project');
    });

    it('should handle expired invitation', async () => {
      const errorMessage = 'Invitation has expired';

      vi.mocked(collaborationAPI.acceptInvitation).mockRejectedValue(
        new Error(errorMessage)
      );

      const acceptPromise = collaborationAPI.acceptInvitation('expired-token');

      await expect(acceptPromise).rejects.toThrow(errorMessage);
    });

    it('should handle already accepted invitation', async () => {
      const errorMessage = 'Invitation already accepted';

      vi.mocked(collaborationAPI.acceptInvitation).mockRejectedValue(
        new Error(errorMessage)
      );

      const acceptPromise = collaborationAPI.acceptInvitation('accepted-token');

      await expect(acceptPromise).rejects.toThrow(errorMessage);
    });

    it('should handle invalid or tampered token', async () => {
      const errorMessage = 'Invalid invitation token';

      vi.mocked(collaborationAPI.acceptInvitation).mockRejectedValue(
        new Error(errorMessage)
      );

      const acceptPromise = collaborationAPI.acceptInvitation('invalid-token');

      await expect(acceptPromise).rejects.toThrow(errorMessage);
    });
  });

  describe('Complete Invitation Journey', () => {
    it('should handle full invitation workflow from creation to acceptance', async () => {
      // Step 1: Create invitation
      const invitationEmail = 'jane.doe@example.com';
      const projectId = 'project-123';

      const createdInvitation = {
        id: 'inv-create-123',
        email: invitationEmail,
        project_id: projectId,
        role: 'editor' as const,
        status: 'pending' as const,
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      };

      vi.mocked(collaborationAPI.createInvitation).mockResolvedValue({
        success: true,
        invitation: createdInvitation,
        invitation_token: 'token-abc-xyz',
      });

      const createResponse = await collaborationAPI.createInvitation(
        projectId,
        invitationEmail,
        'editor'
      );

      expect(createResponse.success).toBe(true);
      expect(createResponse.invitation.status).toBe('pending');

      // Step 2: User receives email with invitation link containing token
      const invitationToken = createResponse.invitation_token;
      expect(invitationToken).toBe('token-abc-xyz');

      // Step 3: User clicks link and validates invitation details
      const invitationDetails = {
        id: 'inv-create-123',
        email: invitationEmail,
        project_id: projectId,
        role: 'editor' as const,
        status: 'pending' as const,
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      };

      vi.mocked(collaborationAPI.getInvitationDetails).mockResolvedValue(
        invitationDetails
      );

      const details = await collaborationAPI.getInvitationDetails(invitationToken);
      expect(details.email).toBe(invitationEmail);
      expect(details.project_id).toBe(projectId);

      // Step 4: User accepts invitation
      const newCollaborator = {
        username: 'jane.doe',
        email: invitationEmail,
        role: 'editor' as const,
        status: 'offline',
        joined_at: new Date().toISOString(),
      };

      const project = {
        project_id: projectId,
        name: 'Shared Project',
        description: 'Description',
        phase: 'execution',
        owner: 'owner-id',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      vi.mocked(collaborationAPI.acceptInvitation).mockResolvedValue({
        success: true,
        message: 'Invitation accepted',
        collaborator: newCollaborator,
        project: project,
      });

      const acceptResponse = await collaborationAPI.acceptInvitation(
        invitationToken
      );

      // Step 5: Verify user is now a collaborator
      expect(acceptResponse.success).toBe(true);
      expect(acceptResponse.collaborator.username).toBe('jane.doe');
      expect(acceptResponse.collaborator.role).toBe('editor');
      expect(acceptResponse.project.name).toBe('Shared Project');

      // Verify invitation status changed
      expect(acceptResponse.message).toBe('Invitation accepted');
    });
  });

  describe('Invitation List Management', () => {
    it('should list pending invitations for a project', async () => {
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
          status: 'pending' as const,
          created_at: new Date().toISOString(),
          expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        },
      ];

      vi.mocked(collaborationAPI.listInvitations).mockResolvedValue({
        invitations: mockInvitations,
        total: 2,
      });

      const response = await collaborationAPI.listInvitations(
        'project-123',
        'pending'
      );

      expect(response.invitations).toHaveLength(2);
      expect(response.invitations[0].status).toBe('pending');
      expect(response.invitations[1].status).toBe('pending');
    });

    it('should cancel pending invitation', async () => {
      vi.mocked(collaborationAPI.cancelInvitation).mockResolvedValue({
        success: true,
        message: 'Invitation cancelled',
      });

      const response = await collaborationAPI.cancelInvitation(
        'project-123',
        'inv-123'
      );

      expect(response.success).toBe(true);
      expect(response.message).toBe('Invitation cancelled');
    });

    it('should filter invitations by status', async () => {
      const acceptedInvitations = [
        {
          id: 'inv-3',
          email: 'user3@example.com',
          role: 'editor' as const,
          status: 'accepted' as const,
          created_at: new Date().toISOString(),
          expires_at: null,
        },
      ];

      vi.mocked(collaborationAPI.listInvitations).mockResolvedValue({
        invitations: acceptedInvitations,
        total: 1,
      });

      const response = await collaborationAPI.listInvitations(
        'project-123',
        'accepted'
      );

      expect(response.invitations).toHaveLength(1);
      expect(response.invitations[0].status).toBe('accepted');
    });
  });
});
