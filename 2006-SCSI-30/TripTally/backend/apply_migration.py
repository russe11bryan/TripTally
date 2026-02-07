#!/usr/bin/env python3
"""
Apply database migrations for technical_reports table
Adds category and added_by columns
"""

import sys
sys.path.insert(0, '/Users/russellbryan/Documents/GitHub/SC2006Proj/2006-priv-repo/triptally/TripTally/backend')

from sqlalchemy import create_engine, text
from app.core.config import settings

def apply_migration():
    """Apply the migration to add category and added_by columns"""
    engine = create_engine(settings.DATABASE_URL)
    
    migration_sql = """
    -- Add category column if it doesn't exist
    DO $$ 
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='technical_reports' AND column_name='category'
        ) THEN
            ALTER TABLE technical_reports ADD COLUMN category VARCHAR(100) DEFAULT '';
        END IF;
    END $$;
    
    -- Add added_by column if it doesn't exist
    DO $$ 
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='technical_reports' AND column_name='added_by'
        ) THEN
            ALTER TABLE technical_reports ADD COLUMN added_by INTEGER;
        END IF;
    END $$;
    
    -- Create index on category if it doesn't exist
    CREATE INDEX IF NOT EXISTS idx_technical_reports_category 
    ON technical_reports(category);
    
    -- Create index on added_by if it doesn't exist
    CREATE INDEX IF NOT EXISTS idx_technical_reports_added_by 
    ON technical_reports(added_by);
    """
    
    try:
        with engine.connect() as conn:
            # Execute the migration
            conn.execute(text(migration_sql))
            conn.commit()
            print("✅ Migration applied successfully!")
            
            # Verify the columns exist
            result = conn.execute(text("""
                SELECT column_name, data_type, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'technical_reports'
                ORDER BY ordinal_position;
            """))
            
            print("\n📊 Current technical_reports table structure:")
            print("-" * 60)
            for row in result:
                length = f"({row[2]})" if row[2] else ""
                print(f"  {row[0]:<20} {row[1]}{length}")
            print("-" * 60)
            
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Applying migration to add category and added_by columns...")
    print(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print()
    apply_migration()
