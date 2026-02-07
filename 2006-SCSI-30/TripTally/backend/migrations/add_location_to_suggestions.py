"""
Migration script to add location fields to suggestions table
Run this script to add latitude, longitude, and location_name columns
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.core.db import engine


def upgrade():
    """Add location columns to suggestions table"""
    with engine.connect() as conn:
        # Add latitude column
        conn.execute(text("""
            ALTER TABLE suggestions 
            ADD COLUMN IF NOT EXISTS latitude FLOAT DEFAULT NULL;
        """))
        
        # Add longitude column
        conn.execute(text("""
            ALTER TABLE suggestions 
            ADD COLUMN IF NOT EXISTS longitude FLOAT DEFAULT NULL;
        """))
        
        # Add location_name column
        conn.execute(text("""
            ALTER TABLE suggestions 
            ADD COLUMN IF NOT EXISTS location_name VARCHAR(200) DEFAULT NULL;
        """))
        
        conn.commit()
        print("✅ Successfully added location columns to suggestions table")


def downgrade():
    """Remove location columns from suggestions table"""
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE suggestions DROP COLUMN IF EXISTS latitude;"))
        conn.execute(text("ALTER TABLE suggestions DROP COLUMN IF EXISTS longitude;"))
        conn.execute(text("ALTER TABLE suggestions DROP COLUMN IF EXISTS location_name;"))
        conn.commit()
        print("✅ Successfully removed location columns from suggestions table")


if __name__ == "__main__":
    print("Running migration: Add location to suggestions")
    upgrade()
