-- Migration: Create user_likes table to track who liked which suggestions
-- Date: 2025-10-28
-- Description: Creates junction table to prevent duplicate likes and track user engagement

-- Create user_likes table
CREATE TABLE IF NOT EXISTS user_likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    suggestion_id INTEGER NOT NULL,
    created_at VARCHAR(50),
    UNIQUE(user_id, suggestion_id),  -- Prevent duplicate likes
    FOREIGN KEY (suggestion_id) REFERENCES suggestions(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_likes_user_id 
ON user_likes(user_id);

CREATE INDEX IF NOT EXISTS idx_user_likes_suggestion_id 
ON user_likes(suggestion_id);
