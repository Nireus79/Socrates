/**
 * Analysis Store - Zustand state management
 *
 * Manages:
 * - Code validation results
 * - Test results
 * - Structure analysis
 * - Code review findings
 * - Auto-fix operations
 */

import { create } from 'zustand';
import { analysisAPI } from '../api/analysis';
import type {
  ValidationResults,
  TestResults,
  StructureAnalysis,
  CodeReviewFindings,
  AutoFixResults,
  AnalysisReport,
} from '../api/analysis';

interface AnalysisState {
  // State
  validationResults: ValidationResults | null;
  testResults: TestResults | null;
  structureAnalysis: StructureAnalysis | null;
  reviewFindings: CodeReviewFindings | null;
  analysisReport: AnalysisReport | null;
  lastAnalyzedProject: string | null;

  // Loading states
  isValidating: boolean;
  isTesting: boolean;
  isAnalyzing: boolean;
  isReviewing: boolean;
  isFixing: boolean;
  error: string | null;

  // Actions
  validateCode: (projectId: string) => Promise<void>;
  runTests: (projectId: string, testType?: string) => Promise<void>;
  analyzeStructure: (projectId: string) => Promise<void>;
  reviewCode: (projectId: string, reviewType?: string) => Promise<void>;
  autoFixIssues: (
    projectId: string,
    issueTypes?: string[],
    applyChanges?: boolean
  ) => Promise<void>;
  getAnalysisReport: (projectId: string) => Promise<void>;
  clearResults: () => void;
  clearError: () => void;
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  // Initial state
  validationResults: null,
  testResults: null,
  structureAnalysis: null,
  reviewFindings: null,
  analysisReport: null,
  lastAnalyzedProject: null,

  isValidating: false,
  isTesting: false,
  isAnalyzing: false,
  isReviewing: false,
  isFixing: false,
  error: null,

  /**
   * Validate code
   */
  validateCode: async (projectId: string) => {
    set({ isValidating: true, error: null, lastAnalyzedProject: projectId });
    try {
      const results = await analysisAPI.validateCode(projectId);
      set({ validationResults: results, isValidating: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to validate code';
      set({ error: message, isValidating: false });
      throw err;
    }
  },

  /**
   * Run tests
   */
  runTests: async (projectId: string, testType: string = 'all') => {
    set({ isTesting: true, error: null, lastAnalyzedProject: projectId });
    try {
      const results = await analysisAPI.runTests(projectId, testType);
      set({ testResults: results, isTesting: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to run tests';
      set({ error: message, isTesting: false });
      throw err;
    }
  },

  /**
   * Analyze structure
   */
  analyzeStructure: async (projectId: string) => {
    set({ isAnalyzing: true, error: null, lastAnalyzedProject: projectId });
    try {
      const results = await analysisAPI.analyzeStructure(projectId);
      set({ structureAnalysis: results, isAnalyzing: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to analyze structure';
      set({ error: message, isAnalyzing: false });
      throw err;
    }
  },

  /**
   * Review code
   */
  reviewCode: async (projectId: string, reviewType: string = 'full') => {
    set({ isReviewing: true, error: null, lastAnalyzedProject: projectId });
    try {
      const results = await analysisAPI.reviewCode(projectId, reviewType);
      set({ reviewFindings: results, isReviewing: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to review code';
      set({ error: message, isReviewing: false });
      throw err;
    }
  },

  /**
   * Auto-fix issues
   */
  autoFixIssues: async (
    projectId: string,
    issueTypes?: string[],
    applyChanges: boolean = false
  ) => {
    set({ isFixing: true, error: null });
    try {
      await analysisAPI.autoFixIssues(projectId, issueTypes, applyChanges);
      set({ isFixing: false });

      // If changes were applied, refresh validation
      if (applyChanges) {
        await get().validateCode(projectId);
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to apply fixes';
      set({ error: message, isFixing: false });
      throw err;
    }
  },

  /**
   * Get analysis report
   */
  getAnalysisReport: async (projectId: string) => {
    set({ isAnalyzing: true, error: null, lastAnalyzedProject: projectId });
    try {
      const report = await analysisAPI.getAnalysisReport(projectId);
      set({ analysisReport: report, isAnalyzing: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to get analysis report';
      set({ error: message, isAnalyzing: false });
      throw err;
    }
  },

  /**
   * Clear all results
   */
  clearResults: () => {
    set({
      validationResults: null,
      testResults: null,
      structureAnalysis: null,
      reviewFindings: null,
      analysisReport: null,
      lastAnalyzedProject: null,
    });
  },

  /**
   * Clear error message
   */
  clearError: () => {
    set({ error: null });
  },
}));
