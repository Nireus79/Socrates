-- Migration: Add code_history column to projects table
-- Tracks history of generated code with metadata

BEGIN TRANSACTION;

-- Add code_history column if it doesn't exist
-- Stores JSON array of code generation history
ALTER TABLE projects ADD COLUMN code_history TEXT DEFAULT NULL;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_projects_code_history ON projects(project_id) WHERE code_history IS NOT NULL;

COMMIT;
