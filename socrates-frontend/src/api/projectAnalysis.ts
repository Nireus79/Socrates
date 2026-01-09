/**
 * Project Analysis API - Code validation, review, testing, and analysis
 */

import { apiClient } from './client';

export interface AnalysisResult {
  status: string;
  message: string;
  [key: string]: any;
}

export interface ValidationResult extends AnalysisResult {
  errors?: Array<{
    type: string;
    line?: number;
    message: string;
  }>;
  warnings?: Array<{
    type: string;
    line?: number;
    message: string;
  }>;
}

export interface TestResult extends AnalysisResult {
  test_count?: number;
  passed?: number;
  failed?: number;
  coverage?: number;
}

export interface ReviewResult extends AnalysisResult {
  issues?: Array<{
    severity: 'critical' | 'major' | 'minor';
    location: string;
    description: string;
  }>;
}

export interface CategoryInfo {
  name: string;
  current_score: number;
  target_score: number;
  percentage: number;
  spec_count: number;
  confidence: number;
  remaining_score: number;
  specs_needed_estimate: number;
}

export interface CategoryBreakdown {
  strong: CategoryInfo[];
  adequate: CategoryInfo[];
  weak: CategoryInfo[];
  missing: CategoryInfo[];
}

export interface Statistics {
  total_categories: number;
  completed_categories: number;
  strong_categories: number;
  adequate_count?: number;
  weak_count?: number;
  missing_count?: number;
  total_points_earned: number;
  total_points_possible: number;
  average_category_confidence: number;
}

export interface Milestone {
  target_percentage: number;
  points_needed: number;
  estimated_specs: number;
  estimated_sessions: number;
}

export interface Recommendation {
  category?: string;
  title?: string;
  priority: 'critical' | 'high' | 'info' | 'success';
  description: string;
  action_items?: string[];
  focus_areas?: string[];
}

export interface PhaseAnalysis {
  overall_percentage: number;
  status: string;
  ready_to_advance: boolean;
  categories: CategoryBreakdown;
  statistics: Statistics;
  milestones: {
    reach_60_percent: Milestone;
    reach_80_percent: Milestone;
    reach_100_percent: Milestone;
  };
  recommendations: Recommendation[];
}

export interface MaturityResult extends AnalysisResult {
  project_id?: string;
  project_type?: string;
  current_phase?: string;
  overall_maturity?: number;
  phases?: {
    [key: string]: PhaseAnalysis;
  };
}

/**
 * Validate project code
 */
export async function validateProject(projectId: string): Promise<ValidationResult> {
  const params = new URLSearchParams({ project_id: projectId });
  const response = await apiClient.post(`/analysis/validate?${params}`, {}) as any;
  return response?.data || { status: 'error', message: 'Validation failed' };
}

/**
 * Run tests on project
 */
export async function testProject(projectId: string): Promise<TestResult> {
  const params = new URLSearchParams({ project_id: projectId });
  const response = await apiClient.post(`/analysis/test?${params}`, {}) as any;
  return response?.data || { status: 'error', message: 'Test failed' };
}

/**
 * Review project code
 */
export async function reviewProject(projectId: string): Promise<ReviewResult> {
  const params = new URLSearchParams({ project_id: projectId });
  const response = await apiClient.post(`/analysis/review?${params}`, {}) as any;
  return response?.data || { status: 'error', message: 'Review failed' };
}

/**
 * Assess project maturity with detailed analysis
 */
export async function assessMaturity(projectId: string, phase?: string): Promise<MaturityResult> {
  const params = new URLSearchParams({});
  if (phase) params.append('phase', phase);
  const response = await apiClient.get(`/projects/${projectId}/maturity/analysis?${params}`) as any;
  return response?.data || { status: 'error', message: 'Maturity assessment failed' };
}

/**
 * Analyze project structure
 */
export async function analyzeStructure(projectId: string): Promise<AnalysisResult> {
  const params = new URLSearchParams({ project_id: projectId });
  const response = await apiClient.post(`/analysis/structure?${params}`, {}) as any;
  return response?.data || { status: 'error', message: 'Structure analysis failed' };
}

/**
 * Fix project issues
 */
export async function fixProject(projectId: string): Promise<AnalysisResult> {
  const params = new URLSearchParams({ project_id: projectId });
  const response = await apiClient.post(`/analysis/fix?${params}`, {}) as any;
  return response?.data || { status: 'error', message: 'Fix failed' };
}

/**
 * Get analysis report
 */
export async function getAnalysisReport(projectId: string): Promise<AnalysisResult> {
  const response = await apiClient.get(`/analysis/report/${projectId}`) as any;
  return response?.data || { status: 'error', message: 'Report not found' };
}
