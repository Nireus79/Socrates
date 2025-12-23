/**
 * GitHub Integration API service
 * Handles repository import, pull, push, and sync operations
 */

import { apiClient } from './client';

export interface GitHubImportRequest {
  url: string;
  projectName?: string;
  branch?: string;
}

export interface GitHubImportResponse {
  project_id: string;
  project_name: string;
  repository_url: string;
  metadata: Record<string, any>;
  validation_results: Record<string, any>;
}

export interface GitHubSyncStatusResponse {
  project_id: string;
  is_linked: boolean;
  repository_url?: string;
  repository_imported_at?: string;
}

export interface GitHubPullResponse {
  project_id: string;
  message: string;
  diff_summary?: string;
}

export interface GitHubPushResponse {
  project_id: string;
  commit_message: string;
  message: string;
}

export interface GitHubSyncResponse {
  project_id: string;
  pull: GitHubPullResponse;
  push: GitHubPushResponse;
}

export const githubAPI = {
  /**
   * Import a GitHub repository as a new project
   */
  async importRepository(
    request: GitHubImportRequest
  ): Promise<GitHubImportResponse> {
    const params = new URLSearchParams();
    params.append('url', request.url);
    if (request.projectName) {
      params.append('project_name', request.projectName);
    }
    if (request.branch) {
      params.append('branch', request.branch);
    }

    return apiClient.post<GitHubImportResponse>(
      `/github/import?${params.toString()}`,
      {}
    );
  },

  /**
   * Pull latest changes from GitHub for a project
   */
  async pullChanges(projectId: string): Promise<GitHubPullResponse> {
    return apiClient.post<GitHubPullResponse>(
      `/github/projects/${projectId}/pull`,
      {}
    );
  },

  /**
   * Push local changes to GitHub for a project
   */
  async pushChanges(
    projectId: string,
    commitMessage?: string
  ): Promise<GitHubPushResponse> {
    const params = new URLSearchParams();
    if (commitMessage) {
      params.append('commit_message', commitMessage);
    }

    return apiClient.post<GitHubPushResponse>(
      `/github/projects/${projectId}/push?${params.toString()}`,
      {}
    );
  },

  /**
   * Sync with GitHub (pull then push)
   */
  async syncProject(
    projectId: string,
    commitMessage?: string
  ): Promise<GitHubSyncResponse> {
    const params = new URLSearchParams();
    if (commitMessage) {
      params.append('commit_message', commitMessage);
    }

    return apiClient.post<GitHubSyncResponse>(
      `/github/projects/${projectId}/sync?${params.toString()}`,
      {}
    );
  },

  /**
   * Get GitHub sync status for a project
   */
  async getSyncStatus(projectId: string): Promise<GitHubSyncStatusResponse> {
    return apiClient.get<GitHubSyncStatusResponse>(
      `/github/projects/${projectId}/status`
    );
  },
};
