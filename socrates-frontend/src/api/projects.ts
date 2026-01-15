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

  /**
   * Export project as archive (ZIP, TAR, TAR.GZ, etc.)
   */
  async exportProject(projectId: string, format: 'zip' | 'tar' | 'tar.gz' | 'tar.bz2' = 'zip'): Promise<Blob> {
    const response = await fetch(`/api/projects/${projectId}/export?format=${format}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to export project: ${response.statusText}`);
    }

    return response.blob();
  },

  /**
   * Publish project to GitHub
   */
  async publishToGitHub(
    projectId: string,
    repoName: string,
    description: string,
    isPrivate: boolean,
    githubToken: string,
  ): Promise<{
    success: boolean;
    status: string;
    message: string;
    data: {
      repo_url: string;
      clone_url: string;
      repo_name: string;
      private: boolean;
      github_user: string;
      project_id: string;
      git_status: any;
    };
  }> {
    return apiClient.post<any>(`/projects/${projectId}/publish-to-github`, {
      repo_name: repoName,
      description,
      private: isPrivate,
      github_token: githubToken,
    });
  },
};

/**
 * Export project wrapper function
 */
export const exportProject = async (
  projectId: string,
  format: 'zip' | 'tar' | 'tar.gz' | 'tar.bz2' = 'zip'
): Promise<Blob> => {
  return projectsAPI.exportProject(projectId, format);
};

/**
 * Publish to GitHub wrapper function
 */
export const publishToGitHub = async (
  projectId: string,
  repoName: string,
  description: string,
  isPrivate: boolean,
  githubToken: string,
) => {
  return projectsAPI.publishToGitHub(projectId, repoName, description, isPrivate, githubToken);
};
