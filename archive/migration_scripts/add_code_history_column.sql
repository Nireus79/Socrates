-- Migration: Add code_history column to projects table
-- Purpose: Store code generation history and evolution tracking

ALTER TABLE projects ADD COLUMN code_history TEXT DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_projects_code_history ON projects(code_history);
