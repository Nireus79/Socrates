/**
 * API request and response type definitions
 */

// ============================================================================
// Authentication Requests
// ============================================================================

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

// ============================================================================
// Project Requests
// ============================================================================

export interface CreateProjectRequest {
  name: string;
  description?: string;
  owner?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
  phase?: string;
}

// ============================================================================
// Chat Requests
// ============================================================================

export interface SendChatMessageRequest {
  message: string;
  mode?: 'socratic' | 'direct';
}

export interface ChatHistoryQuery {
  limit?: number;
  offset?: number;
}

// ============================================================================
// Code Generation Requests
// ============================================================================

export interface GenerateCodeRequest {
  specification: string;
  language: string;
}

// ============================================================================
// API Response Wrappers
// ============================================================================

export interface ListResponse<T> {
  total: number;
  projects?: T[];
  messages?: T[];
  items?: T[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// ============================================================================
// HTTP Error Response
// ============================================================================

export interface APIError {
  status: number;
  error: string;
  message: string;
  error_code?: string;
  details?: Record<string, any>;
}
