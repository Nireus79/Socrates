-- ============================================================================
-- Socrates AI Database Schema V2 - Normalized Design
-- Replaces pickle BLOBs with normalized, queryable tables
-- ============================================================================

-- Main projects table (extracted from pickle BLOB)
CREATE TABLE IF NOT EXISTS projects_v2 (
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

    FOREIGN KEY (owner) REFERENCES users_v2(username)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects_v2(owner);
CREATE INDEX IF NOT EXISTS idx_projects_phase ON projects_v2(phase);
CREATE INDEX IF NOT EXISTS idx_projects_archived ON projects_v2(is_archived);
CREATE INDEX IF NOT EXISTS idx_projects_updated ON projects_v2(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_projects_owner_archived ON projects_v2(owner, is_archived);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects_v2(status);

-- Project requirements (normalized from array)
CREATE TABLE IF NOT EXISTS project_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    requirement TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_project_requirements_project ON project_requirements(project_id);

-- Project tech stack (normalized from array)
CREATE TABLE IF NOT EXISTS project_tech_stack (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    technology TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_project_tech_stack_project ON project_tech_stack(project_id);

-- Project constraints (normalized from array)
CREATE TABLE IF NOT EXISTS project_constraints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    constraint_text TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
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

    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_conversation_project_timestamp ON conversation_history(project_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_project ON conversation_history(project_id);

-- Team members (normalized from array)
CREATE TABLE IF NOT EXISTS team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    skills TEXT,  -- JSON array
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(project_id, username),
    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE,
    FOREIGN KEY (username) REFERENCES users_v2(username)
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
    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
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
    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
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

    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
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

    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
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

    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_project ON analytics_metrics(project_id);

-- Pending questions (normalized from array)
CREATE TABLE IF NOT EXISTS pending_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    question_data TEXT NOT NULL,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sort_order INTEGER DEFAULT 0,

    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_pending_questions_project ON pending_questions(project_id);

-- Project notes (separate table)
CREATE TABLE IF NOT EXISTS project_notes_v2 (
    note_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT,
    content TEXT,
    note_type TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_project_notes_project ON project_notes_v2(project_id);
CREATE INDEX IF NOT EXISTS idx_project_notes_created ON project_notes_v2(created_at DESC);

-- Users table (normalized)
CREATE TABLE IF NOT EXISTS users_v2 (
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
CREATE INDEX IF NOT EXISTS idx_users_archived ON users_v2(is_archived);
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users_v2(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users_v2(subscription_status);
CREATE INDEX IF NOT EXISTS idx_users_subscription ON users_v2(subscription_tier, subscription_status);

-- Question effectiveness tracking
CREATE TABLE IF NOT EXISTS question_effectiveness_v2 (
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
    FOREIGN KEY (user_id) REFERENCES users_v2(username)
);
CREATE INDEX IF NOT EXISTS idx_question_effectiveness_user ON question_effectiveness_v2(user_id);
CREATE INDEX IF NOT EXISTS idx_question_effectiveness_template ON question_effectiveness_v2(question_template_id);

-- Behavior patterns
CREATE TABLE IF NOT EXISTS behavior_patterns_v2 (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    pattern_data TEXT NOT NULL,  -- JSON
    frequency INTEGER DEFAULT 1,
    learned_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    UNIQUE(user_id, pattern_type),
    FOREIGN KEY (user_id) REFERENCES users_v2(username)
);
CREATE INDEX IF NOT EXISTS idx_behavior_patterns_user ON behavior_patterns_v2(user_id);
CREATE INDEX IF NOT EXISTS idx_behavior_patterns_type ON behavior_patterns_v2(pattern_type);

-- Knowledge documents
CREATE TABLE IF NOT EXISTS knowledge_documents_v2 (
    id TEXT PRIMARY KEY,
    project_id TEXT,  -- NULL for global knowledge
    user_id TEXT NOT NULL,
    title TEXT,
    content TEXT,
    source TEXT,
    document_type TEXT DEFAULT 'document',
    uploaded_at TIMESTAMP NOT NULL,

    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users_v2(username)
);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_project ON knowledge_documents_v2(project_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_user ON knowledge_documents_v2(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_type ON knowledge_documents_v2(document_type);

-- LLM Provider configurations
CREATE TABLE IF NOT EXISTS llm_provider_configs_v2 (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    config_data TEXT NOT NULL,  -- JSON
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    UNIQUE(user_id, provider),
    FOREIGN KEY (user_id) REFERENCES users_v2(username)
);
CREATE INDEX IF NOT EXISTS idx_llm_configs_user ON llm_provider_configs_v2(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_configs_provider ON llm_provider_configs_v2(provider);

-- API keys
CREATE TABLE IF NOT EXISTS api_keys_v2 (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    encrypted_key TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    last_used_at TIMESTAMP,

    UNIQUE(user_id, provider),
    FOREIGN KEY (user_id) REFERENCES users_v2(username)
);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys_v2(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_provider ON api_keys_v2(provider);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_provider ON api_keys_v2(user_id, provider);

-- LLM usage tracking
CREATE TABLE IF NOT EXISTS llm_usage_v2 (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0,
    timestamp TIMESTAMP NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users_v2(username)
);
CREATE INDEX IF NOT EXISTS idx_llm_usage_user ON llm_usage_v2(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_timestamp ON llm_usage_v2(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_llm_usage_user_timestamp ON llm_usage_v2(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_llm_usage_provider ON llm_usage_v2(provider);

-- Refresh tokens for JWT authentication
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users_v2(username) ON DELETE CASCADE
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

    FOREIGN KEY (user_id) REFERENCES users_v2(username) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_api_tokens_user ON api_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_api_tokens_expires ON api_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_api_tokens_revoked ON api_tokens(revoked_at);

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
-- ============================================================================
