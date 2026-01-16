-- ============================================================================
-- Socrates AI Database Schema V2 - Normalized Design
-- Replaces pickle BLOBs with normalized, queryable tables
-- ============================================================================

-- Main projects table (extracted from pickle BLOB)
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner TEXT NOT NULL,
    phase TEXT NOT NULL DEFAULT 'discovery',
    project_type TEXT DEFAULT 'software',
    team_structure TEXT DEFAULT 'individual',
    language_preferences TEXT DEFAULT 'python',
    deployment_target TEXT DEFAULT 'local',
    code_style TEXT DEFAULT 'standard',
    chat_mode TEXT DEFAULT 'socratic',
    goals TEXT,
    status TEXT DEFAULT 'active',
    progress INTEGER DEFAULT 0,
    is_archived BOOLEAN DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    archived_at TIMESTAMP,

    FOREIGN KEY (owner) REFERENCES users(username)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner);
CREATE INDEX IF NOT EXISTS idx_projects_phase ON projects(phase);
CREATE INDEX IF NOT EXISTS idx_projects_archived ON projects(is_archived);
CREATE INDEX IF NOT EXISTS idx_projects_updated ON projects(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_projects_owner_archived ON projects(owner, is_archived);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- Project requirements (normalized from array)
CREATE TABLE IF NOT EXISTS project_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    requirement TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_project_requirements_project ON project_requirements(project_id);

-- Project tech stack (normalized from array)
CREATE TABLE IF NOT EXISTS project_tech_stack (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    technology TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_project_tech_stack_project ON project_tech_stack(project_id);

-- Project constraints (normalized from array)
CREATE TABLE IF NOT EXISTS project_constraints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    constraint_text TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_project_constraints_project ON project_constraints(project_id);

-- Conversation history (separated for lazy loading)
CREATE TABLE IF NOT EXISTS conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    message_type TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,  -- JSON for extensibility

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_conversation_project_timestamp ON conversation_history(project_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_project ON conversation_history(project_id);

-- Pre-session conversations (before project selection)
CREATE TABLE IF NOT EXISTS free_session_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    session_id TEXT NOT NULL,
    message_type TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,  -- JSON for extensibility (topics, intents, etc.)

    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_free_session_user_session ON free_session_conversations(username, session_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_free_session_user ON free_session_conversations(username, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_free_session_session ON free_session_conversations(session_id);

-- Team members (normalized from array)
CREATE TABLE IF NOT EXISTS team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    skills TEXT,  -- JSON array
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(project_id, username),
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (username) REFERENCES users(username)
);
CREATE INDEX IF NOT EXISTS idx_team_members_project ON team_members(project_id);
CREATE INDEX IF NOT EXISTS idx_team_members_user ON team_members(username);

-- Phase maturity scores (normalized from dict)
CREATE TABLE IF NOT EXISTS phase_maturity_scores (
    project_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    score REAL DEFAULT 0.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (project_id, phase),
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_phase_maturity_project ON phase_maturity_scores(project_id);

-- Category scores by phase (normalized from nested dict)
CREATE TABLE IF NOT EXISTS category_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    category TEXT NOT NULL,
    score REAL NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(project_id, phase, category),
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_category_scores_project_phase ON category_scores(project_id, phase);

-- Categorized specifications
CREATE TABLE IF NOT EXISTS categorized_specs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    category TEXT NOT NULL,
    spec_data TEXT NOT NULL,  -- JSON
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_categorized_specs_project_phase ON categorized_specs(project_id, phase);

-- Maturity history
CREATE TABLE IF NOT EXISTS maturity_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    old_score REAL,
    new_score REAL,
    event_type TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,  -- JSON

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_maturity_history_project ON maturity_history(project_id);

-- Analytics metrics
CREATE TABLE IF NOT EXISTS analytics_metrics (
    project_id TEXT PRIMARY KEY,
    velocity REAL DEFAULT 0.0,
    total_qa_sessions INTEGER DEFAULT 0,
    avg_confidence REAL DEFAULT 0.0,
    weak_categories TEXT,  -- JSON array
    strong_categories TEXT,  -- JSON array
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_project ON analytics_metrics(project_id);

-- Pending questions (normalized from array)
CREATE TABLE IF NOT EXISTS pending_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    question_data TEXT NOT NULL,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sort_order INTEGER DEFAULT 0,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_pending_questions_project ON pending_questions(project_id);

-- Project notes (separate table)
CREATE TABLE IF NOT EXISTS project_notes (
    note_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT,
    content TEXT,
    note_type TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_project_notes_project ON project_notes(project_id);
CREATE INDEX IF NOT EXISTS idx_project_notes_created ON project_notes(created_at DESC);

-- Users table (normalized)
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    passcode_hash TEXT NOT NULL,
    subscription_tier TEXT DEFAULT 'free',
    subscription_status TEXT DEFAULT 'active',
    subscription_start TIMESTAMP,
    subscription_end TIMESTAMP,
    testing_mode BOOLEAN DEFAULT 0,
    is_archived BOOLEAN DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    archived_at TIMESTAMP,
    claude_auth_method TEXT DEFAULT 'api_key'  -- 'api_key' or 'subscription'
);
CREATE INDEX IF NOT EXISTS idx_users_archived ON users(is_archived);
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users(subscription_status);
CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_tier, subscription_status);

-- Question effectiveness tracking
CREATE TABLE IF NOT EXISTS question_effectiveness (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    question_template_id TEXT NOT NULL,
    effectiveness_score REAL DEFAULT 0.5,
    times_asked INTEGER DEFAULT 0,
    times_answered_well INTEGER DEFAULT 0,
    last_asked_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    UNIQUE(user_id, question_template_id),
    FOREIGN KEY (user_id) REFERENCES users(username)
);
CREATE INDEX IF NOT EXISTS idx_question_effectiveness_user ON question_effectiveness(user_id);
CREATE INDEX IF NOT EXISTS idx_question_effectiveness_template ON question_effectiveness(question_template_id);

-- Behavior patterns
CREATE TABLE IF NOT EXISTS behavior_patterns (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    pattern_data TEXT NOT NULL,  -- JSON
    frequency INTEGER DEFAULT 1,
    learned_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    UNIQUE(user_id, pattern_type),
    FOREIGN KEY (user_id) REFERENCES users(username)
);
CREATE INDEX IF NOT EXISTS idx_behavior_patterns_user ON behavior_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_behavior_patterns_type ON behavior_patterns(pattern_type);

-- Knowledge documents
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id TEXT PRIMARY KEY,
    project_id TEXT,  -- NULL for global knowledge
    user_id TEXT NOT NULL,
    title TEXT,
    content TEXT,
    source TEXT,
    document_type TEXT DEFAULT 'document',
    file_path TEXT,  -- Path to stored file (for downloads)
    file_size INTEGER,  -- File size in bytes
    uploaded_at TIMESTAMP NOT NULL,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(username)
);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_project ON knowledge_documents(project_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_user ON knowledge_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_type ON knowledge_documents(document_type);

-- LLM Provider configurations
CREATE TABLE IF NOT EXISTS llm_provider_configs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    config_data TEXT NOT NULL,  -- JSON
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    UNIQUE(user_id, provider),
    FOREIGN KEY (user_id) REFERENCES users(username)
);
CREATE INDEX IF NOT EXISTS idx_llm_configs_user ON llm_provider_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_configs_provider ON llm_provider_configs(provider);

-- API keys
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    encrypted_key TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    last_used_at TIMESTAMP,

    UNIQUE(user_id, provider),
    FOREIGN KEY (user_id) REFERENCES users(username)
);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_provider ON api_keys(provider);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_provider ON api_keys(user_id, provider);

-- LLM usage tracking
CREATE TABLE IF NOT EXISTS llm_usage (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0,
    timestamp TIMESTAMP NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(username)
);
CREATE INDEX IF NOT EXISTS idx_llm_usage_user ON llm_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_timestamp ON llm_usage(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_llm_usage_user_timestamp ON llm_usage(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_llm_usage_provider ON llm_usage(provider);

-- Refresh tokens for JWT authentication
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(username) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_revoked ON refresh_tokens(revoked_at);

-- API tokens for programmatic access
CREATE TABLE IF NOT EXISTS api_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(username) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_api_tokens_user ON api_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_api_tokens_expires ON api_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_api_tokens_revoked ON api_tokens(revoked_at);

-- Chat sessions (Phase 2 feature - session-based conversations)
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    title TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    archived INTEGER DEFAULT 0,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(username)
);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_project ON chat_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_archived ON chat_sessions(archived);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created ON chat_sessions(created_at DESC);

-- Chat messages (Phase 2 feature - messages within sessions)
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    metadata TEXT,  -- JSON string for extensibility
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(username)
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created ON chat_messages(session_id, created_at);

-- Collaboration invitations (Phase 2 feature - token-based invitations)
CREATE TABLE IF NOT EXISTS collaboration_invitations (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    inviter_id TEXT NOT NULL,
    invitee_email TEXT NOT NULL,
    role TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'pending',  -- pending, accepted, expired, cancelled
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    accepted_at TEXT,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (inviter_id) REFERENCES users(username)
);
CREATE INDEX IF NOT EXISTS idx_invitations_project ON collaboration_invitations(project_id);
CREATE INDEX IF NOT EXISTS idx_invitations_email ON collaboration_invitations(invitee_email);
CREATE INDEX IF NOT EXISTS idx_invitations_token ON collaboration_invitations(token);
CREATE INDEX IF NOT EXISTS idx_invitations_status ON collaboration_invitations(status);
CREATE INDEX IF NOT EXISTS idx_invitations_created ON collaboration_invitations(created_at DESC);

-- Collaboration activities (Phase 2 feature - activity logging)
CREATE TABLE IF NOT EXISTS collaboration_activities (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    activity_type TEXT NOT NULL,  -- member_added, member_removed, role_changed, file_uploaded, message_sent, etc.
    activity_data TEXT,  -- JSON for extensibility
    created_at TEXT NOT NULL,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(username)
);
CREATE INDEX IF NOT EXISTS idx_activities_project ON collaboration_activities(project_id);
CREATE INDEX IF NOT EXISTS idx_activities_created ON collaboration_activities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activities_type ON collaboration_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_activities_project_created ON collaboration_activities(project_id, created_at DESC);

-- Knowledge analytics (Phase 2 feature - document usage tracking)
CREATE TABLE IF NOT EXISTS knowledge_analytics (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- viewed, searched, exported, downloaded
    created_at TEXT NOT NULL,

    FOREIGN KEY (document_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(username)
);
CREATE INDEX IF NOT EXISTS idx_analytics_document ON knowledge_analytics(document_id);
CREATE INDEX IF NOT EXISTS idx_analytics_created ON knowledge_analytics(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_type ON knowledge_analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_document_created ON knowledge_analytics(document_id, created_at DESC);

-- GitHub Sponsors tracking (monetization)
CREATE TABLE IF NOT EXISTS sponsorships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    github_username TEXT NOT NULL,
    github_sponsor_id INTEGER,
    sponsorship_amount INTEGER NOT NULL,  -- Amount in dollars per month
    socrates_tier_granted TEXT NOT NULL,  -- "pro" or "enterprise"
    sponsorship_status TEXT DEFAULT 'active',  -- active, pending, cancelled
    sponsored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tier_expires_at TIMESTAMP,
    last_payment_at TIMESTAMP,
    payment_id TEXT,
    webhook_event_id TEXT,
    notes TEXT,

    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

-- Indexes for sponsorship queries
CREATE INDEX IF NOT EXISTS idx_sponsorships_username ON sponsorships(username);
CREATE INDEX IF NOT EXISTS idx_sponsorships_github_username ON sponsorships(github_username);
CREATE INDEX IF NOT EXISTS idx_sponsorships_status ON sponsorships(sponsorship_status);
CREATE INDEX IF NOT EXISTS idx_sponsorships_created ON sponsorships(sponsored_at DESC);
CREATE INDEX IF NOT EXISTS idx_sponsorships_expires ON sponsorships(tier_expires_at);
CREATE INDEX IF NOT EXISTS idx_sponsorships_active ON sponsorships(username, sponsorship_status) WHERE sponsorship_status = 'active';

-- ============================================================================
-- Summary of Key Improvements
-- ============================================================================
-- 1. All pickle BLOBs removed - data now in normalized columns
-- 2. Strategic indexes on:
--    - Foreign keys (owner_id, user_id, project_id)
--    - Filter columns (is_archived, phase, status, subscription_tier)
--    - Time-based columns (timestamp, created_at, updated_at)
--    - Composite indexes for common multi-column queries
-- 3. Arrays moved to separate tables (requirements, tech_stack, team_members, etc.)
-- 4. Large text fields (conversation, specs) in separate tables for lazy loading
-- 5. All complex dicts stored as JSON text for flexibility
-- 6. GitHub Sponsors tracking for monetization integration
-- ============================================================================
