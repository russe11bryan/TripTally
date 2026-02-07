import requests
import json
import csv
from bs4 import BeautifulSoup
import http.client
from shapely.geometry import LineString
from shapely.wkt import loads
from datetime import datetime, time, timedelta
import googlemaps
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

gmaps = googlemaps.Client(key='REDACTED_GOOGLE_MAPS_KEY_3')

FUEL_PRICE_PER_LITRE = 2.7
FUEL_EFFICIENCY_LITRE_PER_KM = 0.09
CO2_EMISSIONS_PER_KM = 0.110  # in kg/km

def kml_description_to_dict(html):
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.find_all('tr')
    attr_dict = {}
    for row in rows:
        th = row.find('th')
        td = row.find('td')
        if th and td:
            key = th.get_text(strip=True)
            value = td.get_text(strip=True)
            attr_dict[key] = value
    return attr_dict

def get_erp_data():          
    dataset_id = "d_753090823cc9920ac41efaa6530c5893"
    url = "https://api-open.data.gov.sg/v1/public/api/datasets/" + dataset_id + "/poll-download"
            
    response = requests.get(url)
    json_data = response.json()
    if json_data['code'] != 0:
        print(json_data['errMsg'])
        exit(1)

    url = json_data['data']['url']
    response = requests.get(url)

    data = response.json()
    #print(response.text)

    features = []

    for feature in data['features']:
        description_html = feature['properties'].get('Description', '')
        parsed_attrs = kml_description_to_dict(description_html)
        feature['properties'].update(parsed_attrs)
        # Remove the original description field for cleaner access
        if 'Description' in feature['properties']:
            del feature['properties']['Description']

    #print(data['features'])
    for feature in data['features']:
        feature['geometry']['coordinates'] = [(feature['geometry']['coordinates'][0][0], feature['geometry']['coordinates'][0][1]), (feature['geometry']['coordinates'][1][0], feature['geometry']['coordinates'][1][1])]
        features += [feature]
        #print(features)
    return features

