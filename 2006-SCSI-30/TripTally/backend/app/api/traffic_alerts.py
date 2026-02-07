from __future__ import annotations

"""
API endpoints for traffic alerts (road incidents).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, timezone
import uuid
import os
import httpx
import math

from app.core.db import get_db
from app.adapters.sqlalchemy_traffic_alert_repo import SqlTrafficAlertRepo
from app.models.traffic_alert import TrafficAlert

# Singapore timezone (UTC+8)
SGT = timezone(timedelta(hours=8))

router = APIRouter(prefix="/traffic-alerts", tags=["traffic-alerts"])

# Google Maps API Key
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    Returns distance in meters.
    """
    R = 6371000  # Earth's radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


async def is_near_road(latitude: float, longitude: float, max_distance: float = 50) -> bool:
    """
    Check if coordinates are near a road using Google Roads API.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        max_distance: Maximum distance from road in meters (default 50m)
    
    Returns:
        True if location is near a road, False otherwise
    """
    if not GOOGLE_MAPS_API_KEY:
        # If no API key, skip validation (development mode)
        print("⚠️ No Google Maps API key found - skipping road validation")
        return True
    
    try:
        # Use Google Roads API - Snap to Roads endpoint
        url = "https://roads.googleapis.com/v1/snapToRoads"
        params = {
            "path": f"{latitude},{longitude}",
            "key": GOOGLE_MAPS_API_KEY,
            "interpolate": "false"
        }
        
        print(f"🔍 Checking if location ({latitude}, {longitude}) is near a road...")
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params)
            
            print(f"📡 Google Roads API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📦 API response data: {data}")
                
                # Check if any snapped points were returned
                if "snappedPoints" in data and len(data["snappedPoints"]) > 0:
                    snapped_point = data["snappedPoints"][0]
                    snapped_lat = snapped_point["location"]["latitude"]
                    snapped_lon = snapped_point["location"]["longitude"]
                    
                    # Calculate distance between original point and snapped point
                    distance = calculate_distance(latitude, longitude, snapped_lat, snapped_lon)
                    
                    print(f"📏 Distance to nearest road: {distance:.2f} meters (max allowed: {max_distance}m)")
                    
                    # If snapped point is within max_distance meters, it's near a road
                    is_near = distance <= max_distance
                    print(f"{'✅' if is_near else '❌'} Location is {'near' if is_near else 'too far from'} a road")
                    return is_near
                else:
                    # No snapped points means not near any road
                    print(f"❌ No roads found near location - rejecting report")
                    return False  # Strict: reject if no roads found
            else:
                # API error - check response body for details
                error_data = response.text
                print(f"❌ Google Roads API error {response.status_code}: {error_data}")
                
                # If API is not enabled or quota exceeded, be lenient
                if "PERMISSION_DENIED" in error_data or "API_KEY_INVALID" in error_data:
                    print(f"⚠️ Google Roads API not properly configured - allowing report")
                    return True  # Changed to be lenient
                
                # For other errors, be lenient
                return True
                
    except Exception as e:
        # Network error or timeout - be lenient and allow the report
        print(f"❌ Error checking road proximity: {e}")
        return True


# ============= Schemas =============
class TrafficAlertCreate(BaseModel):
    obstruction_type: str  # Traffic, Accident, Road Closure, Police
    latitude: float
    longitude: float
    location_name: Optional[str] = None
    reported_by: Optional[int] = None


class TrafficAlertResponse(BaseModel):
    id: int
    alert_id: str
    obstruction_type: str
    latitude: float
    longitude: float
    location_name: Optional[str]
    reported_by: Optional[int]
    delay_duration: Optional[float]
    status: str
    created_at: Optional[str]
    resolved_at: Optional[str]

    class Config:
        from_attributes = True


