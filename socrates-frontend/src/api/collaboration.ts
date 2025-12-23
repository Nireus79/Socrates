/**
 * Collaboration API service
 */

import { apiClient } from './client';
import type { Collaborator, ProjectPresence, CollaboratorRole } from '../types/models';

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
   * Get project activities
   */
  async getActivities(projectId: string): Promise<{ activities: any[] }> {
    return apiClient.get<{ activities: any[] }>(
      `/projects/${projectId}/activities`
    );
  },

  /**
   * Record user activity in a project
   */
  async recordActivity(
    projectId: string,
    activityType: string,
    data?: Record<string, any>
  ): Promise<{ activity_id: string }> {
    return apiClient.post<{ activity_id: string }>(
      `/projects/${projectId}/activity`,
      { activity_type: activityType, data },
      {
        params: { activity_type: activityType },
      }
    );
  },
};
