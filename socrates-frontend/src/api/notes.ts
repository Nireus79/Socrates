/**
 * Notes API - Project notes management
 */

import { apiClient } from './client';

export interface Note {
  id: string;
  title: string;
  content: string;
  tags: string[];
  created_at: string;
  created_by: string;
}

export interface NotesResponse {
  notes: Note[];
  total: number;
  returned: number;
  filtered_by_tag?: string;
}

export interface SearchNotesResponse {
  results: Note[];
  total_matches: number;
  query: string;
}

/**
 * Get all notes for a project
 */
export async function getNotes(projectId: string, limit?: number, tag?: string): Promise<NotesResponse> {
  const params = new URLSearchParams();
  if (limit) params.append('limit', limit.toString());
  if (tag) params.append('tag', tag);

  const queryString = params.toString();
  const url = `/projects/${projectId}/notes${queryString ? `?${queryString}` : ''}`;

  const response = await apiClient.get(url) as any;
  return response?.data || { notes: [], total: 0, returned: 0 };
}

/**
 * Create a new note
 */
export async function createNote(projectId: string, title: string, content: string, tags: string[] = []): Promise<Note> {
  const response = await apiClient.post(`/projects/${projectId}/notes`, {
    title,
    content,
    tags,
  }) as any;

  return response?.data?.note || null;
}

/**
 * Search notes
 */
export async function searchNotes(projectId: string, query: string): Promise<SearchNotesResponse> {
  const response = await apiClient.post(`/projects/${projectId}/notes/search`, {
    query,
  }) as any;

  return response?.data || { results: [], total_matches: 0, query };
}

/**
 * Delete a note
 */
export async function deleteNote(projectId: string, noteId: string): Promise<boolean> {
  const response = await apiClient.delete(`/projects/${projectId}/notes/${noteId}`) as any;
  return response?.success || false;
}