# ============= Endpoints =============
@router.post("", response_model=TrafficAlertResponse, status_code=201)
async def create_traffic_alert(
    alert_data: TrafficAlertCreate,
    db: Session = Depends(get_db)
):
    """Create a new traffic alert/road incident report."""
    
    # Validate coordinate ranges (basic sanity check)
    if not (-90 <= alert_data.latitude <= 90):
        raise HTTPException(
            status_code=400, 
            detail="Latitude must be between -90 and 90 degrees"
        )
    
    if not (-180 <= alert_data.longitude <= 180):
        raise HTTPException(
            status_code=400,
            detail="Longitude must be between -180 and 180 degrees"
        )
    
    # Check if location is near a road (within 50 meters)
    near_road = await is_near_road(alert_data.latitude, alert_data.longitude, max_distance=50)
    
    if not near_road:
        raise HTTPException(
            status_code=400,
            detail="Location is not near any road. Please select a location on or near a road."
        )
    
    repo = SqlTrafficAlertRepo(db)
    
    # Create alert with unique ID and Singapore time
    alert = TrafficAlert(
        id=0,  # Will be set by database
        alert_id=str(uuid.uuid4()),
        obstruction_type=alert_data.obstruction_type,
        latitude=alert_data.latitude,
        longitude=alert_data.longitude,
        location_name=alert_data.location_name,
        reported_by=alert_data.reported_by,
        delay_duration=None,
        status="active",
        created_at=datetime.now(SGT),  # Use Singapore time
        resolved_at=None,
    )
    
    created_alert = repo.add(alert)
    
    return TrafficAlertResponse(
        id=created_alert.id,
        alert_id=created_alert.alert_id,
        obstruction_type=created_alert.obstruction_type,
        latitude=created_alert.latitude,
        longitude=created_alert.longitude,
        location_name=created_alert.location_name,
        reported_by=created_alert.reported_by,
        delay_duration=created_alert.delay_duration,
        status=created_alert.status,
        created_at=created_alert.created_at.isoformat() if created_alert.created_at else None,
        resolved_at=created_alert.resolved_at.isoformat() if created_alert.resolved_at else None,
    )


@router.get("", response_model=list[TrafficAlertResponse])
def list_traffic_alerts(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List traffic alerts. Optionally filter by status (active, resolved, expired)."""
    repo = SqlTrafficAlertRepo(db)
    
    if status:
        alerts = repo.list_by_status(status)
    else:
        alerts = repo.list()
    
    # Auto-delete alerts older than 1 hour
    now = datetime.now(SGT)  # Use Singapore time
    one_hour_ago = now - timedelta(hours=1)
    
    filtered_alerts = []
    for alert in alerts:
        # If alert is active and older than 1 hour, delete it
        if alert.status == "active" and alert.created_at:
            # Ensure created_at is timezone-aware for comparison
            alert_time = alert.created_at
            if alert_time.tzinfo is None:
                # If naive, assume it's in SGT
                alert_time = alert_time.replace(tzinfo=SGT)
            
            if alert_time < one_hour_ago:
                # Delete the alert from database
                repo.delete(alert.id)
                
                # Skip adding to filtered list (it's deleted)
                continue
        
        filtered_alerts.append(alert)
    
    return [
        TrafficAlertResponse(
            id=alert.id,
            alert_id=alert.alert_id,
            obstruction_type=alert.obstruction_type,
            latitude=alert.latitude,
            longitude=alert.longitude,
            location_name=alert.location_name,
            reported_by=alert.reported_by,
            delay_duration=alert.delay_duration,
            status=alert.status,
            created_at=alert.created_at.isoformat() if alert.created_at else None,
            resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
        )
        for alert in filtered_alerts
    ]


@router.get("/{alert_id}", response_model=TrafficAlertResponse)
def get_traffic_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific traffic alert by ID."""
    repo = SqlTrafficAlertRepo(db)
    alert = repo.get_by_id(alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Traffic alert not found")
    
    return TrafficAlertResponse(
        id=alert.id,
        alert_id=alert.alert_id,
        obstruction_type=alert.obstruction_type,
        latitude=alert.latitude,
        longitude=alert.longitude,
        location_name=alert.location_name,
        reported_by=alert.reported_by,
        delay_duration=alert.delay_duration,
        status=alert.status,
        created_at=alert.created_at.isoformat() if alert.created_at else None,
        resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
    )


@router.delete("/{alert_id}", status_code=204)
def delete_traffic_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Delete a traffic alert."""
    repo = SqlTrafficAlertRepo(db)
    success = repo.delete(alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Traffic alert not found")
    
    return None
