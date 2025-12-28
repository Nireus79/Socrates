/**
 * Search API - Full-text search across projects, conversations, knowledge, and notes
 */

import { apiClient } from './client';

export interface SearchResult {
  id: string;
  type: 'project' | 'conversation' | 'knowledge' | 'note';
  title: string;
  description?: string;
  content?: string;
  projectId?: string;
  createdAt?: string;
  score?: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  searchTime?: number;
}

/**
 * Global search across all content
 */
export async function globalSearch(query: string, limit?: number): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query });
  if (limit) params.append('limit', limit.toString());

  const response = await apiClient.get(`/search?${params}`) as any;
  return response?.data || { results: [], total: 0, query };
}

/**
 * Search conversations
 */
export async function searchConversations(query: string, projectId?: string, limit?: number): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query });
  if (projectId) params.append('project_id', projectId);
  if (limit) params.append('limit', limit.toString());

  const response = await apiClient.post(`/conversations/search?${params}`, {}) as any;
  return response?.data || { results: [], total: 0, query };
}

/**
 * Search knowledge base
 */
export async function searchKnowledge(query: string, projectId?: string, limit?: number): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query });
  if (projectId) params.append('project_id', projectId);
  if (limit) params.append('limit', limit.toString());

  const response = await apiClient.post(`/knowledge/search?${params}`, {}) as any;
  return response?.data || { results: [], total: 0, query };
}

/**
 * Search notes
 */
export async function searchNotes(query: string, projectId?: string, limit?: number): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query });
  if (projectId) params.append('project_id', projectId);
  if (limit) params.append('limit', limit.toString());

  const response = await apiClient.post(`/notes/search?${params}`, {}) as any;
  return response?.data || { results: [], total: 0, query };
}
