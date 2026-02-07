#!/bin/bash
# Start the TripTally backend server

cd "$(dirname "$0")"

export PYTHONPATH="/Users/russellbryan/Documents/GitHub/SC2006Proj/2006-priv-repo/triptally/TripTally/backend:/Users/russellbryan/Documents/GitHub/SC2006Proj/2006-priv-repo/triptally/TripTally/backend/venv/lib/python3.12/site-packages"

echo "Starting TripTally Backend Server..."
echo "Backend will be available at: http://0.0.0.0:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""

python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
