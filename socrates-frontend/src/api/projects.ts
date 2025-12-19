/**
 * Projects API service
 */

import { apiClient } from './client';
import type {
  Project,
  ProjectStats,
  ProjectMaturity,
  ProjectPhase,
} from '../types/models';
import type {
  CreateProjectRequest,
  UpdateProjectRequest,
} from '../types/api';

export const projectsAPI = {
  /**
   * Create a new project
   */
  async createProject(request: CreateProjectRequest): Promise<Project> {
    const data = {
      ...request,
      owner: request.owner || localStorage.getItem('username') || 'anonymous',
    };
    return apiClient.post<Project>('/projects', data);
  },

  /**
   * Get all projects for current user
   */
  async listProjects(owner?: string): Promise<{ total: number; projects: Project[] }> {
    const params = owner ? { owner } : undefined;
    return apiClient.get<{ total: number; projects: Project[] }>('/projects', {
      params,
    });
  },

  /**
   * Get project details
   */
  async getProject(projectId: string): Promise<Project> {
    return apiClient.get<Project>(`/projects/${projectId}`);
  },

  /**
   * Update project
   */
  async updateProject(projectId: string, request: UpdateProjectRequest): Promise<Project> {
    return apiClient.put<Project>(`/projects/${projectId}`, request);
  },

  /**
   * Delete (archive) project
   */
  async deleteProject(projectId: string): Promise<{ success: boolean }> {
    return apiClient.delete<{ success: boolean }>(`/projects/${projectId}`);
  },

  /**
   * Restore archived project
   */
  async restoreProject(projectId: string): Promise<Project> {
    return apiClient.post<Project>(`/projects/${projectId}/restore`, {});
  },

  /**
   * Get project statistics
   */
  async getProjectStats(projectId: string): Promise<ProjectStats> {
    return apiClient.get<ProjectStats>(`/projects/${projectId}/stats`);
  },

  /**
   * Get project maturity scores
   */
  async getProjectMaturity(projectId: string): Promise<ProjectMaturity> {
    return apiClient.get<ProjectMaturity>(`/projects/${projectId}/maturity`);
  },

  /**
   * Advance project to next phase
   */
  async advancePhase(projectId: string, newPhase: ProjectPhase): Promise<Project> {
    return apiClient.put<Project>(`/projects/${projectId}/phase`, {}, {
      params: { new_phase: newPhase },
    });
  },

  /**
   * Get project analytics
   */
  async getAnalytics(projectId: string): Promise<any> {
    return apiClient.get<any>(`/projects/${projectId}/analytics`);
  },
};
