/**
 * Chat API service
 */

import { apiClient } from './client';
import type {
  ConversationHistory,
  ChatMessage,
} from '../types/models';
import type {
  SendChatMessageRequest,
  ChatHistoryQuery,
} from '../types/api';

export const chatAPI = {
  /**
   * Get next Socratic question
   */
  async getQuestion(projectId: string): Promise<{ question: string; phase: string }> {
    return apiClient.get<{ question: string; phase: string }>(
      `/projects/${projectId}/chat/question`
    );
  },

  /**
   * Send a chat message
   */
  async sendMessage(
    projectId: string,
    request: SendChatMessageRequest
  ): Promise<{ message: ChatMessage; conflicts_pending?: boolean; conflicts?: any[] }> {
    return apiClient.post<{ message: ChatMessage; conflicts_pending?: boolean; conflicts?: any[] }>(
      `/projects/${projectId}/chat/message`,
      request
    );
  },

  /**
   * Get chat history
   */
  async getHistory(
    projectId: string,
    query?: ChatHistoryQuery
  ): Promise<ConversationHistory> {
    return apiClient.get<ConversationHistory>(`/projects/${projectId}/chat/history`, {
      params: query,
    });
  },

  /**
   * Switch chat mode
   */
  async switchMode(
    projectId: string,
    mode: 'socratic' | 'direct'
  ): Promise<{ mode: string }> {
    return apiClient.put<{ mode: string }>(`/projects/${projectId}/chat/mode`, {
      mode,
    });
  },

  /**
   * Request a hint
   */
  async getHint(projectId: string): Promise<{ hint: string }> {
    return apiClient.get<{ hint: string }>(`/projects/${projectId}/chat/hint`);
  },

  /**
   * Clear conversation history
   */
  async clearHistory(projectId: string): Promise<{ success: boolean }> {
    return apiClient.delete<{ success: boolean }>(`/projects/${projectId}/chat/clear`);
  },

  /**
   * Get conversation summary
   */
  async getSummary(
    projectId: string
  ): Promise<{ summary: string; key_points: string[]; insights: string[] }> {
    return apiClient.get<{ summary: string; key_points: string[]; insights: string[] }>(
      `/projects/${projectId}/chat/summary`
    );
  },

  /**
   * Search conversations
   */
  async searchConversations(
    projectId: string,
    query: string
  ): Promise<{ results: ChatMessage[] }> {
    return apiClient.post<{ results: ChatMessage[] }>(
      `/projects/${projectId}/chat/search`,
      { query }
    );
  },

  /**
   * Finish chat session for project
   */
  async finishSession(projectId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.post<{ success: boolean; message: string }>(
      `/projects/${projectId}/chat/done`,
      {}
    );
  },

  /**
   * Get answer suggestions for current question
   */
  async getSuggestions(projectId: string): Promise<{ suggestions: string[]; question: string; phase: string }> {
    return apiClient.get<{ suggestions: string[]; question: string; phase: string }>(
      `/projects/${projectId}/chat/suggestions`
    );
  },

  /**
   * Get all questions for a project, optionally filtered by status
   */
  async getQuestions(
    projectId: string,
    statusFilter?: string
  ): Promise<{ questions: any[]; total: number; filtered_by: string }> {
    return apiClient.get<{ questions: any[]; total: number; filtered_by: string }>(
      `/projects/${projectId}/chat/questions`,
      { params: statusFilter ? { status_filter: statusFilter } : undefined }
    );
  },

  /**
   * Reopen a skipped question so user can answer it
   */
  async reopenQuestion(projectId: string, questionId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.post<{ success: boolean; message: string }>(
      `/projects/${projectId}/chat/questions/${questionId}/reopen`,
      {}
    );
  },

};
