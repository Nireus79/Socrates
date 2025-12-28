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

export interface MaturityResult extends AnalysisResult {
  overall_score?: number;
  phase?: string;
  dimensions?: {
    [key: string]: number;
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
 * Assess project maturity
 */
export async function assessMaturity(projectId: string, phase?: string): Promise<MaturityResult> {
  const params = new URLSearchParams({ project_id: projectId });
  if (phase) params.append('phase', phase);
  const response = await apiClient.post(`/analysis/maturity?${params}`, {}) as any;
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
