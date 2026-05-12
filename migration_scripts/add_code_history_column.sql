-- Add code history tracking to projects table
-- This migration adds support for tracking the history of code changes in projects

-- Add code_history column to projects table for storing version history
ALTER TABLE projects ADD COLUMN code_history TEXT;

-- Create index for efficient queries on code history
CREATE INDEX IF NOT EXISTS idx_projects_code_history ON projects(code_history);
