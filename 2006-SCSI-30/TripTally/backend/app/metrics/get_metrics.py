import googlemaps
import os
from datetime import datetime, timedelta
from .get_driving_metrics import get_all_driving_metrics, calculate_erp_charge, get_list_of_passed_gantries
from .get_pt_metrics import calculate_fare

gmaps = googlemaps.Client(key=os.environ.get('GOOGLE_MAPS_API_KEY'))

def get_route_metrics(origin_lat, origin_lng, dest_lat, dest_lng, mode):
    try:
        # Get directions from Google Maps
        result = gmaps.directions(
            origin=f"{origin_lat},{origin_lng}",
            destination=f"{dest_lat},{dest_lng}",
            mode=mode,
            departure_time=datetime.now()
        )

        if not result:
            return {"error": "No route found"}

        route = result[0]
        leg = route['legs'][0]

        # Base metrics for all modes
        distance_km = leg['distance']['value'] / 1000  # Convert meters to km
        duration_minutes = round(leg['duration']['value'] / 60)  # Convert seconds to minutes
        departure_time = datetime.now().strftime("%H:%M")
        arrival_time = (datetime.now() + timedelta(minutes=duration_minutes)).strftime("%H:%M")

        # Common response structure
        response = {
            "duration_minutes": duration_minutes,
            "distance_km": distance_km,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
        }

        # Mode-specific metrics
        if mode == 'driving':
            driving_metrics = get_all_driving_metrics(distance_km)
            polyline = route.get('overview_polyline', {}).get('points', '')
            gantries_passed = get_list_of_passed_gantries(polyline)
            erp_charges = calculate_erp_charge(gantries_passed)
            
            response.update({
                "fuel_cost_sgd": driving_metrics['fuel_cost_sgd'],
                "fuel_cost_per_km": round(driving_metrics['fuel_cost_sgd'] / distance_km, 2),
                "erp_charges": erp_charges,
                "co2_emissions_kg": driving_metrics['co2_emissions_kg'],
            })

            # Add traffic conditions if available
            if 'duration_in_traffic' in leg:
                traffic_ratio = leg['duration_in_traffic']['value'] / leg['duration']['value']
                if traffic_ratio < 1.1:
                    response['traffic_conditions'] = "Light"
                elif traffic_ratio < 1.3:
                    response['traffic_conditions'] = "Moderate"
                else:
                    response['traffic_conditions'] = "Heavy"

        elif mode == 'transit':
            # Calculate public transport fares
            fare = calculate_fare(distance_km)
            response.update({
                "fare": fare,
                "next_departure": "Coming soon",  # This would need real-time transit data
                "route_details": [step['html_instructions'] for step in leg['steps']]
            })

        elif mode == 'walking':
            # Calculate calories burned (rough estimate: 60 kcal per km)
            calories = round(distance_km * 60)
            response.update({
                "calories": calories,
                "elevation_gain": sum(
                    step.get('elevation', 0) 
                    for step in leg.get('steps', [])
                    if step.get('elevation', 0) > 0
                )
            })

        elif mode == 'bicycling':
            # Calculate calories burned (rough estimate: 40 kcal per km)
            calories = round(distance_km * 40)
            co2_saved = round(distance_km * 0.14, 2)  # Compared to driving
            response.update({
                "calories": calories,
                "co2_saved": co2_saved,
                "elevation_gain": sum(
                    step.get('elevation', 0) 
                    for step in leg.get('steps', [])
                    if step.get('elevation', 0) > 0
                )
            })

        return response

    except Exception as e:
        print(f"Error getting {mode} metrics:", str(e))
        return {"error": str(e)}