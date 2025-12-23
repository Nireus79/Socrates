-- Add claude_auth_method column to users_v2 table if it doesn't exist
-- This column tracks whether a user authenticates via API key or subscription

ALTER TABLE users_v2 ADD COLUMN claude_auth_method TEXT DEFAULT 'api_key';
