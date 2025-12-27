/**
 * Progress Store - Zustand state management
 *
 * Manages Phase 4 progress tracking endpoints:
 * - Get overall project progress
 * - Get detailed progress status
 * - Track milestones and trends
 */

import { create } from 'zustand';
import { apiClient } from '../api/client';
import type { SuccessResponse } from '../api/types';

interface ProgressMetrics {
  total_messages?: number;
  last_message_at?: string;
  total_code_blocks?: number;
  current_score?: number;
  previous_score?: number;
  improvement?: number;
}

interface PhaseProgress {
  current_phase?: string;
  phase_scores?: Record<string, number>;
  total_phases?: number;
  completed_phases?: number;
}

interface OverallProgress {
  percentage: number;
  status: 'not_started' | 'in_progress' | 'completed';
}

interface ProjectProgress {
  project_id: string;
  project_name: string;
  status: string;
  created_at?: string;
  updated_at?: string;
  conversation_progress: ProgressMetrics;
  code_generation_progress: ProgressMetrics;
  maturity_progress: ProgressMetrics;
  phase_progress: PhaseProgress;
  category_progress: {
    total_categories?: number;
    categories?: Record<string, number>;
    average_category_score?: number;
  };
  skills_progress: {
    total_skills?: number;
    proficiency_breakdown?: Record<string, number>;
  };
  knowledge_progress: {
    total_items?: number;
    pinned_items?: number;
  };
  overall_progress: OverallProgress;
}

interface Milestone {
  completed: string[];
  total: number;
  completion_rate: string;
}

interface Trend {
  direction: 'improving' | 'declining' | 'stable';
  recent_change?: string;
  last_update?: string;
}

interface ProgressStatus {
  project_id: string;
  project_name: string;
  current_status: string;
  current_maturity: number;
  milestones: Milestone;
  trend: Trend;
  phase_status: {
    current: string;
    phases: Record<string, number>;
  };
  quality_metrics: {
    categories: Record<string, number>;
    analytics: Record<string, unknown>;
  };
  learning_metrics: {
    total_conversations: number;
    total_skills: number;
    knowledge_items: number;
  };
  recommendations: string[];
}

interface ProgressState {
  // State
  progress: ProjectProgress | null;
  status: ProgressStatus | null;
  isLoading: boolean;
  error: string | null;
  currentProjectId: string | null;

  // Actions
  getProgress: (projectId: string) => Promise<void>;
  getProgressStatus: (projectId: string) => Promise<void>;
  refreshProgress: (projectId: string) => Promise<void>;
  clearError: () => void;
}

export const useProgressStore = create<ProgressState>((set, get) => ({
  // Initial state
  progress: null,
  status: null,
  isLoading: false,
  error: null,
  currentProjectId: null,

  // Get overall progress
  getProgress: async (projectId: string) => {
    set({ isLoading: true, error: null, currentProjectId: projectId });
    try {
      const response = await apiClient.get<SuccessResponse>(`/projects/${projectId}/progress`);

      if (response.success && response.data) {
        set({
          progress: response.data,
          isLoading: false,
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get progress';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  // Get detailed progress status
  getProgressStatus: async (projectId: string) => {
    set({ isLoading: true, error: null, currentProjectId: projectId });
    try {
      const response = await apiClient.get<SuccessResponse>(
        `/projects/${projectId}/progress/status`
      );

      if (response.success && response.data) {
        set({
          status: response.data,
          isLoading: false,
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get progress status';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  // Refresh both progress and status
  refreshProgress: async (projectId: string) => {
    try {
      await Promise.all([
        get().getProgress(projectId),
        get().getProgressStatus(projectId),
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to refresh progress';
      set({ error: message });
      throw err;
    }
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },
}));
