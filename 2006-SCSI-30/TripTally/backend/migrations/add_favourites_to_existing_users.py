"""
Migration script to add a "Favourites" list to all existing users who don't have one.

Run this script after activating your virtual environment:
    python migrations/add_favourites_to_existing_users.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.begin() as conn:
        print("Starting migration to add Favourites lists...")
        
        # Get all users (join with accounts table to get email and username)
        result = conn.execute(text("""
            SELECT u.id, a.email, a.username 
            FROM users u 
            JOIN accounts a ON u.id = a.id
        """))
        users = result.fetchall()
        
        print(f"Found {len(users)} users")
        
        favourites_created = 0
        
        for user in users:
            user_id = user[0]
            email = user[1]
            username = user[2]
            
            # Check if user already has a "Favourites" list
            check_result = conn.execute(
                text("SELECT COUNT(*) FROM saved_lists WHERE user_id = :user_id AND name = 'Favourites'"),
                {"user_id": user_id}
            )
            count = check_result.scalar()
            
            if count == 0:
                # Create Favourites list for this user
                conn.execute(
                    text("""
                        INSERT INTO saved_lists (user_id, name, created_at, updated_at)
                        VALUES (:user_id, 'Favourites', :now, :now)
                    """),
                    {
                        "user_id": user_id,
                        "now": datetime.utcnow()
                    }
                )
                print(f"✓ Created 'Favourites' list for user {username} (ID: {user_id})")
                favourites_created += 1
            else:
                print(f"⊘ User {username} (ID: {user_id}) already has a 'Favourites' list")
        
        print(f"\n✅ Migration completed successfully!")
        print(f"Created {favourites_created} new 'Favourites' lists")
        print(f"Skipped {len(users) - favourites_created} users who already had 'Favourites'")

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
