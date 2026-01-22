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
  ): Promise<{
    message: ChatMessage;
    conflicts_pending?: boolean;
    conflicts?: any[];
    extracted_specs?: {
      goals?: string[];
      requirements?: string[];
      tech_stack?: string[];
      constraints?: string[];
    };
    extracted_specs_count?: number;
    mode?: string;
  }> {
    return apiClient.post<{
      message: ChatMessage;
      conflicts_pending?: boolean;
      conflicts?: any[];
      extracted_specs?: {
        goals?: string[];
        requirements?: string[];
        tech_stack?: string[];
        constraints?: string[];
      };
      extracted_specs_count?: number;
      mode?: string;
    }>(
      `/projects/${projectId}/chat/message`,
      request
    );
  },

  /**
   * Save extracted specs from direct dialogue
   */
  async saveExtractedSpecs(
    projectId: string,
    specs: {
      goals?: string[];
      requirements?: string[];
      tech_stack?: string[];
      constraints?: string[];
    }
  ): Promise<{ specs_saved: Record<string, string[]>; project_state: any }> {
    return apiClient.post<{ specs_saved: Record<string, string[]>; project_state: any }>(
      `/projects/${projectId}/chat/save-extracted-specs`,
      specs
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

  /**
   * Mark current question as skipped
   */
  async skipQuestion(projectId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.post<{ success: boolean; message: string }>(
      `/projects/${projectId}/chat/skip`,
      {}
    );
  },

  /**
   * Resolve detected conflicts in project specifications
   */
  async resolveConflict(
    projectId: string,
    resolutions: Array<{
      conflict_type: string;
      old_value: string;
      new_value: string;
      resolution: 'keep' | 'replace' | 'skip' | 'manual';
      manual_value?: string;
    }>
  ): Promise<any> {
    return apiClient.post(
      `/projects/${projectId}/chat/resolve-conflicts`,
      { conflicts: resolutions }
    );
  },

  /**
   * Interpret natural language input and get command suggestions
   */
  async interpretNLU(projectId: string, input: string): Promise<any> {
    return apiClient.post('/nlu/interpret', {
      input,
      context: {
        project_id: projectId,
      },
    });
  },

  /**
   * Get all available commands for NLU
   */
  async getAvailableCommands(): Promise<{ commands: any[]; categories: string[] }> {
    return apiClient.get<{ commands: any[]; categories: string[] }>('/nlu/commands');
  },

  /**
   * Get context-aware command suggestions
   */
  async getCommandSuggestions(projectId: string, phase?: string): Promise<{ suggestions: any[] }> {
    return apiClient.get<{ suggestions: any[] }>('/nlu/suggestions', {
      params: { project_id: projectId, phase },
    });
  },

};
