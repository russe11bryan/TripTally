from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.db import Base, engine
from app.adapters import tables
from app.api.location_routes import router as location_router
from app.api.user_routes import router as user_router
from app.api.auth_routes import router as auth_router
from app.api.reports import router as reports_router
from app.api.suggestions import router as suggestions_router
from app.api.traffic_alerts import router as traffic_alerts_router
from app.api.saved import router as saved_router
from app.api.traffic_camera_routes import router as traffic_camera_router
# Alternative simple implementation:
# from app.api.simple_camera_routes import router as traffic_camera_router
from app.api.route_optimization_routes import router as route_optimization_router
from app.api.departure_optimization_routes import router as departure_optimization_router
from app.api.metrics_routes import router as metrics_router
from app.routers.transport_metrics import router as transport_metrics_router
from app.api.user_route_api import router as user_route_router
from app.routers import maps_router

app = FastAPI(
    title="TripTally API",
    description="Route planning and travel management API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

# Include API routers - YOUR routes + TEAMMATE's maps router
app.include_router(location_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(reports_router)
app.include_router(suggestions_router)
app.include_router(traffic_alerts_router)
app.include_router(saved_router)
app.include_router(traffic_camera_router)
app.include_router(route_optimization_router)
app.include_router(departure_optimization_router)
app.include_router(metrics_router)
app.include_router(transport_metrics_router)
app.include_router(saved_router)
app.include_router(user_route_router)
app.include_router(maps_router.router, prefix="")

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

@app.get("/healthz")
def health():
    return {"status": "ok"}
