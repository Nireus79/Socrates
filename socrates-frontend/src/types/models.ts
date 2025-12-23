/**
 * Type definitions for Socrates API models
 */

// ============================================================================
// User & Authentication
// ============================================================================

export interface User {
  username: string;
  email: string;
  subscription_tier: 'free' | 'pro' | 'enterprise';
  subscription_status: 'active' | 'inactive' | 'suspended';
  testing_mode: boolean;
  created_at: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
}

// ============================================================================
// Projects
// ============================================================================

export type ProjectPhase = 'discovery' | 'analysis' | 'design' | 'implementation' | 'testing' | 'deployment';

export interface Project {
  project_id: string;
  name: string;
  description?: string;
  owner: string;
  phase: ProjectPhase;
  created_at: string;
  updated_at: string;
  is_archived: boolean;
}

export interface ProjectStats {
  project_id: string;
  phase: ProjectPhase;
  progress: number;
  total_questions: number;
  questions_asked?: number;
  questions_change: number;
  average_confidence: number;
  confidence_change: number;
  code_generations: number;
  code_generated?: number;
  code_generation_change: number;
  documents_processed: number;
  velocity: number;
  velocity_change: number;
}

export interface MaturityCategory {
  name: string;
  maturity: number;
  confidence: number;
  specCount: number;
}

export interface MaturityRecommendation {
  priority: 'info' | 'medium' | 'high';
  title: string;
  description: string;
}

export interface ProjectMaturity {
  project_id: string;
  phase: ProjectPhase;
  overall_score: number;
  phase_1_maturity: number;
  phase_2_maturity: number;
  phase_3_maturity: number;
  phase_4_maturity: number;
  testing_score?: number;
  deployment_score?: number;
  strongest_category: string;
  weakest_category: string;
  ready_to_advance: boolean;
  categories: MaturityCategory[];
  recommendations: MaturityRecommendation[];
}

// ============================================================================
// Chat & Messages
// ============================================================================

export type ChatMode = 'socratic' | 'direct';

export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface ConversationHistory {
  project_id: string;
  messages: ChatMessage[];
  mode: ChatMode;
  total: number;
}

// ============================================================================
// WebSocket Messages
// ============================================================================

export type WSMessageType = 'chat_message' | 'command' | 'ping' | 'pong' | 'error';

export type WSResponseType = 'assistant_response' | 'event' | 'error' | 'acknowledgment';

export interface WebSocketMessage {
  type: WSMessageType;
  content: string;
  metadata?: {
    mode?: ChatMode;
    requestHint?: boolean;
  };
  requestId?: string;
}

export interface WebSocketResponse {
  type: WSResponseType;
  content?: string;
  eventType?: string;
  data?: Record<string, any>;
  requestId?: string;
  errorCode?: string;
  errorMessage?: string;
  timestamp: string;
}

// ============================================================================
// Code Generation
// ============================================================================

export interface CodeGenerationRequest {
  specification: string;
  language: string;
}

export interface GeneratedCode {
  code: string;
  explanation: string;
  language: string;
  token_usage?: number;
}

// ============================================================================
// Documents
// ============================================================================

export interface DocumentMetadata {
  id: string;
  name: string;
  file_type: string;
  size: number;
  uploaded_at: string;
  processed: boolean;
  indexed: boolean;
}

// ============================================================================
// Subscriptions
// ============================================================================

export interface SubscriptionTier {
  name: 'free' | 'pro' | 'enterprise';
  features: {
    max_projects: number | null;
    max_team_members: number | null;
    max_questions_per_month: number | null;
    code_generation: boolean;
    collaboration: boolean;
    api_access: boolean;
    advanced_analytics: boolean;
  };
  price_monthly?: number;
  price_annual?: number;
}

// ============================================================================
// API Responses
// ============================================================================

export interface SuccessResponse<T = any> {
  status: 'success';
  data?: T;
}

export interface ErrorResponse {
  status: 'error';
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}

// ============================================================================
// Analytics
// ============================================================================

export interface AnalyticsData {
  project_id: string;
  total_questions: number;
  total_responses: number;
  average_question_difficulty: number;
  response_accuracy: number;
  learning_velocity: number;
  recommended_next_topic?: string;
}

// ============================================================================
// Collaboration
// ============================================================================

export type CollaboratorRole = 'owner' | 'editor' | 'viewer';

export interface Collaborator {
  username: string;
  role: CollaboratorRole;
  status: 'active' | 'pending' | 'inactive';
  joined_at: string;
  last_activity?: string;
}

export interface ProjectPresence {
  username: string;
  status: 'online' | 'offline';
  last_activity: string;
  current_activity?: string;
}

// ============================================================================
// Code Generation
// ============================================================================

export type ProgrammingLanguage =
  | 'python'
  | 'javascript'
  | 'typescript'
  | 'java'
  | 'cpp'
  | 'csharp'
  | 'go'
  | 'rust'
  | 'sql';

export interface CodeGeneration {
  code: string;
  explanation: string;
  language: ProgrammingLanguage;
  token_usage?: number;
  generation_id: string;
  created_at: string;
}

export interface CodeValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
  complexity_score: number;
  readability_score: number;
}

export interface LanguageInfo {
  display: string;
  version: string;
}
