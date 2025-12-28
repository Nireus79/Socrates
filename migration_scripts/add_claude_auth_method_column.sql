-- Add claude_auth_method column to users table if it doesn't exist
-- This column tracks whether a user authenticates via API key or subscription

ALTER TABLE users ADD COLUMN claude_auth_method TEXT DEFAULT 'api_key';
