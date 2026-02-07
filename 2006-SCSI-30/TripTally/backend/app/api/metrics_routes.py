"""
Routes for fetching transport metrics.
"""
from fastapi import APIRouter, Query, HTTPException
from app.metrics.get_driving_metrics import get_all_driving_metrics, calculate_erp_charge, get_list_of_passed_gantries
from app.metrics.get_pt_metrics import calculate_bus_fare, calculate_mrt_lrt_fare, get_bus_type_from_bus_num, calculate_route_fares_from_steps
from metrics.lta_carpark_full_data import get_nearby_carparks

router = APIRouter(prefix="/metrics", tags=["metrics"])

from app.services.maps_service import directions

@router.get("/compare")
async def get_comparison_metrics(
    distance_km: float = Query(..., description="Distance in kilometers"),
    route_polyline: str = Query(..., description="Encoded polyline of the route for ERP calculation"),
    fare_category: str = Query("adult_card_fare", description="Fare category for public transport"),
    origin: str = Query(..., description="Origin coordinates (lat,lng)"),
    destination: str = Query(..., description="Destination coordinates (lat,lng)"),
):
    """Get comparison metrics for different transport modes."""
    
    # Validate distance
    if distance_km <= 0:
        raise HTTPException(
            status_code=422,
            detail="Distance must be greater than 0"
        )
    
    # Validate coordinates format
    try:
        origin_lat, origin_lng = map(float, origin.split(','))
        dest_lat, dest_lng = map(float, destination.split(','))
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid coordinates format. Use 'latitude,longitude'"
        )
    
    # Initialize response structures with all required fields
    driving_metrics = {
        "fuel_cost_sgd": 0.0,
        "total_cost": 0.0,
        "erp_charges": 0.0,
        "co2_emissions_kg": 0.0
    }
    
    pt_metrics = {
        "total_fare": 0.0,
        "mrt_fare": 0.0,
        "bus_fare": 0.0,
        "segments": [],
        "route_polyline": None,
        "total_distance_km": 0.0,
        "co2_emissions_kg": 0.0  # Public transport CO2 emissions considered negligible per passenger
    }
    
    try:
        # Calculate driving metrics (now includes ERP if polyline is provided)
        driving_result = get_all_driving_metrics(distance_km, route_polyline)
        if isinstance(driving_result, dict):
            driving_metrics.update(driving_result)
        else:
            raise HTTPException(status_code=500, detail="Error calculating driving metrics")

        # Get public transport route details
        route_data = await directions(
            origin=origin,
            destination=destination,
            mode="transit",
            alternatives=False  # Get single best route
        )
        
        if route_data and isinstance(route_data, list) and len(route_data) > 0:
            # The route_data is a list of dictionaries (one per alternative)
            route_set = route_data[0]  # Get first alternative
            
            # Extract the first actual route from the routes array
            if route_set and isinstance(route_set, dict):
                routes = route_set.get("routes", [])
                
                if routes and len(routes) > 0:
                    route = routes[0]  # Get first route
                    
                    # Use the new calculate_route_fares_from_steps function
                    fare_breakdown = calculate_route_fares_from_steps(route, fare_category)
                    
                    # Extract polyline
                    route_polyline_points = route.get("encoded_polyline") or route_set.get("overview_polyline")
                    
                    # Update pt_metrics with the calculated fares
                    pt_metrics.update({
                        "total_fare": fare_breakdown.get("total_fare", 0.0),
                        "mrt_fare": fare_breakdown.get("mrt_fare", 0.0),
                        "bus_fare": fare_breakdown.get("bus_fare", 0.0),
                        "segments": fare_breakdown.get("route_details", []),
                        "route_polyline": route_polyline_points or route_polyline,
                        "total_distance_km": distance_km
                    })
                
    except Exception as e:
        import traceback
        error_detail = f"Error calculating metrics: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # For logging
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )
        
    return {
        "driving": driving_metrics,
        "public_transport": pt_metrics
    }

@router.get("/carparks")
async def get_carparks_near_destination(
    latitude: float = Query(..., description="Destination latitude"),
    longitude: float = Query(..., description="Destination longitude"),
    radius: int = Query(1500, description="Search radius in meters")
):
    """Get carparks near a destination point."""
    return get_nearby_carparks(latitude, longitude, radius)