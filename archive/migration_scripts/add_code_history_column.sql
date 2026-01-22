-- ============================================================================
-- Migration: Add code_history column to projects table
-- Purpose: Persist generated code history to the database
-- ============================================================================

-- Add code_history column to store JSON array of generated code with metadata
ALTER TABLE projects ADD COLUMN code_history TEXT;

-- Update schema version or metadata if needed
-- This column stores JSON like:
-- [
--   {
--     "id": "gen_1234567890",
--     "code": "...",
--     "timestamp": "2024-01-22T10:00:00+00:00",
--     "language": "python",
--     "explanation": "...",
--     "lines": 42,
--     "file_path": "...",
--     "filename": "generated_gen_1234567890.py"
--   }
-- ]
