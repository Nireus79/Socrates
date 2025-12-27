/**
 * GitHub Integration API - Repository import and sync
 */

import { apiClient } from './client';

export interface GitHubImportRequest {
  url: string;
  project_name?: string;
  branch?: string;
}

export interface GitHubSyncStatus {
  project_id: string;
  last_sync?: string;
  status: 'synced' | 'pending' | 'failed';
  changes_count?: number;
  [key: string]: any;
}

/**
 * Import GitHub repository as project
 */
export async function importRepository(request: GitHubImportRequest): Promise<any> {
  const response = await apiClient.post('/github/import', request) as any;
  return response?.data || response;
}

/**
 * Pull changes from GitHub
 */
export async function pullFromGithub(projectId: string): Promise<any> {
  const response = await apiClient.post(`/github/projects/${projectId}/pull`, {}) as any;
  return response?.data || response;
}

/**
 * Push changes to GitHub
 */
export async function pushToGithub(projectId: string, message?: string): Promise<any> {
  const response = await apiClient.post(`/github/projects/${projectId}/push`, {
    message: message || 'Sync from Socrates',
  }) as any;
  return response?.data || response;
}

/**
 * Sync project with GitHub
 */
export async function syncWithGithub(projectId: string): Promise<any> {
  const response = await apiClient.post(`/github/projects/${projectId}/sync`, {}) as any;
  return response?.data || response;
}

/**
 * Get GitHub sync status
 */
export async function getGithubStatus(projectId: string): Promise<GitHubSyncStatus> {
  const response = await apiClient.get(`/github/projects/${projectId}/status`) as any;
  return response?.data || response;
}

/**
 * Disconnect project from GitHub
 */
export async function disconnectGithub(projectId: string): Promise<any> {
  const response = await apiClient.post(`/github/disconnect`, { project_id: projectId }) as any;
  return response?.data || response;
}