def retrieve_erp_rates():
    erp_rates = {}
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "ERPRates.csv")
    with open(csv_path, "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header line
        for parts in reader:
            if len(parts) >= 3:
                gantry_id = parts[0]
                rate_info = {
                    "gantry_location_name": parts[1],
                    "road_type": parts[2],
                    "applicable_days": parts[3],
                    "charge_rates": {
                    "7.00-7.05": float(parts[4]),
                    "7.05-7.25": float(parts[5]),
                    "7.25-7.30": float(parts[6]),
                    "7.30-7.35": float(parts[7]),
                    "7.35-7.55": float(parts[8]),
                    "7.55-8.00": float(parts[9]),
                    "8.00-8.05": float(parts[10]),
                    "8.05-8.25": float(parts[11]),
                    "8.25-8.30": float(parts[12]),
                    "8.30-8.35": float(parts[13]),
                    "8.35-8.55": float(parts[14]),
                    "8.55-9.00": float(parts[15]),
                    "9.00-9.05": float(parts[16]),
                    "9.05-9.25": float(parts[17]),
                    "9.25-9.30": float(parts[18]),
                    "9.30-9.35": float(parts[19]),
                    "9.35-9.55": float(parts[20]),
                    "9.55-10.00": float(parts[21]),
                    "17.30-17.35": float(parts[22]),
                    "17.35-17.55": float(parts[23]),
                    "17.55-18.00": float(parts[24]),
                    "18.00-18.05": float(parts[25]),
                    "18.05-18.25": float(parts[26]),
                    "18.25-18.30": float(parts[27]),
                    "18.30-18.35": float(parts[28]),
                    "18.35-18.55": float(parts[29]),
                    "18.55-19.00": float(parts[30]),
                    "19.00-19.05": float(parts[31]),
                    "19.05-19.25": float(parts[32]),
                    "19.25-19.30": float(parts[33]),
                    "19.30-19.35": float(parts[34]),
                    "19.35-19.55": float(parts[35]),
                    "19.55-20.00": float(parts[36])
                    }
                }
                erp_rates[gantry_id] = rate_info
    return erp_rates

def retrieve_all_road_incidents():

    conn = http.client.HTTPSConnection("datamall2.mytransport.sg")

    headers = { 'AccountKey': 
            "REDACTED_LTA_ACCOUNT_KEY==",
            'accept': 'application/json'
                }

    conn.request("GET", "/ltaodataservice/TrafficIncidents", headers=headers)

    res = conn.getresponse()
    data = res.read()

    data = data.decode("utf-8")

    parsed_data = json.loads(data)

    with open('sampleroadincidentdata.json', 'w') as outfile: #to view json structure
        json.dump(parsed_data, outfile, indent=4)

    return parsed_data

def get_full_erp_info():
    erp_data = get_erp_data()
    erp_rates = retrieve_erp_rates()
    full_erp_info = []

    for gantry_num in erp_rates:
        for feature in erp_data:
            if gantry_num == feature['properties'].get('GNTRY_NUM'):
                erp_rates[gantry_num]['coordinates'] = feature['geometry']['coordinates']
        #print(erp_rates[gantry])
        #print("==========================================================")
        full_erp_info += [{'gantry_no': gantry_num, 'info': erp_rates[gantry_num]}]
    return full_erp_info

def calculate_fuel_cost(distance_km):
    fuel_used = distance_km * FUEL_EFFICIENCY_LITRE_PER_KM
    cost = fuel_used * FUEL_PRICE_PER_LITRE
    return round(cost, 2)

def calculate_co2_emissions(distance_km):
    emissions = distance_km * CO2_EMISSIONS_PER_KM
    return round(emissions, 2)


def get_all_driving_metrics(distance_km, polyline=None):
    """
    Calculate all driving metrics including fuel cost, CO2 emissions, and optionally ERP charges.
    
    Args:
        distance_km: Distance in kilometers
        polyline: Optional encoded polyline for ERP calculation
        
    Returns:
        dict: Driving metrics including fuel_cost_sgd, co2_emissions_kg, and erp_charges
    """
    try:
        # Ensure distance is a valid float
        distance_km = float(distance_km)
        if distance_km <= 0:
            raise ValueError("Distance must be greater than 0")
        
        # Base metrics (always calculated)
        metrics = {
            "distance_km": round(distance_km, 2),
            "fuel_cost_sgd": calculate_fuel_cost(distance_km),
            "co2_emissions_kg": calculate_co2_emissions(distance_km)
        }

        # Add ERP charges if polyline is provided
        if polyline:
            try:
                gantries_passed = get_list_of_passed_gantries(polyline)
                erp_charges = calculate_erp_charge(gantries_passed)
                metrics["erp_charges"] = float(erp_charges)
            except Exception as e:
                logger.error(f"Error calculating ERP charges: {str(e)}")
                metrics["erp_charges"] = 0.0
        else:
            metrics["erp_charges"] = 0.0
        
        # Calculate total cost
        metrics["total_cost"] = round(metrics["fuel_cost_sgd"] + metrics["erp_charges"], 2)

        return metrics
        
    except Exception as e:
        logger.error(f"Error in get_all_driving_metrics: {str(e)}")
        raise

def decode_polyline(encoded):
    """Decodes a Google Maps encoded polyline string into a list of (lat, lon) tuples."""
    encoded_len = len(encoded)
    index = 0
    lat = 0
    lng = 0
    coordinates = []

    while index < encoded_len:
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        coordinates.append((lat * 1e-5, lng * 1e-5))
    return coordinates

def polyline_intersects_stringline(polyline_str, lat_long1, lat_long2):
    # Decode polyline: returns list of (lat, lon)
    polyline = decode_polyline(polyline_str)
    # Convert to (lon, lat)
    polyline_geometry = LineString([(lon, lat) for lat, lon in polyline])
    # Switch order for stringline as well
    stringline = LineString([(lat_long1[1], lat_long1[0]), (lat_long2[1], lat_long2[0])])
    # Return True if polyline intersects stringline, False otherwise
    return polyline_geometry.intersects(stringline)

def get_start_point_of_polyline(polyline_str):
    polyline = decode_polyline(polyline_str)
    return polyline[0]  # returns (lat, lon) of start point

def get_list_of_passed_gantries(polyline_str):
    try:
        erp_data = get_full_erp_info()
        if not erp_data:
            logger.warning("No ERP data available")
            return []
            
        gantries_passed = []
        origin = get_start_point_of_polyline(polyline_str)
        if not origin:
            logger.warning("Could not decode polyline start point")
            return []

        departure_dt = datetime.now()
        departure_dt_str = departure_dt.strftime('%Y-%m-%d %H:%M')

        seen_gantries = set()  # Track already processed gantries
        
        for feature in erp_data:
            if 'coordinates' not in feature['info']:
                continue
                
            try:
                gantry_id = feature['gantry_no']
                if gantry_id in seen_gantries:
                    continue
                    
                intersects = polyline_intersects_stringline(
                    polyline_str,
                    (feature['info']['coordinates'][0][1], feature['info']['coordinates'][0][0]),
                    (feature['info']['coordinates'][1][1], feature['info']['coordinates'][1][0])
                )
                
                if intersects:
                    destination = (feature['info']['coordinates'][0][1], feature['info']['coordinates'][0][0])
                    try:
                        result = gmaps.distance_matrix(
                            origins=[origin],
                            destinations=[destination],
                            mode='driving'
                        )
                        
                        if result.get('status') == 'OK' and result.get('rows') and result['rows'][0].get('elements'):
                            element = result['rows'][0]['elements'][0]
                            if element.get('status') == 'OK' and 'duration' in element:
                                duration_seconds = element['duration']['value']
                                real_datetime = datetime.strptime(departure_dt_str, '%Y-%m-%d %H:%M')
                                departure_time = real_datetime + timedelta(seconds=duration_seconds)
                                
                                gantries_passed.append((gantry_id, departure_time.strftime("%Y-%m-%d %H:%M")))
                                seen_gantries.add(gantry_id)
                                origin = destination
                            else:
                                logger.warning(f"Invalid response element for gantry {gantry_id}")
                        else:
                            logger.warning(f"Invalid distance matrix response for gantry {gantry_id}")
                    except Exception as api_error:
                        logger.error(f"Google Maps API error for gantry {gantry_id}: {str(api_error)}")
                        continue
                        
            except Exception as gantry_error:
                logger.error(f"Error processing gantry: {str(gantry_error)}")
                continue

        return gantries_passed
        
    except Exception as e:
        logger.error(f"Error getting passed gantries: {str(e)}")
        return []

def is_weekday(datetime_str):
    dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
    return dt.weekday() < 5  # 0-4 are weekdays

def is_time_in_range(test_time_str, start_time_str, end_time_str):
    # Handle test_time_str that has date and time ('%Y-%m-%d %H:%M')
    test_time = datetime.strptime(test_time_str, "%Y-%m-%d %H:%M").time()
    # Handle start and end time strings in standard time format
    start_time = datetime.strptime(start_time_str, "%H.%M").time()
    end_time = datetime.strptime(end_time_str, "%H.%M").time()
    return start_time <= test_time <= end_time

def calculate_erp_charge(gantries_passed):
    try:
        erp_rates = retrieve_erp_rates()
        total_charge = 0.0

        for gantry in gantries_passed:
            weekday_bool = is_weekday(gantry[1])
            logger.debug(f"Processing gantry pass time: {gantry[1]}")
            
            if not weekday_bool or is_time_in_range(gantry[1], "10.01", "17.29"):
                logger.debug("No charge - weekend/holiday or off-peak hours")
                continue
                
            if gantry[0] in erp_rates:
                for time_interval, rate in erp_rates[gantry[0]]['charge_rates'].items():
                    start_time_str, end_time_str = time_interval.split('-')
                    if is_time_in_range(gantry[1], start_time_str, end_time_str):
                        total_charge += rate
                        logger.debug(f"Added charge {rate} for gantry {gantry[0]} at {time_interval}")
                        break
                        
        return round(total_charge, 2)
    except Exception as e:
        logger.error(f"Error calculating ERP charge: {str(e)}")
        return 0.0


# Example usage
#print(get_erp_data())
#print(retrieve_erp_rates())
'''erp_info = get_full_erp_info()
for gantry in erp_info:
    if 'coordinates' in gantry['info']:
        print(gantry)'''
#print(get_all_driving_metrics(39.8))
#retrieve_all_road_incidents()
#print(decode_polyline('}_p~F~ps|U_ulLnnqC_mqNvxq`@'))
#print(polyline_intersects_stringline('yjfGqrywRi_Ae{z@', (1.13, 103.82), (1.47, 103.82)))  # Example coordinates in Singapore
#print(get_list_of_passed_gantries('aaxFsk}xR`DlD'))
#print(calculate_erp_charge(get_list_of_passed_gantries('aaxFsk}xR`DlD')))

