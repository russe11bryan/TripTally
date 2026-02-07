# Database Migrations

This directory contains SQL migration scripts for database schema changes.

## Available Migrations

1. `add_google_id.sql` - Adds google_id column to users table for Google OAuth
2. `add_technical_report_columns.sql` - Adds category and added_by columns to technical_reports table

## How to Apply Migrations

### For SQLite (Development)
```bash
cd backend
sqlite3 app.db < migrations/add_technical_report_columns.sql
```

### For PostgreSQL (Production)
```bash
psql -d triptally -f migrations/add_technical_report_columns.sql
```

## Migration Workflow

1. Create a new `.sql` file with a descriptive name
2. Add SQL statements with `IF NOT EXISTS` clauses for safety
3. Document the migration at the top of the file
4. Test the migration on a copy of the database first
5. Apply to development database
6. Apply to production database when ready

## Auto-creation via SQLAlchemy

Note: The FastAPI app uses `Base.metadata.create_all()` on startup, which will automatically create tables if they don't exist. However, it won't automatically alter existing tables. For schema changes to existing tables, you need to:

1. Update the model in `app/models/`
2. Update the table in `app/adapters/tables.py`
3. Create a migration SQL file (this directory)
4. Apply the migration manually

## Future: Alembic Integration

For more robust migration management, consider setting up Alembic:
```bash
pip install alembic
alembic init alembic
# Configure alembic.ini and env.py
alembic revision --autogenerate -m "description"
alembic upgrade head
```
