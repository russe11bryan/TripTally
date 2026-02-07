from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..metrics.get_metrics import get_route_metrics
from ..metrics.lta_carpark_full_data import get_nearby_carparks
from ..services.maps_service import directions
from ..metrics.get_driving_metrics import get_all_driving_metrics, calculate_erp_charge, get_list_of_passed_gantries
from ..metrics.get_pt_metrics import calculate_bus_fare, calculate_mrt_lrt_fare, get_bus_type_from_bus_num, calculate_route_fares_from_steps
from datetime import datetime, timedelta

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"]
)

async def get_route_data(mode, origin_lat, origin_lng, dest_lat, dest_lng):
    """Get route data from Google Maps API"""
    origin = f"{origin_lat},{origin_lng}"
    destination = f"{dest_lat},{dest_lng}"
    
    route_data = await directions(
        origin=origin,
        destination=destination,
        mode=mode.lower(),
        alternatives=False
    )
    
    if not route_data or not isinstance(route_data, list) or len(route_data) == 0:
        raise HTTPException(status_code=404, detail="No route found")
    
    # directions() returns a list of route sets, each with a 'routes' array
    route_set = route_data[0]
    if not route_set.get('routes') or len(route_set['routes']) == 0:
        raise HTTPException(status_code=404, detail="No routes in response")
    
    # Return the first actual route from the set
    route = route_set['routes'][0]
    return route

