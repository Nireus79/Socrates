/**
 * Project Analysis API client
 *
 * Provides methods for code validation, testing, review, and analysis:
 * - Validate project code
 * - Run tests
 * - Analyze structure
 * - Perform code review
 * - Auto-fix issues
 */

import { apiClient } from './client';

// Type definitions for Analysis API

export interface ValidationResults {
  total_files: number;
  valid_files: number;
  files_with_issues: number;
  issues: ValidationIssue[];
  code_quality_score: number;
}

export interface ValidationIssue {
  file: string;
  line: number;
  column: number;
  severity: 'error' | 'warning' | 'info';
  message: string;
  code: string;
}

export interface TestResults {
  test_type: string;
  total_tests: number;
  passed: number;
  failed: number;
  skipped: number;
  duration: number;
  coverage: number;
  failures: TestFailure[];
}

export interface TestFailure {
  test_name: string;
  error: string;
  stack_trace: string;
}

export interface StructureAnalysis {
  files: number;
  total_lines: number;
  modules: AnalysisModule[];
  dependencies: string[];
  complexity_score: number;
  maintainability_index: number;
}

export interface AnalysisModule {
  name: string;
  path: string;
  lines: number;
  functions: number;
}

export interface CodeReviewFindings {
  review_type: string;
  total_issues: number;
  critical: number;
  major: number;
  minor: number;
  suggestions: number;
  findings: ReviewFinding[];
  summary: string;
}

export interface ReviewFinding {
  severity: 'critical' | 'major' | 'minor' | 'suggestion';
  category: string;
  title: string;
  description: string;
  location: string;
  recommendation: string;
}

export interface AutoFixResults {
  apply_changes: boolean;
  files_modified: number;
  issues_fixed: number;
  changes: FileChange[];
  warnings: string[];
}

export interface FileChange {
  file: string;
  change_type: 'add' | 'modify' | 'delete';
  description: string;
}

export interface AnalysisReport {
  project_id: string;
  generated_at: string;
  code_quality: {
    score: number;
    grade: string;
  };
  validation: {
    status: string;
    issues: number;
  };
  tests: {
    status: string;
    coverage: number;
  };
  structure: {
    complexity: number;
    maintainability: number;
  };
  recommendations: string[];
}

/**
 * Project Analysis API client
 */
export const analysisAPI = {
  /**
   * Validate project code
   */
  async validateCode(projectId: string): Promise<ValidationResults> {
    const params = new URLSearchParams();
    params.append('project_id', projectId);
    return apiClient.post<ValidationResults>(
      `/analysis/validate?${params.toString()}`,
      {}
    );
  },

  /**
   * Run tests for project
   */
  async runTests(
    projectId: string,
    testType: string = 'all'
  ): Promise<TestResults> {
    const params = new URLSearchParams();
    params.append('project_id', projectId);
    params.append('test_type', testType);
    return apiClient.post<TestResults>(
      `/analysis/test?${params.toString()}`,
      {}
    );
  },

  /**
   * Analyze project structure
   */
  async analyzeStructure(projectId: string): Promise<StructureAnalysis> {
    const params = new URLSearchParams();
    params.append('project_id', projectId);
    return apiClient.post<StructureAnalysis>(
      `/analysis/structure?${params.toString()}`,
      {}
    );
  },

  /**
   * Perform code review
   */
  async reviewCode(
    projectId: string,
    reviewType: string = 'full'
  ): Promise<CodeReviewFindings> {
    const params = new URLSearchParams();
    params.append('project_id', projectId);
    params.append('review_type', reviewType);
    return apiClient.post<CodeReviewFindings>(
      `/analysis/review?${params.toString()}`,
      {}
    );
  },

  /**
   * Auto-fix code issues
   */
  async autoFixIssues(
    projectId: string,
    issueTypes?: string[],
    applyChanges: boolean = false
  ): Promise<AutoFixResults> {
    const params = new URLSearchParams();
    params.append('project_id', projectId);
    if (issueTypes && issueTypes.length > 0) {
      issueTypes.forEach((type) => params.append('issue_types', type));
    }
    params.append('apply_changes', applyChanges.toString());
    return apiClient.post<AutoFixResults>(
      `/analysis/fix?${params.toString()}`,
      {}
    );
  },

  /**
   * Get analysis report
   */
  async getAnalysisReport(projectId: string): Promise<AnalysisReport> {
    return apiClient.get<AnalysisReport>(`/analysis/report/${projectId}`);
  },
};
