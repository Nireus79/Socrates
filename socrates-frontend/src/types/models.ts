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

// ============================================================================
// Collaboration - Invitations
// ============================================================================

export interface Invitation {
  id: string;
  project_id: string;
  inviter_id: string;
  invitee_email: string;
  role: CollaboratorRole;
  token: string;
  status: 'pending' | 'accepted' | 'cancelled' | 'expired';
  created_at: string;
  expires_at: string;
  accepted_at?: string;
}

export interface InvitationResponse {
  invitation_id?: string;
  id?: string;
  token: string;
  email: string;
  role: CollaboratorRole;
  status: string;
  created_at: string;
  expires_at: string;
}

export interface InvitationsListResponse {
  invitations: Invitation[];
  total?: number;
  pagination?: {
    limit: number;
    offset: number;
    total: number;
    has_more: boolean;
  };
}

export interface AcceptInvitationResponse {
  status: string;
  message?: string;
  project?: Project;
  member?: {
    username: string;
    role: CollaboratorRole;
  };
}

// ============================================================================
// Collaboration - Real-Time
// ============================================================================

export interface UserPresence {
  username: string;
  status: 'active' | 'idle' | 'offline';
  last_seen: string;
  avatar_url?: string;
}

export interface Activity {
  id: string;
  project_id: string;
  user_id: string;
  activity_type: string;
  activity_data?: Record<string, any>;
  created_at: string;
}

export interface ActivitiesResponse {
  activities: Activity[];
  total: number;
  pagination?: {
    limit: number;
    offset: number;
    total: number;
    has_more: boolean;
  };
}

export interface PresenceResponse {
  collaborators: UserPresence[];
  total?: number;
}

// ============================================================================
// Knowledge Base - Documents
// ============================================================================

export interface DocumentDetails {
  id: string;
  title: string;
  source: string;
  document_type: 'text' | 'file' | 'url';
  uploaded_at: string;
  word_count: number;
  character_count?: number;
  preview?: string;
  content?: string;
  metadata?: Record<string, any>;
  file_path?: string;
  file_size?: number;
}

export interface DocumentDetailsResponse {
  status: string;
  document: DocumentDetails;
}

export interface DocumentAnalytics {
  word_count: number;
  character_count?: number;
  estimated_reading_time_minutes?: number;
  views?: number;
  searches?: number;
  last_accessed?: string;
}

export interface DocumentAnalyticsResponse {
  status: string;
  analytics: DocumentAnalytics;
}

// ============================================================================
// Knowledge Base - Bulk Operations
// ============================================================================

export interface BulkDeleteResponse {
  status: string;
  deleted: string[];
  failed: Array<{
    id: string;
    reason: string;
  }>;
  summary: {
    total_requested: number;
    deleted_count: number;
    failed_count: number;
  };
}

export interface BulkImportResult {
  file: string;
  status: 'success' | 'failed';
  document_id?: string;
  error?: string;
}

export interface BulkImportResponse {
  status: string;
  results: BulkImportResult[];
  summary: {
    total: number;
    imported: number;
    failed: number;
  };
}

// ============================================================================
// Knowledge Base - Filtering & Pagination
// ============================================================================

export interface DocumentListFilters {
  projectId?: string;
  documentType?: 'text' | 'file' | 'url' | null;
  searchQuery?: string;
  sortBy?: 'uploaded_at' | 'title' | 'document_type';
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface PaginationInfo {
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface Document {
  id: string;
  title: string;
  source: string;
  document_type: 'text' | 'file' | 'url';
  uploaded_at: string;
  word_count?: number;
}

export interface DocumentListResponse {
  status: string;
  data?: {
    documents: Document[];
    pagination: PaginationInfo;
  };
  documents?: Document[];
  pagination?: PaginationInfo;
  total?: number;
}
