import http.client
import csv
import json
from datetime import datetime, time
import os

def retrieve_api_data():

    conn = http.client.HTTPSConnection("datamall2.mytransport.sg")

    headers = { 'AccountKey': 
            "REDACTED_LTA_ACCOUNT_KEY==",
            'accept': 'application/json'
                }

    conn.request("GET", "/ltaodataservice/BusServices", headers=headers)

    res = conn.getresponse()
    data = res.read()

    data = data.decode("utf-8")

    parsed_data = json.loads(data)

    '''with open('samplebusdata.json', 'w') as outfile: #to view json structure
        json.dump(parsed_data, outfile, indent=4)'''

    return parsed_data

def retrieve_express_bus_fares():
    bus_fares = {}
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "pt_fares/ExpressBusFares.csv")
    with open(csv_path, "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header line
        for parts in reader:
            if len(parts) >= 3:
                dist_range = parts[0]
                fare_info = {
                    "cash_fare" : int(parts[1]),
                    "adult_card_fare": int(parts[2]),
                    "senior_card_fare": int(parts[3]),
                    "student_card_fare": int(parts[4]),
                    "work_concession_fare": int(parts[5]),
                    "disability_card_fare": int(parts[6])
                }
                bus_fares[dist_range] = fare_info
    return bus_fares

def retrieve_feeder_bus_fares():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "pt_fares/FeederBusFares.csv")
    with open(csv_path, "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header line
        for parts in reader:
            if len(parts) >= 3:
                fare_info = {
                    "adult_card_fare": int(parts[1]),
                    "adult_cash_fare": int(parts[2]),
                    "senior_card_fare": int(parts[3]),
                    "senior_cash_fare": int(parts[4]),
                    "student_card_fare": int(parts[5]),
                    "student_cash_fare": int(parts[6]),
                    "work_card_fare": int(parts[7]),
                    "work_cash_fare": int(parts[8]),
                    "disability_card_fare": int(parts[9]),
                    "disability_cash_fare": int(parts[10])
                }
    return fare_info

def retrieve_trunk_bus_fares():
    bus_fares = {}
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "pt_fares/TrunkBusFares.csv")
    with open(csv_path, "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header line
        for parts in reader:
            if len(parts) >= 3:
                dist_range = parts[0]
                fare_info = {
                    "adult_card_fare" : int(parts[1]),
                    "adult_cash_fare": int(parts[2]),
                    "senior_card_fare": int(parts[3]),
                    "senior_card_fare": int(parts[4]),
                    "student_card_fare": int(parts[5]),
                    "student_cash_fare": int(parts[6]),
                    "work_card_fare": int(parts[7]),
                    "work_cash_fare": int(parts[8]),
                    "disability_card_fare": int(parts[9]),
                    "disability_cash_fare": int(parts[10])
                }
                bus_fares[dist_range] = fare_info
    return bus_fares

def retrieve_mrt_lrt_fares():
    mrt_lrt_fares = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "pt_fares/MRT_LRT_Fares.csv")
    with open(csv_path, "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header line
        for parts in reader:
            if len(parts) >= 3:
                dist_range = parts[0]
                fare_info = {
                    "applicable_time" : parts[1],
                    "adult_card_fare": int(parts[2]),
                    "senior_card_fare": int(parts[3]),
                    "student_card_fare": int(parts[4]),
                    "work_concession_fare": int(parts[5]),
                    "disability_card_fare": int(parts[6])
                }
                mrt_lrt_fares += [[dist_range, fare_info]]
    return mrt_lrt_fares

def calculate_bus_fare(bus_type, distance_km, fare_category):
    if bus_type == "express":
        fare_data = retrieve_express_bus_fares()
    elif bus_type == "feeder":
        fare_data = retrieve_feeder_bus_fares()
        final_fare = fare_data.get(fare_category, "Fare category not found.")
        return round(final_fare / 100, 2)
    elif bus_type == "trunk" or bus_type == "Bus number not found.":
        fare_data = retrieve_trunk_bus_fares()
    else:
        raise ValueError("Invalid bus type. Choose from 'express', 'feeder', or 'trunk'.")

    for dist_range, fares in fare_data.items():
        if dist_range == "Up to 3.2 km":
            lower_bound, upper_bound = 0, 3.2
        elif dist_range == "Over 40.2 km":
            lower_bound, upper_bound = 40.2, float('inf')
        else:
            bounds = dist_range.replace("km", "").split("-")
            lower_bound = float(bounds[0].strip())
            upper_bound = float(bounds[1].strip())
        if lower_bound <= distance_km <= upper_bound:
            final_fare = float(fares.get(fare_category, "Fare category not found."))
            return round(final_fare/100, 2)
    return "Distance out of range."

def get_bus_type_from_bus_num(bus_num):
    bus_data = retrieve_api_data()
    for entry in bus_data["value"]:
        if entry["ServiceNo"] == bus_num:
            return entry["Category"].lower()
    return "Bus number not found."

def get_public_holidays():
    public_holiday_dates = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "PublicHolidaysfor2025.csv")
    try:
        with open(csv_path, "r") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header line
            for parts in reader:
                if len(parts) >= 1:
                    holiday_date = parts[0]
                    public_holiday_dates.append(holiday_date)
    except FileNotFoundError:
        print(f"Warning: Public holidays file not found at {csv_path}")
        return []
    except Exception as e:
        print(f"Error reading public holidays: {str(e)}")
        return []
    return public_holiday_dates

