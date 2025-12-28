/**
 * Knowledge Base API client
 *
 * Provides centralized methods for knowledge base operations:
 * - Document import (file, URL, text)
 * - Document search and management
 * - Knowledge entries
 * - Bulk operations
 * - Advanced filtering and analytics
 */

import { apiClient } from './client';
import type {
  DocumentDetails,
  DocumentDetailsResponse,
  DocumentAnalyticsResponse,
  BulkDeleteResponse,
  BulkImportResponse,
  DocumentListFilters,
  DocumentListResponse as TypesDocumentListResponse,
} from '../types/models';

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
   * List all documents in knowledge base with filtering, sorting, and pagination
   */
  async listDocuments(filters: DocumentListFilters = {}): Promise<TypesDocumentListResponse> {
    const params = new URLSearchParams();

    if (filters.projectId) params.append('project_id', filters.projectId);
    if (filters.documentType) params.append('document_type', filters.documentType);
    if (filters.searchQuery) params.append('search_query', filters.searchQuery);
    if (filters.sortBy) params.append('sort_by', filters.sortBy);
    if (filters.sortOrder) params.append('sort_order', filters.sortOrder);

    // Handle pagination (defaults)
    const limit = filters.limit || 50;
    const offset = filters.offset || 0;
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    return apiClient.get<TypesDocumentListResponse>(
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

  /**
   * Get detailed information about a document
   */
  async getDocumentDetails(
    documentId: string,
    includeContent: boolean = false
  ): Promise<DocumentDetailsResponse> {
    const params = new URLSearchParams();
    if (includeContent) params.append('include_content', 'true');

    return apiClient.get<DocumentDetailsResponse>(
      `/knowledge/documents/${documentId}${params.toString() ? `?${params.toString()}` : ''}`
    );
  },

  /**
   * Delete multiple documents in bulk
   */
  async bulkDeleteDocuments(documentIds: string[]): Promise<BulkDeleteResponse> {
    return apiClient.post<BulkDeleteResponse>('/knowledge/documents/bulk-delete', {
      document_ids: documentIds,
    });
  },

  /**
   * Import multiple files/documents in bulk
   */
  async bulkImportDocuments(
    files: File[],
    projectId?: string
  ): Promise<BulkImportResponse> {
    const formData = new FormData();

    // Add all files to formData
    files.forEach((file) => {
      formData.append('files', file);
    });

    // Add project_id if provided
    if (projectId) {
      formData.append('project_id', projectId);
    }

    return apiClient.post<BulkImportResponse>('/knowledge/documents/bulk-import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  /**
   * Get analytics for a document
   */
  async getDocumentAnalytics(documentId: string): Promise<DocumentAnalyticsResponse> {
    return apiClient.get<DocumentAnalyticsResponse>(
      `/knowledge/documents/${documentId}/analytics`
    );
  },
};
