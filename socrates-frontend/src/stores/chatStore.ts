/**
 * Chat Store - Chat messaging (REST API only)
 */

import { create } from 'zustand';
import type { ChatMessage, ChatMode } from '../types/models';
import { chatAPI } from '../api';

const logger = {
  info: (msg: string) => console.log('[ChatStore]', msg),
  warn: (msg: string) => console.warn('[ChatStore]', msg),
  error: (msg: string) => console.error('[ChatStore]', msg),
};

interface Conflict {
  conflict_id: string;
  conflict_type: string;
  old_value: string;
  new_value: string;
  old_author: string;
  new_author: string;
  old_timestamp: string;
  new_timestamp: string;
  severity: string;
  suggestions: string[];
}

interface ChatState {
  // State
  messages: ChatMessage[];
  searchResults: ChatMessage[];
  isLoading: boolean;
  isSearching: boolean;
  error: string | null;
  mode: ChatMode;
  currentProjectId: string | null;
  conflicts: Conflict[] | null;
  pendingConflicts: boolean;

  // Actions
  getQuestion: (projectId: string) => Promise<string>;
  sendMessage: (content: string) => Promise<void>;
  addMessage: (message: ChatMessage) => void;
  addSystemMessage: (content: string) => void;
  switchMode: (projectId: string, mode: ChatMode) => Promise<void>;
  requestHint: (projectId: string) => Promise<string>;
  clearHistory: (projectId: string) => Promise<void>;
  loadHistory: (projectId: string) => Promise<void>;
  getSummary: (projectId: string) => Promise<{ summary: string; key_points: string[] }>;
  searchConversations: (projectId: string, query: string) => Promise<void>;
  resolveConflict: (projectId: string, resolution: any) => Promise<void>;
  clearConflicts: () => void;
  clearSearch: () => void;
  clearError: () => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  messages: [],
  searchResults: [],
  isLoading: false,
  isSearching: false,
  error: null,
  mode: 'socratic',
  currentProjectId: null,
  conflicts: null,
  pendingConflicts: false,

