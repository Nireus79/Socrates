-- Add file tracking columns to knowledge_documents table
-- This migration adds support for tracking which files knowledge entries came from

-- Add file_path column for tracking document source
ALTER TABLE knowledge_documents ADD COLUMN file_path TEXT;

-- Add file_size column for tracking document size
ALTER TABLE knowledge_documents ADD COLUMN file_size INTEGER;

-- Add indexes for efficient queries on file tracking
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_file_path ON knowledge_documents(file_path);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_file_size ON knowledge_documents(file_size);