@router.get("/driving")
async def get_driving_metrics(
    origin_lat: Optional[float] = Query(None),
    origin_lng: Optional[float] = Query(None),
    dest_lat: float = Query(...),
    dest_lng: float = Query(...),
):
    """Get driving metrics for a route"""
    if origin_lat is None or origin_lng is None:
        origin_lat = 1.3521  # Singapore center
        origin_lng = 103.8198

    try:
        route = await get_route_data('driving', origin_lat, origin_lng, dest_lat, dest_lng)
        
        # Calculate distance in km - handle both formats
        distance_val = route.get('distance')
        if isinstance(distance_val, dict):
            distance_meters = distance_val.get('value', 0)
        elif isinstance(distance_val, (int, float)):
            distance_meters = distance_val
        else:
            distance_meters = 0
            
        distance_km = distance_meters / 1000.0
        
        if distance_km <= 0:
            raise HTTPException(status_code=400, detail="Invalid distance calculation")
        
        # Get duration - handle both formats
        duration_val = route.get('duration')
        if isinstance(duration_val, dict):
            duration_seconds = duration_val.get('value', 0)
        elif isinstance(duration_val, (int, float)):
            duration_seconds = duration_val
        else:
            duration_seconds = 0
            
        duration_minutes = duration_seconds / 60
        
        # Calculate departure and arrival times
        now = datetime.now()
        arrival_time = now + timedelta(minutes=duration_minutes)
        
        # Get the route polyline for ERP calculation
        polyline_val = route.get('overview_polyline') or route.get('encoded_polyline')
        if isinstance(polyline_val, dict):
            polyline = polyline_val.get('points', '')
        elif isinstance(polyline_val, str):
            polyline = polyline_val
        else:
            polyline = ''
        
        # Calculate driving metrics (includes ERP calculation if polyline exists)
        driving_metrics = get_all_driving_metrics(distance_km, polyline)
        
        # Traffic conditions
        traffic_status = "Moderate"  # Default
        if 'duration_in_traffic' in route:
            traffic_in_traffic = route['duration_in_traffic']
            if traffic_in_traffic is not None:
                if isinstance(traffic_in_traffic, dict):
                    traffic_duration = traffic_in_traffic.get('value', duration_seconds)
                else:
                    traffic_duration = traffic_in_traffic
                
                if duration_seconds > 0 and traffic_duration is not None:
                    traffic_ratio = traffic_duration / duration_seconds
                    if traffic_ratio < 1.1:
                        traffic_status = "Light"
                    elif traffic_ratio > 1.3:
                        traffic_status = "Heavy"
        
        fuel_cost = driving_metrics.get('fuel_cost_sgd') or 0.0
        
        return {
            "duration_minutes": round(duration_minutes),
            "distance_km": round(distance_km, 1),
            "erp_charges": driving_metrics.get('erp_charges') or 0.0,
            "fuel_cost_sgd": fuel_cost,
            "fuel_cost_per_km": round(fuel_cost / distance_km, 2) if distance_km > 0 else 0.0,
            "co2_emissions_kg": driving_metrics.get('co2_emissions_kg') or 0.0,
            "total_cost": driving_metrics.get('total_cost') or 0.0,
            "departure_time": now.strftime("%H:%M"),
            "arrival_time": arrival_time.strftime("%H:%M"),
            "traffic_conditions": traffic_status
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/public-transport")
async def get_pt_metrics(
    origin_lat: Optional[float] = Query(None),
    origin_lng: Optional[float] = Query(None),
    dest_lat: float = Query(...),
    dest_lng: float = Query(...),
):
    """Get public transport metrics for a route"""
    if origin_lat is None or origin_lng is None:
        origin_lat = 1.3521
        origin_lng = 103.8198

    try:
        route = await get_route_data('transit', origin_lat, origin_lng, dest_lat, dest_lng)
        
        # Calculate distance - handle both formats
        distance_val = route.get('distance')
        if isinstance(distance_val, dict):
            distance_meters = distance_val.get('value', 0)
        elif isinstance(distance_val, (int, float)):
            distance_meters = distance_val
        else:
            distance_meters = 0
            
        distance_km = distance_meters / 1000.0
        
        # Calculate duration - handle both formats
        duration_val = route.get('duration')
        if isinstance(duration_val, dict):
            duration_seconds = duration_val.get('value', 0)
        elif isinstance(duration_val, (int, float)):
            duration_seconds = duration_val
        else:
            duration_seconds = 0
            
        duration_minutes = duration_seconds / 60
        
        # Calculate times
        now = datetime.now()
        arrival_time = now + timedelta(minutes=duration_minutes)
        
        # Use the new calculate_route_fares_from_steps function
        fare_breakdown = calculate_route_fares_from_steps(route, fare_category="adult_card_fare")
        
        # Format route details for frontend with duration info
        steps = route.get('steps', [])
        formatted_route_details = []
        
        for step in steps:
            travel_mode = step.get('travel_mode', '')
            duration_text = step.get('duration_text', '')
            distance_text = step.get('distance_text', '')
            
            step_detail = {
                'travel_mode': travel_mode,
                'duration': duration_text,
                'distance': distance_text,
                'instruction': step.get('instruction', '')
            }
            
            if travel_mode == 'TRANSIT':
                transit_details = step.get('transit_details', {})
                step_detail.update({
                    'line_name': transit_details.get('line_name', ''),
                    'vehicle_type': transit_details.get('vehicle_type', ''),
                    'departure_stop': transit_details.get('departure_stop', ''),
                    'arrival_stop': transit_details.get('arrival_stop', ''),
                    'departure_time': transit_details.get('departure_time_text', ''),
                    'arrival_time': transit_details.get('arrival_time_text', ''),
                    'num_stops': transit_details.get('num_stops', 0)
                })
                
                # Find matching fare from fare_breakdown
                for detail in fare_breakdown['route_details']:
                    if (detail['line_name'] == step_detail['line_name'] and 
                        detail['departure_stop'] == step_detail['departure_stop']):
                        step_detail['fare'] = detail['fare']
                        step_detail['transport_type'] = detail['transport_type']
                        break
            
            formatted_route_details.append(step_detail)
        
        return {
            "duration_minutes": round(duration_minutes),
            "distance_km": round(distance_km, 1),
            "fare": fare_breakdown['total_fare'],
            "mrt_fare": fare_breakdown['mrt_fare'],
            "bus_fare": fare_breakdown['bus_fare'],
            "departure_time": now.strftime("%H:%M"),
            "arrival_time": arrival_time.strftime("%H:%M"),
            "next_departure": "Coming Soon",  # This would need real-time data
            "route_details": formatted_route_details
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/walking")
async def get_walking_metrics(
    origin_lat: Optional[float] = Query(None),
    origin_lng: Optional[float] = Query(None),
    dest_lat: float = Query(...),
    dest_lng: float = Query(...),
):
    """Get walking metrics for a route"""
    if origin_lat is None or origin_lng is None:
        origin_lat = 1.3521
        origin_lng = 103.8198

    try:
        route = await get_route_data('walking', origin_lat, origin_lng, dest_lat, dest_lng)
        
        # Calculate distance - handle both formats
        distance_val = route.get('distance')
        if isinstance(distance_val, dict):
            distance_meters = distance_val.get('value', 0)
        elif isinstance(distance_val, (int, float)):
            distance_meters = distance_val
        else:
            distance_meters = 0
            
        distance_km = distance_meters / 1000.0
        
        # Calculate duration - handle both formats
        duration_val = route.get('duration')
        if isinstance(duration_val, dict):
            duration_seconds = duration_val.get('value', 0)
        elif isinstance(duration_val, (int, float)):
            duration_seconds = duration_val
        else:
            duration_seconds = 0
            
        duration_minutes = duration_seconds / 60
        
        # Calculate times
        now = datetime.now()
        arrival_time = now + timedelta(minutes=duration_minutes)
        
        # Calculate calories (approximate: 60 kcal per km)
        calories = round(distance_km * 60)
        
        return {
            "duration_minutes": round(duration_minutes),
            "distance_km": round(distance_km, 1),
            "calories": calories,
            "departure_time": now.strftime("%H:%M"),
            "arrival_time": arrival_time.strftime("%H:%M"),
            "elevation_gain": route.get('elevation_gain', 0)  # If available from Google Maps
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cycling")
async def get_cycling_metrics(
    origin_lat: Optional[float] = Query(None),
    origin_lng: Optional[float] = Query(None),
    dest_lat: float = Query(...),
    dest_lng: float = Query(...),
):
    """Get cycling metrics for a route"""
    if origin_lat is None or origin_lng is None:
        origin_lat = 1.3521
        origin_lng = 103.8198

    try:
        route = await get_route_data('bicycling', origin_lat, origin_lng, dest_lat, dest_lng)
        
        # Calculate distance - handle both formats
        distance_val = route.get('distance')
        if isinstance(distance_val, dict):
            distance_meters = distance_val.get('value', 0)
        elif isinstance(distance_val, (int, float)):
            distance_meters = distance_val
        else:
            distance_meters = 0
            
        distance_km = distance_meters / 1000.0
        
        # Calculate duration - handle both formats
        duration_val = route.get('duration')
        if isinstance(duration_val, dict):
            duration_seconds = duration_val.get('value', 0)
        elif isinstance(duration_val, (int, float)):
            duration_seconds = duration_val
        else:
            duration_seconds = 0
            
        duration_minutes = duration_seconds / 60
        
        # Calculate times
        now = datetime.now()
        arrival_time = now + timedelta(minutes=duration_minutes)
        
        # Calculate calories (approximate: 40 kcal per km)
        calories = round(distance_km * 40)
        
        # Calculate CO2 saved (compared to driving)
        co2_saved = round(distance_km * 0.14, 2)
        
        return {
            "duration_minutes": round(duration_minutes),
            "distance_km": round(distance_km, 1),
            "calories": calories,
            "co2_saved": co2_saved,
            "departure_time": now.strftime("%H:%M"),
            "arrival_time": arrival_time.strftime("%H:%M"),
            "elevation_gain": route.get('elevation_gain', 0),  # If available from Google Maps
            "traffic_conditions": "Light"  # Default for cycling
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))