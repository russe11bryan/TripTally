import http.client
import csv
import json
import os

def retrieve_api_data():
    conn = http.client.HTTPSConnection("datamall2.mytransport.sg")
    headers = { 
        'AccountKey': "REDACTED_LTA_ACCOUNT_KEY==",
        'accept': 'application/json'
    }
    conn.request("GET", "/ltaodataservice/CarParkAvailabilityv2", headers=headers)
    res = conn.getresponse()
    data = res.read()
    data = data.decode("utf-8")
    return json.loads(data)

def retrieve_cp_rates():
    carpark_rates = {}
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(backend_dir, "metrics", "CarparkRates.csv")
    with open(csv_path, "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header line
        for parts in reader:
            if len(parts) >= 6:
                carpark_name = parts[0].strip()
                weekday_rate_1 = parts[2].strip()
                weekday_rate_2 = parts[3].strip()
                saturday_rate = parts[4].strip()
                sunday_ph_rate = parts[5].strip()

                # Handle empty or '-' values
                if not weekday_rate_1 or weekday_rate_1 == '-':
                    weekday_rate_1 = "Not available"
                if not weekday_rate_2 or weekday_rate_2 == '-':
                    weekday_rate_2 = "Not available"
                if not saturday_rate or saturday_rate == '-':
                    saturday_rate = "Not available"
                if not sunday_ph_rate or sunday_ph_rate == '-':
                    sunday_ph_rate = "Not available"

                rates_info = {
                    "weekday_rate_1": weekday_rate_1,
                    "weekday_rate_2": weekday_rate_2,
                    "saturday_rates": saturday_rate,
                    "sunday_public_holiday_rates": sunday_ph_rate
                }

                # Handle "Same as weekdays" cases
                if rates_info["saturday_rates"].lower() == "same as weekdays":
                    rates_info["saturday_rates"] = weekday_rate_1
                    if weekday_rate_2 != "Not available":
                        rates_info["saturday_rates"] += " / " + weekday_rate_2

                if rates_info["sunday_public_holiday_rates"].lower() == "same as weekdays":
                    rates_info["sunday_public_holiday_rates"] = weekday_rate_1
                    if weekday_rate_2 != "Not available":
                        rates_info["sunday_public_holiday_rates"] += " / " + weekday_rate_2

                if rates_info["sunday_public_holiday_rates"].lower() == "same as saturday":
                    rates_info["sunday_public_holiday_rates"] = rates_info["saturday_rates"]

                carpark_rates[carpark_name] = rates_info
    
    return carpark_rates

def retrieve_live_carpark_data_by_latlong(cp_lat, cp_long):
    data = retrieve_api_data()
    for entry in data["value"]:
        location_str = entry["Location"]
        current_lat, current_long = map(float, location_str.split(" "))
        if cp_long == current_long and cp_lat == current_lat:
            return {
                "car_park_ID": entry["CarParkID"],
                "area": entry["Area"],
                "development": entry["Development"],
                "available_lots": int(entry["AvailableLots"]),
                "agency": entry["Agency"]
            }
    raise ValueError("No carpark found at the provided latitude and longitude.")

def get_nearby_carparks(dest_lat, dest_long, radius_meters=1500):
    data = retrieve_api_data()
    cp_rates = retrieve_cp_rates()
    all_carparks = []

    # First, collect all carparks within radius
    for entry in data["value"]:
        location_str = entry["Location"]
        current_lat, current_long = map(float, location_str.split(" "))
        
        # Calculate distance using Haversine formula
        from math import radians, cos, sin, sqrt, atan2

        R = 6371000  # Radius of the Earth in meters
        dlat = radians(current_lat - dest_lat)
        dlon = radians(current_long - dest_long)
        a = sin(dlat / 2) ** 2 + cos(radians(dest_lat)) * cos(radians(current_lat)) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c

        if distance <= radius_meters:
            carpark = {
                "car_park_ID": entry["CarParkID"],
                "area": entry["Area"],
                "development": entry["Development"],
                "available_lots": int(entry["AvailableLots"]),
                "agency": entry["Agency"],
                "distance_meters": int(distance),
                "latitude": current_lat,
                "longitude": current_long
            }
            all_carparks.append(carpark)

    # Group carparks by normalized development name
    carpark_groups = {}
    for carpark in all_carparks:
        dev_name = carpark["development"].strip()
        if not dev_name:  # Skip empty development names
            continue
        
        # Use area name if development is empty
        if dev_name == "NULL" or dev_name.lower() == "nil":
            dev_name = carpark["area"].strip()
            carpark["development"] = dev_name
        
        # Skip if still no valid name
        if not dev_name or dev_name == "NULL" or dev_name.lower() == "nil":
            continue
            
        if dev_name not in carpark_groups:
            carpark_groups[dev_name] = []
        carpark_groups[dev_name].append(carpark)

    # Create combined carpark list
    combined_carparks = []
    for dev_name, carparks in carpark_groups.items():
        # Use the carpark with the shortest distance as base
        carparks.sort(key=lambda x: x["distance_meters"])
        base_carpark = carparks[0].copy()
        
        # Always create sections array, even for single carparks
        total_lots = sum(cp["available_lots"] for cp in carparks)
        base_carpark["available_lots"] = total_lots
        base_carpark["total_sections"] = len(carparks)
        base_carpark["sections"] = [
            {
                "id": cp["car_park_ID"],
                "available_lots": cp["available_lots"],
                "distance_meters": cp["distance_meters"]
            }
            for cp in carparks
        ]
        
        combined_carparks.append(base_carpark)

    # Sort by distance and limit to 10
    combined_carparks.sort(key=lambda x: x["distance_meters"])
    combined_carparks = combined_carparks[:10]

    # Add rates for each carpark
    for carpark in combined_carparks:
        dev_name = carpark["development"]
        # Find exact match first
        matching_carpark = None
        if dev_name in cp_rates:
            matching_carpark = dev_name
        else:
            # Try case-insensitive match
            dev_name_lower = dev_name.lower().strip()
            matching_carpark = next(
                (name for name in cp_rates.keys() 
                 if name.lower().strip() == dev_name_lower),
                None
            )
        
        if matching_carpark:
            carpark["weekday_rate_1"] = cp_rates[matching_carpark]["weekday_rate_1"]
            carpark["weekday_rate_2"] = cp_rates[matching_carpark]["weekday_rate_2"]
            carpark["saturday_rates"] = cp_rates[matching_carpark]["saturday_rates"]
            carpark["sunday_public_holiday_rates"] = cp_rates[matching_carpark]["sunday_public_holiday_rates"]
        else:
            carpark["weekday_rate_1"] = "N/A"
            carpark["weekday_rate_2"] = "N/A"
            carpark["saturday_rates"] = "N/A"
            carpark["sunday_public_holiday_rates"] = "N/A"

    return combined_carparks