def calculate_mrt_lrt_fare(distance_km, fare_category):
    fare_data = retrieve_mrt_lrt_fares()
    ph_dates = get_public_holidays()
    isWeekendPH = False
    actual_dt = datetime.now()
    if actual_dt.strftime('%Y-%m-%d') in ph_dates:
        isWeekendPH = True
    if actual_dt.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        isWeekendPH = True
    current_time = actual_dt.time()
    stip_time = datetime.strptime('07:45', '%H:%M').time()
    before_745_fares = fare_data[:len(fare_data)//2]
    after_745_fares = fare_data[len(fare_data)//2:]

    for idx, entry in enumerate(fare_data):
        if entry[0] == 'Up to 3.2 km':
            lower_bound, upper_bound = 0, 3.2
        elif entry[0] == 'Over 40.2 km':
            lower_bound, upper_bound = 40.2, float('inf')
        else:
            bounds = entry[0].replace("km", "").split("-")
            lower_bound = float(bounds[0].strip())
            upper_bound = float(bounds[1].strip())

        if lower_bound <= distance_km <= upper_bound:
            if current_time >= stip_time:
                final_fare = float(after_745_fares[idx][1].get(fare_category, "Fare category not found."))
                return round(final_fare/100, 2)
            else:
                if isWeekendPH:
                    final_fare = float(after_745_fares[idx][1].get(fare_category, "Fare category not found."))
                    return round(final_fare/100, 2)
                else:
                    final_fare = float(before_745_fares[idx][1].get(fare_category, "Fare category not found."))
                    return round(final_fare/100, 2)

    return "Distance out of range."

def calculate_fare(distance_km, transport_type="mrt", bus_type=None, fare_category="adult_card_fare"):
    """
    Calculate public transport fare based on distance and transport type.
    
    Args:
        distance_km (float): Distance in kilometers
        transport_type (str): Type of transport - 'mrt' or 'bus'
        bus_type (str, optional): Type of bus - 'express', 'feeder', or 'trunk'
        fare_category (str): Fare category - 'adult_card_fare', 'senior_card_fare', etc.
    
    Returns:
        float: Calculated fare in SGD
    """
    if transport_type == "mrt":
        return calculate_mrt_lrt_fare(distance_km, fare_category)
    elif transport_type == "bus":
        if not bus_type:
            bus_type = "trunk"  # default to trunk bus if not specified
        return calculate_bus_fare(bus_type, distance_km, fare_category)
    else:
        raise ValueError("Invalid transport type. Choose 'mrt' or 'bus'")

def calculate_route_fares_from_steps(route_data, fare_category="adult_card_fare"):
    """
    Process a public transport route from Google Maps API and calculate fares for each transit segment.
    
    Args:
        route_data: Route data from Google Maps API (should contain 'steps' array)
        fare_category: Fare category (default: "adult_card_fare")
        
    Returns:
        dict: Breakdown of fares including total_fare, mrt_fare, bus_fare, and route_details
    """
    try:
        total_fare = 0.0
        total_mrt_fare = 0.0
        total_bus_fare = 0.0
        route_details = []
        
        # Get steps from route data
        steps = route_data.get('steps', [])
        
        for step in steps:
            travel_mode = step.get('travel_mode', '')
            
            # Skip walking segments
            if travel_mode == 'WALKING':
                continue
            
            # Process transit segments
            if travel_mode == 'TRANSIT':
                instruction = step.get('instruction', '').lower()
                transit_details = step.get('transit_details', {})
                
                # Extract distance in km from distance_text (e.g., "9.3 km" -> 9.3)
                distance_text = step.get('distance_text', '0 km')
                distance_km = float(distance_text.replace('km', '').strip())
                
                vehicle_type = transit_details.get('vehicle_type', '').upper()
                line_name = transit_details.get('line_name', '')
                departure_stop = transit_details.get('departure_stop', '')
                arrival_stop = transit_details.get('arrival_stop', '')
                
                fare = 0.0
                transport_type = ''
                
                # Determine if it's MRT/LRT or Bus based on vehicle_type
                if vehicle_type in ['SUBWAY', 'TRAIN', 'METRO_RAIL', 'MONORAIL', 'HEAVY_RAIL', 'COMMUTER_TRAIN']:
                    # MRT/LRT transit
                    fare = calculate_mrt_lrt_fare(distance_km, fare_category)
                    total_mrt_fare += fare
                    transport_type = 'MRT/LRT'
                    
                elif vehicle_type == 'BUS':
                    # Check if it's a campus shuttle bus (free)
                    line_short_name = (transit_details.get('line_short_name') or '').lower()
                    is_campus_shuttle = (
                        'campus rider' in line_name.lower() or
                        ('rider' in line_short_name and any(color in line_short_name for color in ['red', 'blue', 'green', 'brown']))
                    )
                    
                    if is_campus_shuttle:
                        # Campus shuttle buses are free
                        fare = 0.0
                        transport_type = 'Campus Shuttle'
                    else:
                        # Regular bus transit
                        if line_name:
                            bus_type = get_bus_type_from_bus_num(line_name)
                            fare = calculate_bus_fare(bus_type, distance_km, fare_category)
                        else:
                            # Default to trunk bus if no line name
                            fare = calculate_bus_fare("trunk", distance_km, fare_category)
                        total_bus_fare += fare
                        transport_type = 'Bus'
                
                total_fare += fare
                
                # Add to route details
                route_details.append({
                    'transport_type': transport_type,
                    'line_name': line_name,
                    'vehicle_type': vehicle_type,
                    'distance_km': round(distance_km, 2),
                    'fare': round(fare, 2),
                    'departure_stop': departure_stop,
                    'arrival_stop': arrival_stop,
                    'departure_time': transit_details.get('departure_time_text', ''),
                    'arrival_time': transit_details.get('arrival_time_text', '')
                })
        
        return {
            'total_fare': round(total_fare, 2),
            'mrt_fare': round(total_mrt_fare, 2),
            'bus_fare': round(total_bus_fare, 2),
            'route_details': route_details
        }
        
    except Exception as e:
        import logging
        logging.error(f"Error in calculate_route_fares_from_steps: {str(e)}")
        raise

def get_all_pt_metrics(distance_km, transport_type="mrt", bus_number=None, fare_category="adult_card_fare"):
    """
    Calculate public transport metrics for a given route.
    
    Args:
        distance_km: Distance in kilometers
        transport_type: Type of transport ("mrt", "bus", etc.)
        bus_number: Optional bus service number
        fare_category: Fare category (default: "adult_card_fare")
        
    Returns:
        dict: Public transport metrics including fare and distance
    """
    try:
        distance_km = float(distance_km)
        if distance_km <= 0:
            raise ValueError("Distance must be greater than 0")
            
        metrics = {
            "distance_km": round(distance_km, 2)
        }

        # Calculate fare based on transport type
        if transport_type.lower() == "mrt" or transport_type.lower() in ["subway", "train"]:
            fare = calculate_mrt_lrt_fare(distance_km, fare_category)
        elif transport_type.lower() == "bus":
            if bus_number:
                bus_type = get_bus_type_from_bus_num(bus_number)
                fare = calculate_bus_fare(bus_type, distance_km, fare_category)
            else:
                # Default to trunk bus if no bus number provided
                fare = calculate_bus_fare("trunk", distance_km, fare_category)
        else:
            fare = 0.0

        # Ensure fare is a valid number
        if isinstance(fare, (int, float)):
            metrics["fare"] = float(fare)
        else:
            metrics["fare"] = 0.0
            
        return metrics
        
    except Exception as e:
        print(f"Error in get_all_pt_metrics: {str(e)}")
        raise