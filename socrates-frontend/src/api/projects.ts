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
    // Don't send owner - it's derived from JWT token by the API
    return apiClient.post<Project>('/projects', request);
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
   * Delete project
   */
  async deleteProject(projectId: string): Promise<void> {
    return apiClient.delete(`/projects/${projectId}`);
  },

  /**
   * Get project statistics
   */
  async getProjectStats(projectId: string): Promise<ProjectStats> {
    return apiClient.get<ProjectStats>(`/projects/${projectId}/stats`);
  },

  /**
   * Get project maturity analysis
   */
  async getProjectMaturity(projectId: string): Promise<ProjectMaturity> {
    return apiClient.get<ProjectMaturity>(`/projects/${projectId}/maturity`);
  },

  /**
   * Restore archived project
   */
  async restoreProject(projectId: string): Promise<Project> {
    return apiClient.post<Project>(`/projects/${projectId}/restore`, {});
  },

  /**
   * Advance project phase
   */
  async advancePhase(projectId: string, newPhase: ProjectPhase): Promise<Project> {
    return apiClient.put<Project>(`/projects/${projectId}/phase`, { phase: newPhase });
  },

  /**
   * Get project files
   */
  async getProjectFiles(projectId: string): Promise<{ project_id: string; files: any[]; total: number }> {
    return apiClient.get(`/projects/${projectId}/files`);
  },

  /**
   * Get file content
   */
  async getFileContent(projectId: string, fileName: string): Promise<{ project_id: string; file_name: string; content: string }> {
    return apiClient.get(`/projects/${projectId}/files/content`, {
      params: { file_name: fileName },
    });
  },

  /**
   * Delete a file from project
   */
  async deleteFile(projectId: string, fileName: string): Promise<{ project_id: string; file_name: string }> {
    return apiClient.delete(`/projects/${projectId}/files`, {
      params: { file_name: fileName },
    });
  },
};
