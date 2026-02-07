"""
Database migration to add saved places functionality and user location fields.

This migration:
1. Adds home and work location columns to users table
2. Creates saved_lists table for user's saved lists
3. Creates saved_places table for places within lists

Run this script after activating your virtual environment:
    python migrations/add_saved_places_and_user_locations.py
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.begin() as conn:
        print("Starting migration...")
        
        # 1. Add location columns to users table
        print("Adding location columns to users table...")
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS home_latitude FLOAT,
            ADD COLUMN IF NOT EXISTS home_longitude FLOAT,
            ADD COLUMN IF NOT EXISTS home_address VARCHAR(255),
            ADD COLUMN IF NOT EXISTS work_latitude FLOAT,
            ADD COLUMN IF NOT EXISTS work_longitude FLOAT,
            ADD COLUMN IF NOT EXISTS work_address VARCHAR(255)
        """))
        print("✓ User location columns added")
        
        # 2. Create saved_lists table
        print("Creating saved_lists table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS saved_lists (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ saved_lists table created")
        
        # 3. Create saved_places table
        print("Creating saved_places table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS saved_places (
                id SERIAL PRIMARY KEY,
                list_id INTEGER NOT NULL REFERENCES saved_lists(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                address VARCHAR(500) NOT NULL,
                latitude FLOAT NOT NULL,
                longitude FLOAT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ saved_places table created")
        
        # 4. Create indexes for better performance
        print("Creating indexes...")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_saved_lists_user_id 
            ON saved_lists(user_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_saved_places_list_id 
            ON saved_places(list_id)
        """))
        print("✓ Indexes created")
        
        print("\n✅ Migration completed successfully!")
        print("\nNew tables:")
        print("  - saved_lists (id, user_id, name, created_at, updated_at)")
        print("  - saved_places (id, list_id, name, address, latitude, longitude, created_at)")
        print("\nNew columns in users table:")
        print("  - home_latitude, home_longitude, home_address")
        print("  - work_latitude, work_longitude, work_address")

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
