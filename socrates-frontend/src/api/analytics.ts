/**
 * Analytics API service
 *
 * Provides methods for project analytics, trends, and recommendations:
 * - Get analytics summary
 * - Get analytics trends
 * - Get project recommendations
 * - Export analytics data
 * - Compare projects
 */

import { apiClient } from './client';

// Type definitions for Analytics API

export interface AnalyticsSummary {
  project_id: string;
  total_questions: number;
  total_answers: number;
  confidence_score: number;
  code_generation_count: number;
  code_lines_generated: number;
  average_response_time: number;
  learning_velocity: number;
  categories: Record<string, number>;
}

export interface AnalyticsTrend {
  date: string;
  questions_asked: number;
  answers_provided: number;
  code_generated: number;
  confidence_score: number;
}

export interface TrendsData {
  project_id: string;
  time_period: string;
  trends: AnalyticsTrend[];
  average_questions_per_day: number;
  peak_activity_day: string;
  trend_direction: 'increasing' | 'stable' | 'decreasing';
}

export interface Recommendation {
  priority: 'high' | 'medium' | 'low';
  category: string;
  title: string;
  description: string;
  action_items: string[];
  estimated_impact: string;
}

export interface RecommendationsData {
  project_id: string;
  generated_at: string;
  recommendations: Recommendation[];
  focus_areas: string[];
  next_steps: string[];
}

export interface ExportFormat {
  format: 'csv' | 'json' | 'pdf';
  filename: string;
  data: string;
  size: number;
}

export interface ComparativeAnalysis {
  project_1_id: string;
  project_2_id: string;
  comparison_date: string;
  metrics: {
    questions: { project_1: number; project_2: number; difference: number };
    confidence: { project_1: number; project_2: number; difference: number };
    code_generated: { project_1: number; project_2: number; difference: number };
    velocity: { project_1: number; project_2: number; difference: number };
  };
  summary: string;
}

/**
 * Analytics API client
 */
export const analyticsAPI = {
  /**
   * Get analytics summary for a project
   */
  async getSummary(projectId: string): Promise<AnalyticsSummary> {
    return apiClient.get<AnalyticsSummary>(
      `/analytics/summary`,
      { params: { project_id: projectId } }
    );
  },

  /**
   * Get analytics trends for a project
   */
  async getTrends(
    projectId: string,
    timePeriod: string = '30d'
  ): Promise<TrendsData> {
    return apiClient.get<TrendsData>(
      `/analytics/trends`,
      { params: { project_id: projectId, time_period: timePeriod } }
    );
  },

  /**
   * Get recommendations based on analytics
   */
  async getRecommendations(projectId: string): Promise<RecommendationsData> {
    return apiClient.post<RecommendationsData>(
      `/analytics/recommend`,
      { project_id: projectId }
    );
  },

  /**
   * Export analytics data
   */
  async exportAnalytics(
    projectId: string,
    format: 'csv' | 'json' | 'pdf' = 'json'
  ): Promise<ExportFormat> {
    return apiClient.post<ExportFormat>(
      `/analytics/export`,
      { project_id: projectId, format }
    );
  },

  /**
   * Compare two projects
   */
  async compareProjects(
    project1Id: string,
    project2Id: string
  ): Promise<ComparativeAnalysis> {
    return apiClient.post<ComparativeAnalysis>(
      `/analytics/comparative`,
      { project_1_id: project1Id, project_2_id: project2Id }
    );
  },

  /**
   * Get analytics report
   */
  async getReport(projectId: string): Promise<any> {
    return apiClient.post(
      `/analytics/report`,
      { project_id: projectId }
    );
  },

  /**
   * Analyze project
   */
  async analyzeProject(projectId: string): Promise<any> {
    return apiClient.post(
      `/analytics/analyze`,
      { project_id: projectId }
    );
  },
};
