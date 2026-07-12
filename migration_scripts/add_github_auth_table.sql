-- Migration: Add GitHub authentication table for real-time sponsorship verification
-- Purpose: Store encrypted GitHub Personal Access Tokens and verification status
-- Date: 2026-07-12

-- Create github_auth table for storing GitHub authentication data
CREATE TABLE IF NOT EXISTS github_auth (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    github_username TEXT NOT NULL UNIQUE,
    github_user_id INTEGER,
    github_token TEXT NOT NULL,  -- ENCRYPTED with SOCRATES_ENCRYPTION_KEY
    token_scopes TEXT,  -- Comma-separated scopes (user,repo,etc.)
    token_created_at TIMESTAMP,
    token_expires_at TIMESTAMP,  -- For fine-grained tokens with expiry
    last_verified_at TIMESTAMP,  -- Last time token was verified with GitHub API
    verification_status TEXT DEFAULT 'active',  -- active, expired, revoked, invalid
    verification_error TEXT,  -- Error message if verification failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

-- Create indexes for GitHub auth queries
CREATE INDEX IF NOT EXISTS idx_github_auth_username ON github_auth(username);
CREATE INDEX IF NOT EXISTS idx_github_auth_github_username ON github_auth(github_username);
CREATE INDEX IF NOT EXISTS idx_github_auth_verified ON github_auth(verification_status, last_verified_at);
CREATE INDEX IF NOT EXISTS idx_github_auth_status ON github_auth(verification_status);

-- Add verification columns to sponsorships table for API verification tracking
ALTER TABLE sponsorships ADD COLUMN verified_at TIMESTAMP;
ALTER TABLE sponsorships ADD COLUMN verification_status TEXT DEFAULT 'pending';
ALTER TABLE sponsorships ADD COLUMN api_verification_error TEXT;
ALTER TABLE sponsorships ADD COLUMN github_token_used BOOLEAN DEFAULT 0;

-- Create indexes on sponsorship verification columns
CREATE INDEX IF NOT EXISTS idx_sponsorships_verified ON sponsorships(verification_status, verified_at DESC);
CREATE INDEX IF NOT EXISTS idx_sponsorships_user_verified ON sponsorships(username, verification_status) WHERE verification_status = 'verified';
