"""
Migration: Update traffic_alerts table structure
- Remove description column
- Replace location with latitude, longitude, location_name
- Add reported_by column
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Update traffic_alerts table structure."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'traffic_alerts'
                );
            """))
            table_exists = result.scalar()
            
            if table_exists:
                print("Updating existing traffic_alerts table...")
                
                # Check if old columns exist and drop them
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'traffic_alerts' 
                    AND column_name IN ('location', 'description');
                """))
                old_columns = [row[0] for row in result]
                
                if 'description' in old_columns:
                    conn.execute(text("ALTER TABLE traffic_alerts DROP COLUMN IF EXISTS description;"))
                    print("  - Dropped description column")
                
                if 'location' in old_columns:
                    conn.execute(text("ALTER TABLE traffic_alerts DROP COLUMN IF EXISTS location;"))
                    print("  - Dropped location column")
                
                # Add new columns if they don't exist
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'traffic_alerts';
                """))
                existing_columns = [row[0] for row in result]
                
                if 'latitude' not in existing_columns:
                    conn.execute(text("ALTER TABLE traffic_alerts ADD COLUMN latitude FLOAT;"))
                    print("  - Added latitude column")
                
                if 'longitude' not in existing_columns:
                    conn.execute(text("ALTER TABLE traffic_alerts ADD COLUMN longitude FLOAT;"))
                    print("  - Added longitude column")
                
                if 'location_name' not in existing_columns:
                    conn.execute(text("ALTER TABLE traffic_alerts ADD COLUMN location_name VARCHAR(200);"))
                    print("  - Added location_name column")
                
                if 'reported_by' not in existing_columns:
                    conn.execute(text("ALTER TABLE traffic_alerts ADD COLUMN reported_by INTEGER;"))
                    print("  - Added reported_by column")
                
                print("Migration completed successfully!")
            else:
                print("traffic_alerts table does not exist yet. It will be created on next server start.")
            
            # Commit transaction
            trans.commit()
            
        except Exception as e:
            trans.rollback()
            print(f"Error during migration: {e}")
            raise

if __name__ == "__main__":
    run_migration()
