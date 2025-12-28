/**
 * Project Analysis Store - Manages project analysis state
 */

import { create } from 'zustand';
import * as analysisAPI from '../api/projectAnalysis';

export interface AnalysisState {
  // State
  selectedProjectId: string | null;
  isLoading: boolean;
  error: string | null;

  // Analysis results
  validationResult: any | null;
  testResult: any | null;
  reviewResult: any | null;
  maturityResult: any | null;
  structureResult: any | null;
  reportResult: any | null;

  // Active tab
  activeAnalysis: 'validation' | 'testing' | 'review' | 'maturity' | 'structure' | 'report' | null;

  // Actions
  setSelectedProject: (projectId: string | null) => void;
  validateCode: (projectId: string) => Promise<void>;
  testCode: (projectId: string) => Promise<void>;
  reviewCode: (projectId: string) => Promise<void>;
  assessMaturity: (projectId: string, phase?: string) => Promise<void>;
  analyzeStructure: (projectId: string) => Promise<void>;
  fixCode: (projectId: string) => Promise<void>;
  getReport: (projectId: string) => Promise<void>;
  clearResults: () => void;
  clearError: () => void;
  setActiveAnalysis: (analysis: AnalysisState['activeAnalysis']) => void;
}

export const useProjectAnalysisStore = create<AnalysisState>((set, get) => ({
  // Initial state
  selectedProjectId: null,
  isLoading: false,
  error: null,
  validationResult: null,
  testResult: null,
  reviewResult: null,
  maturityResult: null,
  structureResult: null,
  reportResult: null,
  activeAnalysis: null,

  // Set selected project
  setSelectedProject: (projectId: string | null) => {
    set({ selectedProjectId: projectId });
  },

  // Validate code
  validateCode: async (projectId: string) => {
    set({ isLoading: true, error: null, activeAnalysis: 'validation' });
    try {
      const result = await analysisAPI.validateProject(projectId);
      set({
        validationResult: result,
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to validate code';
      set({ error: message, isLoading: false });
    }
  },

  // Test code
  testCode: async (projectId: string) => {
    set({ isLoading: true, error: null, activeAnalysis: 'testing' });
    try {
      const result = await analysisAPI.testProject(projectId);
      set({
        testResult: result,
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to test code';
      set({ error: message, isLoading: false });
    }
  },

  // Review code
  reviewCode: async (projectId: string) => {
    set({ isLoading: true, error: null, activeAnalysis: 'review' });
    try {
      const result = await analysisAPI.reviewProject(projectId);
      set({
        reviewResult: result,
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to review code';
      set({ error: message, isLoading: false });
    }
  },

  // Assess maturity
  assessMaturity: async (projectId: string, phase?: string) => {
    set({ isLoading: true, error: null, activeAnalysis: 'maturity' });
    try {
      const result = await analysisAPI.assessMaturity(projectId, phase);
      set({
        maturityResult: result,
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to assess maturity';
      set({ error: message, isLoading: false });
    }
  },

  // Analyze structure
  analyzeStructure: async (projectId: string) => {
    set({ isLoading: true, error: null, activeAnalysis: 'structure' });
    try {
      const result = await analysisAPI.analyzeStructure(projectId);
      set({
        structureResult: result,
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to analyze structure';
      set({ error: message, isLoading: false });
    }
  },

  // Fix code
  fixCode: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const result = await analysisAPI.fixProject(projectId);
      // After fixing, re-validate to show updated results
      await get().validateCode(projectId);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fix code';
      set({ error: message, isLoading: false });
    }
  },

  // Get report
  getReport: async (projectId: string) => {
    set({ isLoading: true, error: null, activeAnalysis: 'report' });
    try {
      const result = await analysisAPI.getAnalysisReport(projectId);
      set({
        reportResult: result,
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to get report';
      set({ error: message, isLoading: false });
    }
  },

  // Clear results
  clearResults: () => {
    set({
      validationResult: null,
      testResult: null,
      reviewResult: null,
      maturityResult: null,
      structureResult: null,
      reportResult: null,
      activeAnalysis: null,
    });
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },

  // Set active analysis
  setActiveAnalysis: (analysis) => {
    set({ activeAnalysis: analysis });
  },
}));
