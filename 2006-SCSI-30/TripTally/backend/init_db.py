"""
Database initialization script.
Run this to create all database tables.
"""
from app.core.db import Base, engine
from app.adapters import tables  # noqa: F401 ensures all models are imported for metadata


def init_db():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully!")
    
    # Print all created tables
    print("\nCreated tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


def drop_all_tables():
    """Drop all database tables. USE WITH CAUTION!"""
    print("⚠️  WARNING: Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    print("✓ All tables dropped!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        response = input("Are you sure you want to drop all tables? (yes/no): ")
        if response.lower() == "yes":
            drop_all_tables()
            init_db()
        else:
            print("Cancelled.")
    else:
        init_db()
