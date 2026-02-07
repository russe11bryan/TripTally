-- Migration: Create suggestions table
-- Date: 2025-10-28
-- Description: Creates table for user suggestions/recommendations with title, category, description, and added_by fields

-- Create suggestions table
CREATE TABLE IF NOT EXISTS suggestions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    added_by VARCHAR(100),
    created_at VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending' NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_suggestions_status 
ON suggestions(status);

CREATE INDEX IF NOT EXISTS idx_suggestions_category 
ON suggestions(category);

CREATE INDEX IF NOT EXISTS idx_suggestions_created_at 
ON suggestions(created_at);
