-- PostgreSQL Migration: Add category and added_by columns to technical_reports table
-- Date: 2025-10-27
-- Description: Adds category and added_by fields to technical_reports for better categorization and tracking

-- Add category column to technical_reports table
ALTER TABLE technical_reports 
ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT '';

-- Add added_by column to technical_reports table (foreign key to users)
ALTER TABLE technical_reports 
ADD COLUMN IF NOT EXISTS added_by INTEGER;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_technical_reports_category 
ON technical_reports(category);

CREATE INDEX IF NOT EXISTS idx_technical_reports_added_by 
ON technical_reports(added_by);

-- Verify the changes
\d technical_reports