  // Get next question
  getQuestion: async (projectId: string) => {
    set({ isLoading: true, error: null, currentProjectId: projectId });
    try {
      const response = await chatAPI.getQuestion(projectId);

      // Add question as assistant message
      get().addMessage({
        id: `q_${Date.now()}`,
        role: 'assistant',
        content: response.question,
        timestamp: new Date().toISOString(),
      });

      set({ isLoading: false });
      return response.question;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to get question',
        isLoading: false,
      });
      throw error;
    }
  },

  // Send message
  sendMessage: async (content: string) => {
    const state = get();
    if (!state.currentProjectId) {
      set({ error: 'No project selected' });
      return;
    }

    // Add user message optimistically
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    get().addMessage(userMessage);

    set({ isLoading: true, error: null });
    try {
      const response = await chatAPI.sendMessage(state.currentProjectId, {
        message: content,
        mode: state.mode,
      });

      // Add assistant message only if one was returned (null when debug off and no insights)
      if (response.message) {
        get().addMessage({
          id: response.message.id,
          role: 'assistant',
          content: response.message.content,
          timestamp: response.message.timestamp,
        });
      }

      // If conflicts were detected, store them and notify user
      if (response.conflicts_pending && response.conflicts) {
        logger.warn(`Conflicts detected: ${response.conflicts.length} conflict(s)`);
        set({
          conflicts: response.conflicts,
          pendingConflicts: true,
          isLoading: false,
        });
        get().addSystemMessage('Conflicts detected in your response. Please resolve them to proceed.');
        return;
      }

      // Get the next question after response is processed (in Socratic mode)
      if (state.mode === 'socratic') {
        try {
          logger.info('Response processed. Generating next question...');
          await get().getQuestion(state.currentProjectId);
        } catch (error) {
          logger.warn(`Failed to get next question: ${error}`);
          // Don't fail the entire response if question generation fails
        }
      }

      set({ isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to send message',
        isLoading: false,
      });
      throw error;
    }
  },

  // Add message
  addMessage: (message: ChatMessage) => {
    set((state) => ({
      messages: [...state.messages, message],
    }));
  },

  // Add system message
  addSystemMessage: (content: string) => {
    const message: ChatMessage = {
      id: `sys_${Date.now()}`,
      role: 'system',
      content,
      timestamp: new Date().toISOString(),
    };
    get().addMessage(message);
  },

  // Switch mode
  switchMode: async (projectId: string, mode: ChatMode) => {
    set({ isLoading: true, error: null });
    try {
      await chatAPI.switchMode(projectId, mode);
      set({ mode, isLoading: false, conflicts: null, pendingConflicts: false });
      get().addSystemMessage(`Switched to ${mode} mode`);
      // Refresh conversation history to ensure UI stays in sync with backend
      try {
        await get().loadHistory(projectId);
      } catch (historyError) {
        logger.warn(`Failed to refresh history after mode switch: ${historyError}`);
      }
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to switch mode',
        isLoading: false,
      });
      throw error;
    }
  },

  // Request hint
  requestHint: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await chatAPI.getHint(projectId);
      set({ isLoading: false });
      get().addSystemMessage(`Hint: ${response.hint}`);
      return response.hint;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to get hint',
        isLoading: false,
      });
      throw error;
    }
  },

  // Clear history
  clearHistory: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      await chatAPI.clearHistory(projectId);
      set({ messages: [], isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to clear history',
        isLoading: false,
      });
      throw error;
    }
  },

  // Load history
  loadHistory: async (projectId: string) => {
    set({ isLoading: true, error: null, currentProjectId: projectId });
    try {
      const history = await chatAPI.getHistory(projectId);
      // Set messages from API (API returns complete history)
      set({ messages: history.messages, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load history',
        isLoading: false,
      });
      throw error;
    }
  },

  // Get summary
  getSummary: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await chatAPI.getSummary(projectId);
      set({ isLoading: false });
      return {
        summary: response.summary,
        key_points: response.key_points,
      };
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to get summary',
        isLoading: false,
      });
      throw error;
    }
  },

  // Search conversations
  searchConversations: async (projectId: string, query: string) => {
    set({ isSearching: true, error: null });
    try {
      const response = await chatAPI.searchConversations(projectId, query);
      set({ searchResults: response.results, isSearching: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to search conversations',
        isSearching: false,
      });
      throw error;
    }
  },

  // Resolve conflict
  resolveConflict: async (projectId: string, resolution: any) => {
    const state = get();
    if (!state.currentProjectId) {
      set({ error: 'No project selected' });
      return;
    }

    set({ isLoading: true, error: null });
    try {
      // Call conflict resolution API endpoint
      if (chatAPI.resolveConflict) {
        await chatAPI.resolveConflict(projectId, resolution);
      }

      set({ conflicts: null, pendingConflicts: false, isLoading: false });
      get().addSystemMessage('Conflict resolved. Continuing...');

      // Get next question to continue flow
      try {
        await get().getQuestion(projectId);
      } catch (questionError) {
        logger.warn(`Failed to get next question: ${questionError}`);
      }
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to resolve conflict',
        isLoading: false,
      });
      throw error;
    }
  },

  // Clear conflicts
  clearConflicts: () => set({ conflicts: null, pendingConflicts: false }),

  // Clear search results
  clearSearch: () => set({ searchResults: [] }),

  // Clear error
  clearError: () => set({ error: null }),

  // Reset state
  reset: () => {
    set({
      messages: [],
      searchResults: [],
      isLoading: false,
      isSearching: false,
      error: null,
      mode: 'socratic',
      currentProjectId: null,
      conflicts: null,
      pendingConflicts: false,
    });
  },

  // Get answer suggestions for current question
  getSuggestions: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await chatAPI.getSuggestions(projectId);
      set({ isLoading: false });
      return response.suggestions;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to get suggestions',
        isLoading: false,
      });
      throw error;
    }
  },

  // Get all questions for a project
  getQuestions: async (projectId: string, statusFilter?: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await chatAPI.getQuestions(projectId, statusFilter);
      set({ isLoading: false });
      return response.questions;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to get questions',
        isLoading: false,
      });
      throw error;
    }
  },

  // Reopen a skipped question
  reopenQuestion: async (projectId: string, questionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await chatAPI.reopenQuestion(projectId, questionId);
      set({ isLoading: false });
      return response;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to reopen question',
        isLoading: false,
      });
      throw error;
    }
  },
}));
