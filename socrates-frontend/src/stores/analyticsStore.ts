/**
 * Analytics Store - Analytics and insights state management
 *
 * Manages:
 * - Project analytics summary
 * - Trends data
 * - Recommendations
 * - Comparative analysis
 */

import { create } from 'zustand';
import { analyticsAPI } from '../api/analytics';
import type {
  AnalyticsSummary,
  TrendsData,
  RecommendationsData,
  ExportFormat,
  ComparativeAnalysis,
} from '../api/analytics';

interface AnalyticsState {
  // State
  summary: AnalyticsSummary | null;
  trends: TrendsData | null;
  recommendations: RecommendationsData | null;
  comparativeAnalysis: ComparativeAnalysis | null;
  lastProjectId: string | null;

  // Loading states
  isLoadingSummary: boolean;
  isLoadingTrends: boolean;
  isLoadingRecommendations: boolean;
  isLoadingComparative: boolean;
  isExporting: boolean;
  error: string | null;

  // Actions
  getSummary: (projectId: string) => Promise<void>;
  getTrends: (projectId: string, timePeriod?: string) => Promise<void>;
  getRecommendations: (projectId: string) => Promise<void>;
  compareProjects: (
    project1Id: string,
    project2Id: string
  ) => Promise<void>;
  exportAnalytics: (
    projectId: string,
    format?: 'csv' | 'json' | 'pdf'
  ) => Promise<ExportFormat | null>;
  analyzeProject: (projectId: string) => Promise<void>;
  clearResults: () => void;
  clearError: () => void;
}

export const useAnalyticsStore = create<AnalyticsState>((set) => ({
  // Initial state
  summary: null,
  trends: null,
  recommendations: null,
  comparativeAnalysis: null,
  lastProjectId: null,

  isLoadingSummary: false,
  isLoadingTrends: false,
  isLoadingRecommendations: false,
  isLoadingComparative: false,
  isExporting: false,
  error: null,

  /**
   * Get analytics summary
   */
  getSummary: async (projectId: string) => {
    set({ isLoadingSummary: true, error: null, lastProjectId: projectId });
    try {
      const result = await analyticsAPI.getSummary(projectId);
      set({ summary: result, isLoadingSummary: false });
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : 'Failed to load analytics summary';
      set({ error: message, isLoadingSummary: false });
      throw err;
    }
  },

  /**
   * Get analytics trends
   */
  getTrends: async (projectId: string, timePeriod: string = '30d') => {
    set({ isLoadingTrends: true, error: null, lastProjectId: projectId });
    try {
      const result = await analyticsAPI.getTrends(projectId, timePeriod);
      set({ trends: result, isLoadingTrends: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load trends data';
      set({ error: message, isLoadingTrends: false });
      throw err;
    }
  },

  /**
   * Get recommendations
   */
  getRecommendations: async (projectId: string) => {
    set({
      isLoadingRecommendations: true,
      error: null,
      lastProjectId: projectId,
    });
    try {
      const result = await analyticsAPI.getRecommendations(projectId);
      set({ recommendations: result, isLoadingRecommendations: false });
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : 'Failed to load recommendations';
      set({ error: message, isLoadingRecommendations: false });
      throw err;
    }
  },

  /**
   * Compare projects
   */
  compareProjects: async (project1Id: string, project2Id: string) => {
    set({ isLoadingComparative: true, error: null });
    try {
      const result = await analyticsAPI.compareProjects(project1Id, project2Id);
      set({ comparativeAnalysis: result, isLoadingComparative: false });
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : 'Failed to compare projects';
      set({ error: message, isLoadingComparative: false });
      throw err;
    }
  },

  /**
   * Export analytics data
   */
  exportAnalytics: async (
    projectId: string,
    format: 'csv' | 'json' | 'pdf' = 'json'
  ) => {
    set({ isExporting: true, error: null });
    try {
      const result = await analyticsAPI.exportAnalytics(projectId, format);
      set({ isExporting: false });
      return result;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to export analytics';
      set({ error: message, isExporting: false });
      throw err;
    }
  },

  /**
   * Analyze project
   */
  analyzeProject: async (projectId: string) => {
    set({
      isLoadingSummary: true,
      error: null,
      lastProjectId: projectId,
    });
    try {
      await analyticsAPI.analyzeProject(projectId);
      // Refresh summary after analysis
      const summary = await analyticsAPI.getSummary(projectId);
      set({ summary, isLoadingSummary: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to analyze project';
      set({ error: message, isLoadingSummary: false });
      throw err;
    }
  },

  /**
   * Clear all results
   */
  clearResults: () => {
    set({
      summary: null,
      trends: null,
      recommendations: null,
      comparativeAnalysis: null,
      lastProjectId: null,
    });
  },

  /**
   * Clear error message
   */
  clearError: () => {
    set({ error: null });
  },
}));
