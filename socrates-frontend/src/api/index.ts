/**
 * API module - Central export point for all API services
 */

export { apiClient } from './client';
export { authAPI } from './auth';
export { projectsAPI } from './projects';
export { chatAPI } from './chat';
export { collaborationAPI } from './collaboration';
export { codeGenerationAPI } from './codeGeneration';
// GitHub exports individual functions, not githubAPI object
export * as github from './github';
export { knowledgeAPI } from './knowledge';
export { llmAPI } from './llm';
export { analysisAPI } from './analysis';
export { analyticsAPI } from './analytics';
export { nluAPI } from './nlu';
