#!/usr/bin/env python3
"""
Apply database migration to add likes column to suggestions table.
"""

import sys
sys.path.insert(0, '/Users/russellbryan/Documents/GitHub/SC2006Proj/2006-priv-repo/triptally/TripTally/backend')

from sqlalchemy import create_engine, text
from app.core.config import settings

def apply_migration():
    """Add likes column to suggestions table"""
    engine = create_engine(settings.DATABASE_URL)
    
    migration_sql = """
    -- Add likes column with default value of 0
    ALTER TABLE suggestions 
    ADD COLUMN IF NOT EXISTS likes INTEGER DEFAULT 0 NOT NULL;

    -- Create index for sorting by likes
    CREATE INDEX IF NOT EXISTS idx_suggestions_likes 
    ON suggestions(likes DESC);
    """
    
    try:
        with engine.connect() as conn:
            # Execute the migration
            conn.execute(text(migration_sql))
            conn.commit()
            print("✅ Likes column added successfully!")
            
            # Verify the column exists
            result = conn.execute(text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'suggestions'
                ORDER BY ordinal_position;
            """))
            
            print("\n📊 Updated suggestions table structure:")
            print("-" * 70)
            for row in result:
                default = f" DEFAULT {row[2]}" if row[2] else ""
                print(f"  {row[0]:<20} {row[1]}{default}")
            print("-" * 70)
            
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Adding likes column to suggestions table...")
    print(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print()
    apply_migration()
