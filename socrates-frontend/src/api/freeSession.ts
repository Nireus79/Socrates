/**
 * Free Session API client
 *
 * Provides methods for pre-session (free-form) chat without a project selection.
 * Used for conversational AI before a project is created or selected.
 */

import { apiClient } from './client';

export interface FreeSessionQuestion {
  question: string;
  session_id?: string;
  context?: Record<string, any>;
}

export interface FreeSessionAnswer {
  answer: string;
  has_context: boolean;
  session_id: string;
  suggested_commands?: string[];
  topics_detected?: string[];
}

export const freeSessionAPI = {
  /**
   * Ask a question in free session chat
   */
  async ask(question: string, sessionId?: string): Promise<FreeSessionAnswer> {
    try {
      const response = await apiClient.post<FreeSessionAnswer>('/free_session/ask', {
        question,
        session_id: sessionId,
      });
      return response;
    } catch (error) {
      console.error('Free session ask failed:', error);
      throw error;
    }
  },
};
