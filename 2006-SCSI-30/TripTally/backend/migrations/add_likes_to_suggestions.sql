-- Migration: Add likes column to suggestions table
-- Date: 2025-10-28
-- Description: Adds likes counter to track user engagement with suggestions

-- Add likes column with default value of 0
ALTER TABLE suggestions 
ADD COLUMN IF NOT EXISTS likes INTEGER DEFAULT 0 NOT NULL;

-- Create index for sorting by likes
CREATE INDEX IF NOT EXISTS idx_suggestions_likes 
ON suggestions(likes DESC);
