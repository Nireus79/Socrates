/**
 * Knowledge Base API client
 *
 * Provides centralized methods for knowledge base operations:
 * - Document import (file, URL, text)
 * - Document search and management
 * - Knowledge entries
 */

import { apiClient } from './client';

// Type definitions for Knowledge Base API

export interface DocumentMetadata {
  id: string;
  title: string;
  source_type: 'file' | 'url' | 'text';
  created_at: string;
  size?: number;
  chunk_count: number;
}

export interface SearchResult {
  document_id: string;
  title: string;
  excerpt: string;
  relevance_score: number;
  source: string;
}

export interface KnowledgeSearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

export interface DocumentListResponse {
  documents: DocumentMetadata[];
  total: number;
}

export interface ImportFileRequest {
  projectId?: string;
}

export interface ImportURLRequest {
  url: string;
  projectId?: string;
}

export interface ImportTextRequest {
  title: string;
  content: string;
  projectId?: string;
}

export interface ImportResponse {
  filename?: string;
  url?: string;
  title?: string;
  size?: number;
  word_count?: number;
  chunks: number;
  entries: number;
}

export interface KnowledgeEntryRequest {
  content: string;
  category: string;
  projectId?: string;
}

export interface KnowledgeEntryResponse {
  category: string;
  content_length: number;
}

export interface ExportResponse {
  project_id: string;
  entries: number;
  export_format: string;
}

/**
 * Knowledge Base API client
 */
export const knowledgeAPI = {
  /**
   * List all documents in knowledge base
   */
  async listDocuments(projectId?: string): Promise<DocumentListResponse> {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    return apiClient.get<DocumentListResponse>(
      `/knowledge/documents${params.toString() ? `?${params.toString()}` : ''}`
    );
  },

  /**
   * Import file to knowledge base
   */
  async importFile(file: File, projectId?: string): Promise<ImportResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (projectId) formData.append('project_id', projectId);

    return apiClient.post<ImportResponse>('/knowledge/import/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  /**
   * Import content from URL
   */
  async importURL(url: string, projectId?: string): Promise<ImportResponse> {
    const body: ImportURLRequest = {
      url,
      projectId,
    };

    return apiClient.post<ImportResponse>('/knowledge/import/url', body);
  },

  /**
   * Import pasted text
   */
  async importText(
    title: string,
    content: string,
    projectId?: string
  ): Promise<ImportResponse> {
    const body: ImportTextRequest = {
      title,
      content,
      projectId,
    };

    return apiClient.post<ImportResponse>('/knowledge/import/text', body);
  },

  /**
   * Search knowledge base
   */
  async searchKnowledge(
    query: string,
    projectId?: string,
    topK: number = 10
  ): Promise<KnowledgeSearchResponse> {
    const params = new URLSearchParams();
    params.append('query', query);
    if (projectId) params.append('project_id', projectId);
    params.append('top_k', topK.toString());

    return apiClient.get<KnowledgeSearchResponse>(
      `/knowledge/search?${params.toString()}`
    );
  },

  /**
   * Delete document from knowledge base
   */
  async deleteDocument(documentId: string): Promise<{ document_id: string }> {
    return apiClient.delete<{ document_id: string }>(
      `/knowledge/documents/${documentId}`
    );
  },

  /**
   * Add knowledge entry
   */
  async addKnowledgeEntry(
    content: string,
    category: string,
    projectId?: string
  ): Promise<KnowledgeEntryResponse> {
    const body: KnowledgeEntryRequest = {
      content,
      category,
      projectId,
    };

    return apiClient.post<KnowledgeEntryResponse>('/knowledge/entries', body);
  },

  /**
   * Export knowledge base for project
   */
  async exportKnowledge(projectId: string): Promise<ExportResponse> {
    return apiClient.get<ExportResponse>(`/knowledge/export/${projectId}`);
  },
};
