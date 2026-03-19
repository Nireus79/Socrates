-- Migration: Add GitHub import related tables
-- Tracks GitHub repository imports and sync information

BEGIN TRANSACTION;

-- GitHub import metadata table
CREATE TABLE IF NOT EXISTS github_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    github_repo_url TEXT NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,
    sync_status TEXT DEFAULT 'pending',  -- 'pending', 'syncing', 'completed', 'failed'
    metadata TEXT,  -- JSON for extensibility

    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    UNIQUE(project_id, github_repo_url)
);

CREATE INDEX IF NOT EXISTS idx_github_imports_project ON github_imports(project_id);
CREATE INDEX IF NOT EXISTS idx_github_imports_sync_status ON github_imports(sync_status);
CREATE INDEX IF NOT EXISTS idx_github_imports_last_synced ON github_imports(last_synced_at DESC);

-- GitHub file tracking table
CREATE TABLE IF NOT EXISTS github_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    last_modified TIMESTAMP,
    content_hash TEXT,
    tracked BOOLEAN DEFAULT 1,

    FOREIGN KEY (import_id) REFERENCES github_imports(id) ON DELETE CASCADE,
    UNIQUE(import_id, file_path)
);

CREATE INDEX IF NOT EXISTS idx_github_files_import ON github_files(import_id);
CREATE INDEX IF NOT EXISTS idx_github_files_tracked ON github_files(tracked);

-- GitHub sync log table
CREATE TABLE IF NOT EXISTS github_sync_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_id INTEGER NOT NULL,
    sync_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,  -- 'success', 'error', 'partial'
    files_added INTEGER DEFAULT 0,
    files_modified INTEGER DEFAULT 0,
    files_deleted INTEGER DEFAULT 0,
    error_message TEXT,
    details TEXT,  -- JSON for extensibility

    FOREIGN KEY (import_id) REFERENCES github_imports(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_sync_logs_import ON github_sync_logs(import_id);
CREATE INDEX IF NOT EXISTS idx_github_sync_logs_timestamp ON github_sync_logs(sync_timestamp DESC);

COMMIT;
