"""
FastAPI main application entry point.
Initializes the database and includes all API routers.
"""
from fastapi import FastAPI
from app.core.db import Base, engine
from app.adapters import tables  # Import all table definitions
from app.api.location_routes import router as location_router
from app.api.user_routes import router as user_router
from app.api import maps_router

app = FastAPI(
    title="TripTally API",
    description="Route planning and travel management API",
    version="1.0.0"
)

app.include_router(maps_router.router)
# Create all database tables on startup
Base.metadata.create_all(bind=engine)

# Include API routers
# app.include_router(location_router)
# app.include_router(user_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to TripTally API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}



