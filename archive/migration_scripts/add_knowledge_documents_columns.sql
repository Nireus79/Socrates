-- Migration: Add file_path and file_size columns to knowledge_documents table
-- Purpose: Support file tracking and storage management for knowledge documents
-- Date: 2026-01-21

-- Check if columns already exist before adding them
PRAGMA table_info(knowledge_documents);

-- Add file_path column if it doesn't exist
ALTER TABLE knowledge_documents ADD COLUMN file_path TEXT;

-- Add file_size column if it doesn't exist
ALTER TABLE knowledge_documents ADD COLUMN file_size INTEGER;

-- Verify the columns were added
PRAGMA table_info(knowledge_documents);
