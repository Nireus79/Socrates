/**
 * Code Generation Store - Code generation and refactoring state
 */

import { create } from 'zustand';
import type { CodeGeneration, CodeValidationResult, ProgrammingLanguage } from '../types/models';
import { codeGenerationAPI } from '../api';

interface CodeGenerationState {
  // State
  currentCode: string;
  generatedCode: CodeGeneration | null;
  validationResult: CodeValidationResult | null;
  codeHistory: CodeGeneration[];
  isLoading: boolean;
  error: string | null;
  currentLanguage: ProgrammingLanguage;

  // Actions
  generateCode: (
    projectId: string,
    specification: string,
    language?: ProgrammingLanguage
  ) => Promise<void>;
  validateCode: (
    projectId: string,
    code: string,
    language?: ProgrammingLanguage
  ) => Promise<void>;
  loadCodeHistory: (projectId: string) => Promise<void>;
  refactorCode: (
    projectId: string,
    code: string,
    language?: ProgrammingLanguage,
    refactorType?: 'optimize' | 'simplify' | 'document' | 'modernize'
  ) => Promise<void>;
  setCurrentCode: (code: string) => void;
  setCurrentLanguage: (language: ProgrammingLanguage) => void;
  clearError: () => void;
}

export const useCodeGenerationStore = create<CodeGenerationState>((set) => ({
  // Initial state
  currentCode: '',
  generatedCode: null,
  validationResult: null,
  codeHistory: [],
  isLoading: false,
  error: null,
  currentLanguage: 'python',

  // Generate code
  generateCode: async (
    projectId: string,
    specification: string,
    language: ProgrammingLanguage = 'python'
  ) => {
    set({ isLoading: true, error: null });
    try {
      const result = await codeGenerationAPI.generateCode(projectId, specification, language);
      set({ generatedCode: result, currentCode: result.code, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to generate code',
        isLoading: false,
      });
      throw error;
    }
  },

  // Validate code
  validateCode: async (
    projectId: string,
    code: string,
    language: ProgrammingLanguage = 'python'
  ) => {
    set({ isLoading: true, error: null });
    try {
      const result = await codeGenerationAPI.validateCode(projectId, code, language);
      set({ validationResult: result, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to validate code',
        isLoading: false,
      });
      throw error;
    }
  },

  // Load code history
  loadCodeHistory: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await codeGenerationAPI.getCodeHistory(projectId);
      set({ codeHistory: response.generations, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load history',
        isLoading: false,
      });
      throw error;
    }
  },

  // Refactor code
  refactorCode: async (
    projectId: string,
    code: string,
    language: ProgrammingLanguage = 'python',
    refactorType: 'optimize' | 'simplify' | 'document' | 'modernize' = 'optimize'
  ) => {
    set({ isLoading: true, error: null });
    try {
      const result = await codeGenerationAPI.refactorCode(
        projectId,
        code,
        language,
        refactorType
      );
      set({
        currentCode: result.refactored_code,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to refactor code',
        isLoading: false,
      });
      throw error;
    }
  },

  // Set current code
  setCurrentCode: (code: string) => {
    set({ currentCode: code });
  },

  // Set current language
  setCurrentLanguage: (language: ProgrammingLanguage) => {
    set({ currentLanguage: language });
  },

  // Clear error
  clearError: () => set({ error: null }),
}));
