-- Migration: Add GitHub import related tables
-- Tracks GitHub repository imports and sync information

BEGIN TRANSACTION;

-- Project files table - stores project files from GitHub imports
CREATE TABLE IF NOT EXISTS project_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    content_hash TEXT,
    last_modified TIMESTAMP,
    tracked BOOLEAN DEFAULT 1,

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    UNIQUE(project_id, file_path)
);

CREATE INDEX IF NOT EXISTS idx_project_files_project ON project_files(project_id);
CREATE INDEX IF NOT EXISTS idx_project_files_tracked ON project_files(tracked);

-- Repository metadata table - stores GitHub repository information
CREATE TABLE IF NOT EXISTS repository_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    repo_url TEXT NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    default_branch TEXT DEFAULT 'main',
    description TEXT,
    is_private BOOLEAN DEFAULT 0,
    imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,
    sync_status TEXT DEFAULT 'pending',  -- 'pending', 'syncing', 'completed', 'failed'
    metadata TEXT,  -- JSON for extensibility

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    UNIQUE(project_id, repo_url)
);

CREATE INDEX IF NOT EXISTS idx_repository_metadata_project ON repository_metadata(project_id);
CREATE INDEX IF NOT EXISTS idx_repository_metadata_sync_status ON repository_metadata(sync_status);

-- Code validation results table - stores code validation history
CREATE TABLE IF NOT EXISTS code_validation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    validation_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,  -- 'success', 'error', 'warning'
    error_count INTEGER DEFAULT 0,
    warning_count INTEGER DEFAULT 0,
    error_message TEXT,
    details TEXT,  -- JSON for extensibility

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_code_validation_project ON code_validation_results(project_id);
CREATE INDEX IF NOT EXISTS idx_code_validation_status ON code_validation_results(status);

COMMIT;
