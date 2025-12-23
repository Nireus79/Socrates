-- Migration: Add GitHub Import and Code Validation Support
-- This script creates tables for:
-- 1. Storing project files (generated or imported code)
-- 2. Storing repository metadata (for GitHub projects)
-- 3. Storing code validation results

-- ============================================================================
-- Table 1: project_files - Stores actual project code files
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    file_path TEXT NOT NULL,           -- Relative path (e.g., "src/main.py")
    content TEXT NOT NULL,             -- File contents
    language TEXT,                     -- Python, JavaScript, Java, etc.
    file_size INTEGER DEFAULT 0,       -- Size in bytes
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE,
    UNIQUE (project_id, file_path)     -- One entry per file per project
);

CREATE INDEX IF NOT EXISTS idx_project_files_project
    ON project_files(project_id);

CREATE INDEX IF NOT EXISTS idx_project_files_language
    ON project_files(language);

CREATE INDEX IF NOT EXISTS idx_project_files_path
    ON project_files(project_id, file_path);

-- ============================================================================
-- Table 2: repository_metadata - Stores GitHub repository information
-- ============================================================================
CREATE TABLE IF NOT EXISTS repository_metadata (
    project_id TEXT PRIMARY KEY,
    repository_url TEXT NOT NULL,
    repository_owner TEXT,
    repository_name TEXT,
    repository_description TEXT,
    primary_language TEXT,
    languages TEXT,                    -- JSON array of languages found
    file_count INTEGER DEFAULT 0,
    total_size_bytes INTEGER DEFAULT 0,
    has_tests BOOLEAN DEFAULT 0,
    has_readme BOOLEAN DEFAULT 0,
    default_branch TEXT DEFAULT 'main',
    imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_repo_metadata_url
    ON repository_metadata(repository_url);

CREATE INDEX IF NOT EXISTS idx_repo_metadata_owner
    ON repository_metadata(repository_owner);

CREATE INDEX IF NOT EXISTS idx_repo_metadata_language
    ON repository_metadata(primary_language);

-- ============================================================================
-- Table 3: code_validation_results - Stores validation run results
-- ============================================================================
CREATE TABLE IF NOT EXISTS code_validation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    validation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    overall_status TEXT NOT NULL,     -- "pass", "warning", or "fail"

    -- Syntax validation results
    syntax_valid BOOLEAN DEFAULT 1,
    syntax_issues_count INTEGER DEFAULT 0,

    -- Dependency validation results
    dependencies_valid BOOLEAN DEFAULT 1,
    dependency_issues_count INTEGER DEFAULT 0,

    -- Test execution results
    tests_found BOOLEAN DEFAULT 0,
    tests_passed INTEGER DEFAULT 0,
    tests_failed INTEGER DEFAULT 0,
    tests_skipped INTEGER DEFAULT 0,

    -- Detailed data (JSON format)
    validation_data TEXT,              -- JSON with full validation results
    recommendations TEXT,              -- JSON array of recommendations

    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_validation_project
    ON code_validation_results(project_id);

CREATE INDEX IF NOT EXISTS idx_validation_date
    ON code_validation_results(validation_date DESC);

CREATE INDEX IF NOT EXISTS idx_validation_status
    ON code_validation_results(overall_status);

-- ============================================================================
-- Add new fields to projects_v2 table (for repository context)
-- ============================================================================
ALTER TABLE projects_v2 ADD COLUMN repository_url TEXT;
ALTER TABLE projects_v2 ADD COLUMN repository_imported_at TIMESTAMP;

-- ============================================================================
-- Create indexes on new columns
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_projects_repository_url
    ON projects_v2(repository_url);

CREATE INDEX IF NOT EXISTS idx_projects_repository_imported_at
    ON projects_v2(repository_imported_at);

-- ============================================================================
-- Migration completed successfully
-- ============================================================================
