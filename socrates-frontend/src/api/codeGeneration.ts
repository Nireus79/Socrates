/**
 * Code Generation API service
 */

import { apiClient } from './client';
import type {
  CodeGeneration,
  CodeValidationResult,
  ProgrammingLanguage,
  LanguageInfo,
} from '../types/models';

export const codeGenerationAPI = {
  /**
   * Generate code from specification
   */
  async generateCode(
    projectId: string,
    specification: string,
    language: ProgrammingLanguage = 'python',
    requirements?: string
  ): Promise<CodeGeneration> {
    return apiClient.post<CodeGeneration>(
      `/projects/${projectId}/code/generate`,
      { specification, requirements },
      { params: { language } }
    );
  },

  /**
   * Validate code for syntax and best practices
   */
  async validateCode(
    projectId: string,
    code: string,
    language: ProgrammingLanguage = 'python'
  ): Promise<CodeValidationResult> {
    return apiClient.post<CodeValidationResult>(
      `/projects/${projectId}/code/validate`,
      { code },
      { params: { language } }
    );
  },

  /**
   * Get code generation history
   */
  async getCodeHistory(
    projectId: string,
    limit: number = 20,
    offset: number = 0
  ): Promise<{ generations: CodeGeneration[]; total: number }> {
    return apiClient.get<{ generations: CodeGeneration[]; total: number }>(
      `/projects/${projectId}/code/history`,
      { params: { limit, offset } }
    );
  },

  /**
   * Get supported programming languages
   */
  async getSupportedLanguages(): Promise<Record<string, LanguageInfo>> {
    const response = await apiClient.get<{ languages: Record<string, LanguageInfo> }>(
      `/languages`
    );
    return response.languages;
  },

  /**
   * Refactor existing code
   */
  async refactorCode(
    projectId: string,
    code: string,
    language: ProgrammingLanguage = 'python',
    refactorType: 'optimize' | 'simplify' | 'document' | 'modernize' = 'optimize'
  ): Promise<{ refactored_code: string; explanation: string; changes: string[] }> {
    return apiClient.post<{
      refactored_code: string;
      explanation: string;
      changes: string[];
    }>(`/projects/${projectId}/code/refactor`, { code }, { params: { language, refactor_type: refactorType } });
  },
};
