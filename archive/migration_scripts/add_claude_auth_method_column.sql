-- Migration: Add claude_auth_method column to users table
-- Purpose: Support Claude API authentication method tracking

ALTER TABLE users ADD COLUMN claude_auth_method TEXT DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_users_claude_auth ON users(claude_auth_method);
