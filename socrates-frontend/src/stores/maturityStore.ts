/**
 * Maturity Store - Manages project maturity and progress tracking
 */

import { create } from 'zustand';
import { apiClient } from '../api/client';

export interface MaturityData {
  overall_maturity?: number;
  phase_maturity_scores?: Record<string, number>;
  confidence_score?: number;
  code_quality?: number;
  [key: string]: any;
}

export interface ProgressData {
  project_id: string;
  project_name: string;
  status: string;
  conversation_progress?: {
    total_messages: number;
    last_message_at?: string;
  };
  code_generation_progress?: {
    generated_files: number;
    last_generated_at?: string;
  };
  documentation_progress?: {
    documents_created: number;
    last_document_at?: string;
  };
  knowledge_progress?: {
    knowledge_entries: number;
    last_entry_at?: string;
  };
  [key: string]: any;
}

interface MaturityState {
  // State
  selectedProjectId: string | null;
  isLoading: boolean;
  error: string | null;

  // Data
  maturityData: MaturityData | null;
  progressData: ProgressData | null;
  progressStatus: any | null;

  // Actions
  setSelectedProject: (projectId: string | null) => void;
  fetchMaturity: (projectId: string) => Promise<void>;
  fetchProgress: (projectId: string) => Promise<void>;
  fetchProgressStatus: (projectId: string) => Promise<void>;
  fetchAll: (projectId: string) => Promise<void>;
  clearError: () => void;
}

export const useMaturityStore = create<MaturityState>((set, get) => ({
  // Initial state
  selectedProjectId: null,
  isLoading: false,
  error: null,
  maturityData: null,
  progressData: null,
  progressStatus: null,

  // Set selected project
  setSelectedProject: (projectId: string | null) => {
    set({ selectedProjectId: projectId });
  },

  // Fetch maturity data
  fetchMaturity: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get(`/projects/${projectId}/maturity`) as any;
      set({
        maturityData: response?.data || response,
        selectedProjectId: projectId,
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch maturity data';
      set({ error: message, isLoading: false });
    }
  },

  // Fetch progress data
  fetchProgress: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get(`/projects/${projectId}/progress`) as any;
      set({
        progressData: response?.data || response,
        selectedProjectId: projectId,
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch progress data';
      set({ error: message, isLoading: false });
    }
  },

  // Fetch detailed progress status
  fetchProgressStatus: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get(`/projects/${projectId}/progress/status`) as any;
      set({
        progressStatus: response?.data || response,
        selectedProjectId: projectId,
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch progress status';
      set({ error: message, isLoading: false });
    }
  },

  // Fetch all maturity and progress data
  fetchAll: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const [maturityRes, progressRes, statusRes] = await Promise.all([
        apiClient.get(`/projects/${projectId}/maturity`) as Promise<any>,
        apiClient.get(`/projects/${projectId}/progress`) as Promise<any>,
        apiClient.get(`/projects/${projectId}/progress/status`) as Promise<any>,
      ]);

      set({
        maturityData: maturityRes?.data || maturityRes,
        progressData: progressRes?.data || progressRes,
        progressStatus: statusRes?.data || statusRes,
        selectedProjectId: projectId,
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch maturity and progress data';
      set({ error: message, isLoading: false });
    }
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },
}));
