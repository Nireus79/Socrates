-- Migration: Add testing_mode_enabled_at column to users table
-- Purpose: Track when testing mode was activated (for 24-hour auto-expiration)
-- This column stores the timestamp when testing mode was enabled
-- Used by is_testing_mode_active() to check if 24 hours have passed

ALTER TABLE users ADD COLUMN testing_mode_enabled_at TIMESTAMP;
