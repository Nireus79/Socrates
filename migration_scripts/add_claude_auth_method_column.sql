-- Add Claude authentication method column to users table
-- This migration adds support for Claude-based authentication

-- Add claude_auth_method column if it doesn't exist
ALTER TABLE users ADD COLUMN claude_auth_method TEXT DEFAULT 'none' CHECK (claude_auth_method IN ('none', 'api_key', 'session'));

-- Add index for efficient lookups by auth method
CREATE INDEX IF NOT EXISTS idx_users_claude_auth_method ON users(claude_auth_method);
