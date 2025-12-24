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
   * Send a chat message
   */
  async sendMessage(
    projectId: string,
    request: SendChatMessageRequest
  ): Promise<{ message: ChatMessage }> {
    return apiClient.post<{ message: ChatMessage }>(
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
   * Get WebSocket connection URL
   */
  getWebSocketURL(projectId: string, token: string): string {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const protocol = baseURL.startsWith('https') ? 'wss' : 'ws';
    const wsBaseURL = baseURL.replace(/^https?/, protocol);
    return `${wsBaseURL}/ws/chat/${projectId}?token=${token}`;
  },
};
