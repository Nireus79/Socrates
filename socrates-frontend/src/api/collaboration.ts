/**
 * Collaboration API service
 */

import { apiClient } from './client';
import type {
  Collaborator,
  ProjectPresence,
  CollaboratorRole,
  Invitation,
  InvitationResponse,
  InvitationsListResponse,
  Activity,
  ActivitiesResponse,
  PresenceResponse,
} from '../types/models';

export const collaborationAPI = {
  /**
   * Add a collaborator to a project
   */
  async addCollaborator(
    projectId: string,
    username: string,
    role: CollaboratorRole = 'editor'
  ): Promise<{ collaborator: Collaborator }> {
    return apiClient.post<{ collaborator: Collaborator }>(
      `/projects/${projectId}/collaborators`,
      {},
      {
        params: { username, role },
      }
    );
  },

  /**
   * List all collaborators for a project
   */
  async listCollaborators(
    projectId: string
  ): Promise<{ collaborators: Collaborator[]; total: number }> {
    return apiClient.get<{ collaborators: Collaborator[]; total: number }>(
      `/projects/${projectId}/collaborators`
    );
  },

  /**
   * Update a collaborator's role
   */
  async updateCollaboratorRole(
    projectId: string,
    username: string,
    role: CollaboratorRole
  ): Promise<{ collaborator: Collaborator }> {
    return apiClient.put<{ collaborator: Collaborator }>(
      `/projects/${projectId}/collaborators/${username}/role`,
      {},
      { params: { role } }
    );
  },

  /**
   * Remove a collaborator from a project
   */
  async removeCollaborator(projectId: string, username: string): Promise<{ success: boolean }> {
    return apiClient.delete<{ success: boolean }>(
      `/projects/${projectId}/collaborators/${username}`
    );
  },

  /**
   * Get active collaborators (presence)
   */
  async getPresence(projectId: string): Promise<{ active_collaborators: ProjectPresence[] }> {
    return apiClient.get<{ active_collaborators: ProjectPresence[] }>(
      `/projects/${projectId}/presence`
    );
  },

  /**
   * Get project activities with pagination
   */
  async getActivities(
    projectId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<ActivitiesResponse> {
    return apiClient.get<ActivitiesResponse>(
      `/projects/${projectId}/activities`,
      {
        params: { limit, offset },
      }
    );
  },

  /**
   * Record user activity in a project
   */
  async recordActivity(
    projectId: string,
    activityType: string,
    data?: Record<string, any>
  ): Promise<{ activity_id: string; activity: Activity }> {
    return apiClient.post<{ activity_id: string; activity: Activity }>(
      `/projects/${projectId}/activities`,
      { activity_type: activityType, activity_data: data }
    );
  },

  /**
   * Create an invitation for a collaborator
   */
  async createInvitation(
    projectId: string,
    email: string,
    role: CollaboratorRole = 'editor'
  ): Promise<InvitationResponse> {
    return apiClient.post<InvitationResponse>(
      `/projects/${projectId}/invitations`,
      { email, role }
    );
  },

  /**
   * List invitations for a project
   */
  async listInvitations(
    projectId: string,
    statusFilter?: string
  ): Promise<InvitationsListResponse> {
    return apiClient.get<InvitationsListResponse>(
      `/projects/${projectId}/invitations`,
      {
        params: statusFilter ? { status: statusFilter } : {},
      }
    );
  },

  /**
   * Accept an invitation using the token
   */
  async acceptInvitation(token: string): Promise<{ status: string; message?: string }> {
    return apiClient.post<{ status: string; message?: string }>(
      `/projects/invitations/${token}/accept`,
      { email: '' }
    );
  },

  /**
   * Cancel/delete an invitation
   */
  async cancelInvitation(
    projectId: string,
    invitationId: string
  ): Promise<{ status: string }> {
    return apiClient.delete<{ status: string }>(
      `/projects/${projectId}/invitations/${invitationId}`
    );
  },
};
