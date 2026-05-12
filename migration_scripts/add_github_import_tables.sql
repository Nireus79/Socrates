-- Create tables for GitHub repository import functionality
-- This migration sets up support for importing projects from GitHub

-- Create table for tracking imported project files
CREATE TABLE IF NOT EXISTS project_files (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_content TEXT,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE(project_id, file_path)
);

-- Create table for repository metadata
CREATE TABLE IF NOT EXISTS repository_metadata (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL UNIQUE,
    repository_url TEXT NOT NULL,
    repository_name TEXT,
    branch TEXT DEFAULT 'main',
    last_sync_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Create table for code validation results
CREATE TABLE IF NOT EXISTS code_validation_results (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    validation_type TEXT NOT NULL,
    result TEXT,
    severity TEXT CHECK (severity IN ('info', 'warning', 'error')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_project_files_project_id ON project_files(project_id);
CREATE INDEX IF NOT EXISTS idx_project_files_file_path ON project_files(file_path);
CREATE INDEX IF NOT EXISTS idx_repository_metadata_project_id ON repository_metadata(project_id);
CREATE INDEX IF NOT EXISTS idx_code_validation_results_project_id ON code_validation_results(project_id);
CREATE INDEX IF NOT EXISTS idx_code_validation_results_severity ON code_validation_results(severity);
