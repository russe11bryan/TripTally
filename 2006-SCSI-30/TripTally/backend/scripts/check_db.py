"""Simple DB connectivity check for the TripTally backend.

Run this from the backend folder:
    python scripts/check_db.py

It will print the effective DATABASE_URL (with password redacted) and try to connect using SQLAlchemy.
"""
from urllib.parse import urlparse
import sys
from app.core.config import settings
from app.core.db import engine

def redact_url(url: str) -> str:
    try:
        p = urlparse(url)
        if p.password:
            netloc = f"{p.username}:***@{p.hostname}:{p.port}"
        else:
            netloc = p.netloc
        return f"{p.scheme}://{netloc}{p.path}"
    except Exception:
        return "<invalid url>"

def main():
    print("Using DATABASE_URL:", redact_url(settings.DATABASE_URL))
    try:
        print("Attempting to connect to DB...")
        with engine.connect() as conn:
            res = conn.execute("SELECT 1")
            row = res.fetchone()
            if row and row[0] == 1:
                print("OK: connected to DB (SELECT 1 returned 1)")
            else:
                print("Connected but unexpected SELECT 1 result:", row)
    except Exception as e:
        print("DB connection failed:", type(e).__name__, str(e))
        sys.exit(2)

if __name__ == '__main__':
    main()
