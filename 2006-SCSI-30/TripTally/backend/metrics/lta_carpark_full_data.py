import http.client
import csv
import json
import os

def retrieve_api_data():

    conn = http.client.HTTPSConnection("datamall2.mytransport.sg")

    headers = { 'AccountKey': 
            "REDACTED_LTA_ACCOUNT_KEY==",
            'accept': 'application/json'
                }

    conn.request("GET", "/ltaodataservice/CarParkAvailabilityv2", headers=headers)

    res = conn.getresponse()
    data = res.read()

    data = data.decode("utf-8")

    parsed_data = json.loads(data)

    #print(parsed_data)

    '''with open('output1.json', 'w') as outfile: #to view json structure
        json.dump(parsed_data, outfile, indent=4)'''

    return parsed_data

def retrieve_cp_rates():
    carpark_rates = {}
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "CarparkRates.csv")
    with open(csv_path, "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header line
        for parts in reader:
            if len(parts) >= 4:
                carpark_name = parts[0]
                rates_info = {
                    "weekday_rate_1": parts[2],
                    "weekday_rate_2": parts[3],
                    "saturday_rates": parts[4],
                    "sunday_public_holiday_rates": parts[5]
                }
                carpark_rates[carpark_name] = rates_info
                if rates_info["saturday_rates"] == "Same as weekdays":
                    rates_info["saturday_rates"] = rates_info["weekday_rate_1"] + " / " + rates_info["weekday_rate_2"]
    return carpark_rates

def retrieve_live_carpark_data_by_latlong(cp_lat, cp_long):

    data = retrieve_api_data()
    carpark_info = {}

    for entry in data["value"]:
        location_str = entry["Location"]
        current_lat, current_long = map(float, location_str.split(" "))
        #print(current_lat, current_long)
        if cp_long == current_long and cp_lat == current_lat:
            carpark_info["car_park_ID"] = entry["CarParkID"]
            carpark_info["area"] = entry["Area"]
            carpark_info["development"] = entry["Development"]
            carpark_info["available_lots"] = int(entry["AvailableLots"])
            carpark_info["agency"] = entry["Agency"]
            return carpark_info
        
    raise ValueError("No carpark found at the provided latitude and longitude.")

def get_nearby_carparks(dest_lat, dest_long, radius_meters=1500):

    data = retrieve_api_data()
    cp_rates = retrieve_cp_rates()
    nearby_carparks = []

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
            carpark_info = {
                "car_park_ID": entry["CarParkID"],
                "area": entry["Area"],
                "development": entry["Development"],
                "available_lots": int(entry["AvailableLots"]),
                "agency": entry["Agency"],
                "distance_meters": int(distance),
                "latitude": current_lat,
                "longitude": current_long
            }
            nearby_carparks.append(carpark_info)

        nearby_carparks = nearby_carparks[:10]

        for carpark in nearby_carparks:

            if carpark["development"] in cp_rates.keys():
                carpark["weekday_rate_1"] = cp_rates.get(carpark["development"]).get("weekday_rate_1")
                carpark["weekday_rate_2"] = cp_rates.get(carpark["development"]).get("weekday_rate_2")
                carpark["saturday_rates"] = cp_rates.get(carpark["development"]).get("saturday_rates")
                carpark["sunday_public_holiday_rates"] = cp_rates.get(carpark["development"]).get("sunday_public_holiday_rates")

            else:
                carpark["weekday_rate_1"] = "N/A"
                carpark["weekday_rate_2"] = "N/A"
                carpark["saturday_rates"] = "N/A"
                carpark["sunday_public_holiday_rates"] = "N/A"

    nearby_carparks.sort(key=lambda x: x["distance_meters"])
    return nearby_carparks

#print(retrieve_cp_rates()) #example usage      
print(get_nearby_carparks(1.3010351, 103.8387588)) #example usage
#print(retrieve_live_carpark_data_by_latlong(1.291008686889873, 103.83251535744483)) #example usage

    

