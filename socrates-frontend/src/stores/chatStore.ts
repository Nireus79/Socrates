/**
 * Chat Store - Chat messaging and WebSocket state
 */

import { create } from 'zustand';
import type { ChatMessage, ChatMode, WebSocketResponse } from '../types/models';
import { chatAPI } from '../api';

interface ChatState {
  // State
  messages: ChatMessage[];
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  mode: ChatMode;
  currentProjectId: string | null;

  // Actions
  connectWebSocket: (projectId: string, token: string) => Promise<void>;
  disconnectWebSocket: () => void;
  sendMessage: (content: string) => Promise<void>;
  addMessage: (message: ChatMessage) => void;
  addSystemMessage: (content: string) => void;
  handleWebSocketResponse: (response: WebSocketResponse) => void;
  switchMode: (projectId: string, mode: ChatMode) => Promise<void>;
  requestHint: (projectId: string) => Promise<string>;
  clearHistory: (projectId: string) => Promise<void>;
  loadHistory: (projectId: string) => Promise<void>;
  getSummary: (projectId: string) => Promise<{ summary: string; key_points: string[] }>;
  clearError: () => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  messages: [],
  isConnected: false,
  isLoading: false,
  error: null,
  mode: 'socratic',
  currentProjectId: null,

  // Connect WebSocket
  connectWebSocket: async (projectId: string, token: string) => {
    set({ isLoading: true, error: null, currentProjectId: projectId });
    try {
      // In a real implementation, this would create a WebSocket connection
      // For now, we'll simulate the connection
      const wsURL = chatAPI.getWebSocketURL(projectId, token);
      console.log('WebSocket URL:', wsURL);

      set({
        isConnected: true,
        isLoading: false,
      });

      // Add connection message
      get().addSystemMessage('Connected to chat');
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to connect',
        isLoading: false,
      });
      throw error;
    }
  },

  // Disconnect WebSocket
  disconnectWebSocket: () => {
    set({
      isConnected: false,
      currentProjectId: null,
    });
    get().addSystemMessage('Disconnected from chat');
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

      // Add assistant message
      get().addMessage({
        id: response.message.id,
        role: 'assistant',
        content: response.message.content,
        timestamp: response.message.timestamp,
      });

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

  // Handle WebSocket response
  handleWebSocketResponse: (response: WebSocketResponse) => {
    if (response.type === 'assistant_response' && response.content) {
      get().addMessage({
        id: response.requestId || `ws_${Date.now()}`,
        role: 'assistant',
        content: response.content,
        timestamp: response.timestamp,
      });
    } else if (response.type === 'event') {
      console.log('Event received:', response.eventType, response.data);
    } else if (response.type === 'error') {
      set({ error: response.errorMessage || 'WebSocket error' });
    }
  },

  // Switch mode
  switchMode: async (projectId: string, mode: ChatMode) => {
    set({ isLoading: true, error: null });
    try {
      await chatAPI.switchMode(projectId, mode);
      set({ mode, isLoading: false });
      get().addSystemMessage(`Switched to ${mode} mode`);
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
    set({ isLoading: true, error: null });
    try {
      const history = await chatAPI.getHistory(projectId);
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

  // Clear error
  clearError: () => set({ error: null }),

  // Reset state
  reset: () => {
    set({
      messages: [],
      isConnected: false,
      isLoading: false,
      error: null,
      mode: 'socratic',
      currentProjectId: null,
    });
  },
}));
