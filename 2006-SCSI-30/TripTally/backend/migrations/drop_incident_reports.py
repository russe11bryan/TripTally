"""
Migration: Drop incident_reports table
We're now using traffic_alerts table for all incident reports.
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Drop incident_reports table."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'incident_reports'
                );
            """))
            table_exists = result.scalar()
            
            if table_exists:
                print("Dropping incident_reports table...")
                conn.execute(text("DROP TABLE IF EXISTS incident_reports CASCADE;"))
                print("✅ incident_reports table dropped successfully!")
            else:
                print("incident_reports table does not exist. Nothing to do.")
            
            trans.commit()
            
        except Exception as e:
            trans.rollback()
            print(f"Error during migration: {e}")
            raise

if __name__ == "__main__":
    run_migration()
