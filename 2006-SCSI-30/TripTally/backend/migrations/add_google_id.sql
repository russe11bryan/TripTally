-- Migration: Add google_id column to users table
-- This allows users to authenticate via Google Sign-In

ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255) UNIQUE;
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
