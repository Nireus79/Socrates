-- Migration: Add file tracking columns to knowledge_documents table
-- Purpose: Track file path and size information for knowledge documents

ALTER TABLE knowledge_documents ADD COLUMN file_path TEXT DEFAULT NULL;
ALTER TABLE knowledge_documents ADD COLUMN file_size INTEGER DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_file_path ON knowledge_documents(file_path);
