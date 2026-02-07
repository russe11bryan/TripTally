 # app/services/maps_service.py
import asyncio
import httpx
from typing import Dict, Any, Optional
from cachetools import TTLCache
from fastapi import HTTPException, params
from app.core.config import GOOGLE_MAPS_API_KEY, REQUEST_TIMEOUT, CACHE_TTL_SECONDS
# app/services/maps_service.py
import asyncio
import html
import re
from typing import Dict, Any, Optional, List, Tuple


import httpx
from cachetools import TTLCache
from fastapi import HTTPException


from app.core.config import GOOGLE_MAPS_API_KEY, REQUEST_TIMEOUT, CACHE_TTL_SECONDS
import os
TOMTOM_KEY = os.getenv("TOMTOM_KEY")



BASE = "https://maps.googleapis.com"
cache = TTLCache(maxsize=1000, ttl=CACHE_TTL_SECONDS)

async def _get_with_retries(url: str, params: Dict[str, Any], retries: int = 2) -> httpx.Response:
    last_exc = None
    for attempt in range(retries + 1):
        try:
            timeout = httpx.Timeout(connect=5.0, read=12.0, write=5.0, pool=5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, params=params)
            if resp.status_code in (429, 500, 502, 503, 504):
                # transient; backoff and retry
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
            return resp
        except httpx.RequestError as e:
            last_exc = e
            await asyncio.sleep(0.5 * (attempt + 1))
    raise HTTPException(status_code=502, detail=f"Upstream error: {str(last_exc)}")


async def gget(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    params = dict(params or {})
    params["key"] = GOOGLE_MAPS_API_KEY
    url = f"{BASE}{path}"
    ck = (path, tuple(sorted(params.items())))
    if ck in cache:
        return cache[ck]
    resp = await _get_with_retries(url, params)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Google error {resp.status_code}: {resp.text}")
    data = resp.json()
    status = data.get("status")

    
    if status in (None, "OK", "ZERO_RESULTS"):
        cache[ck] = data
        return data

    # Client issues (bad params)
    if status in ("INVALID_REQUEST"):
        raise HTTPException(status_code=400, detail=data)

    # Quota / key / permission issues
    if status in ("OVER_QUERY_LIMIT", "REQUEST_DENIED"):
        # 429 for quota, 403 also ok; pick what you prefer
        raise HTTPException(status_code=429, detail=data)

    # Other Google errors → treat as upstream failure
    raise HTTPException(status_code=502, detail=data)
    cache[ck] = data
    return data

# Public service functions
"""async def nearby_places(location: str, radius: int = 1000, type: str | None = None, keyword: str | None = None):
    params = {"location": location, "radius": radius}
    if type: params["type"] = type
    if keyword: params["keyword"] = keyword
    return await gget("/maps/api/place/nearbysearch/json", params)"""

from typing import Optional, Dict, Any
from fastapi import HTTPException

async def nearby_places(
    location: str,
    radius: Optional[int] = 1000,
    type: Optional[str] = None,
    keyword: Optional[str] = None,
    rankby: Optional[str] = None,   # NEW
) -> Dict[str, Any]:
    # normalize "lat,lng"
    location = location.replace(" ", "")
    params: Dict[str, Any] = {"location": location}

    # choose mode
    if rankby == "distance":
        params["rankby"] = "distance"
        if not (keyword or type):
            raise HTTPException(status_code=400, detail="rankby=distance requires 'keyword' or 'type'")
        # radius must NOT be sent with rankby=distance
    else:
        params["radius"] = radius or 1000

    if type:
        params["type"] = type
    if keyword:
        params["keyword"] = keyword

    data = await gget("/maps/api/place/nearbysearch/json", params)

    places_out = []
    for p in data.get("results", []):
        loc = (p.get("geometry") or {}).get("location") or {}
        lat, lng = loc.get("lat"), loc.get("lng")
        if lat is None or lng is None:
            continue  # skip malformed results instead of crashing

        places_out.append({
            "name": p.get("name"),
            "place_id": p.get("place_id"),
            "lat": float(lat),
            "lng": float(lng),
            "address": p.get("vicinity"),
            "rating": p.get("rating"),
            "user_ratings_total": p.get("user_ratings_total"),
            "types": p.get("types"),
            "open_now": (p.get("opening_hours") or {}).get("open_now"),
            "icon": p.get("icon"),
        })

    return {"status": data.get("status"), "routes": places_out}

"""async def directions(origin: str, destination: str, mode: str = "driving", departure_time: str | None = None, avoid: str | None = None):
    params = {"origin": origin, "destination": destination, "mode": mode}
    if departure_time: params["departure_time"] = departure_time
    if avoid: params["avoid"] = avoid
    return await gget("/maps/api/directions/json", params)"""


#getting multiple routes with parsing example
# maps_service.py
from typing import Optional, Dict, List
import re

TAG_RE = re.compile(r"<[^>]+>")

def strip_html(s: Optional[str]) -> str:
    return TAG_RE.sub("", s or "").replace("&nbsp;", " ").replace("&amp;", "&").strip()




# ---------------------------
# Low-level HTTP helpers
# ---------------------------
async def _get_with_retries(url: str, params: Dict[str, Any], retries: int = 2) -> httpx.Response:
   """JSON (API) GET with limited retries/backoff."""
   last_exc = None
   for attempt in range(retries + 1):
       try:
           read_to = REQUEST_TIMEOUT if isinstance(REQUEST_TIMEOUT, (int, float)) else 12.0
           timeout = httpx.Timeout(connect=5.0, read=read_to, write=5.0, pool=5.0)
           async with httpx.AsyncClient(timeout=timeout) as client:
               resp = await client.get(url, params=params)
           if resp.status_code in (429, 500, 502, 503, 504):
               await asyncio.sleep(0.5 * (attempt + 1))
               continue
           return resp
       except httpx.RequestError as e:
           last_exc = e
           await asyncio.sleep(0.5 * (attempt + 1))
   raise HTTPException(status_code=502, detail=f"Upstream error: {str(last_exc)}")




async def _get_binary_with_retries(url: str, params: Dict[str, Any], retries: int = 2) -> httpx.Response:
   """Binary (image) GET with limited retries/backoff. Follows redirects."""
   last_exc = None
   for attempt in range(retries + 1):
       try:
           read_to = REQUEST_TIMEOUT if isinstance(REQUEST_TIMEOUT, (int, float)) else 12.0
           timeout = httpx.Timeout(connect=5.0, read=read_to, write=5.0, pool=5.0)
           async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
               resp = await client.get(url, params=params)
           if resp.status_code in (429, 500, 502, 503, 504):
               await asyncio.sleep(0.5 * (attempt + 1))
               continue
           return resp
       except httpx.RequestError as e:
           last_exc = e
           await asyncio.sleep(0.5 * (attempt + 1))
   raise HTTPException(status_code=502, detail=f"Upstream error: {str(last_exc)}")




async def gget(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
   """Google JSON API GET with API key + caching + status normalization."""
   params = dict(params or {})
   params["key"] = GOOGLE_MAPS_API_KEY
   url = f"{BASE}{path}"
   ck = (path, tuple(sorted(params.items())))
   if ck in cache:
       return cache[ck]
   resp = await _get_with_retries(url, params)
   if resp.status_code != 200:
       raise HTTPException(status_code=502, detail=f"Google error {resp.status_code}: {resp.text}")
   data = resp.json()
   status = data.get("status")


   if status in (None, "OK", "ZERO_RESULTS"):
       cache[ck] = data
       return data


   # Client issues (bad params)
   if status in ("INVALID_REQUEST",):
       raise HTTPException(status_code=400, detail=data)


   # Quota / key / permission issues
   if status in ("OVER_QUERY_LIMIT", "REQUEST_DENIED"):
       raise HTTPException(status_code=429, detail=data)


   # Other Google errors → treat as upstream failure
   raise HTTPException(status_code=502, detail=data)




# ---------------------------
# Helpers
# ---------------------------
def strip_html(s: Optional[str]) -> str:
   if not s:
       return ""
   # remove tags then unescape entities
   return html.unescape(re.sub(r"<[^>]+>", "", s))




def normalize_hex(c) -> Optional[str]:
   if not c:
       return None
   c = str(c).strip()
   return c if c.startswith("#") else f"#{c}"




# ---------------------------
# Places: Nearby Search
# ---------------------------
async def nearby_places(
   location: str,
   radius: Optional[int] = 1000,
   type: Optional[str] = None,
   keyword: Optional[str] = None,
   rankby: Optional[str] = None,
) -> Dict[str, Any]:
   """Places Nearby Search. Returns {status, results:[...] } with first-photo metadata."""
   # normalize "lat,lng"
   location = location.replace(" ", "")
   params: Dict[str, Any] = {"location": location}


   # choose mode
   if rankby == "distance":
       params["rankby"] = "distance"
       if not (keyword or type):
           raise HTTPException(status_code=400, detail="rankby=distance requires 'keyword' or 'type'")
       # radius must NOT be sent with rankby=distance
   else:
       params["radius"] = radius or 1000


   if type:
       params["type"] = type
   if keyword:
       params["keyword"] = keyword


   data = await gget("/maps/api/place/nearbysearch/json", params)


   places_out: List[Dict[str, Any]] = []
   for p in data.get("results", []) or []:
       loc = (p.get("geometry") or {}).get("location") or {}
       lat, lng = loc.get("lat"), loc.get("lng")
       if lat is None or lng is None:
           continue  # skip malformed results instead of crashing


       photos = p.get("photos") or []
       first_photo = photos[0] if photos else {}


       places_out.append({
           "name": p.get("name"),
           "place_id": p.get("place_id"),
           "lat": float(lat),
           "lng": float(lng),
           "address": p.get("vicinity"),
           "rating": p.get("rating"),
           "user_ratings_total": p.get("user_ratings_total"),
           "types": p.get("types"),
           "open_now": (p.get("opening_hours") or {}).get("open_now"),
           "icon": p.get("icon"),
           "photo": ({
               "photo_reference": first_photo.get("photo_reference"),
               "width": first_photo.get("width"),
               "height": first_photo.get("height"),
               "html_attributions": first_photo.get("html_attributions"),
           } if first_photo else None),
       })


   return {"status": data.get("status"), "routes": places_out}


"""async def directions(origin: str, destination: str, mode: str = "driving", departure_time: str | None = None, avoid: str | None = None):
   params = {"origin": origin, "destination": destination, "mode": mode}
   if departure_time: params["departure_time"] = departure_time
   if avoid: params["avoid"] = avoid
   return await gget("/maps/api/directions/json", params)"""




from typing import Optional, Dict, List
import re


TAG_RE = re.compile(r"<[^>]+>")


from typing import Optional, Dict, List
import re
import html


from typing import Optional, Dict, List
import re


# --- helpers you were using but hadn't defined ---
def strip_html(html: Optional[str]) -> str:
   if not html:
       return ""
   # quick & safe-ish HTML -> text
   text = re.sub(r"<br\s*/?>", " ", html, flags=re.I)
   text = re.sub(r"<div\s*/?>", " ", text, flags=re.I)
   text = re.sub(r"<.*?>", "", text)
   return re.sub(r"\s+", " ", text).strip()


def normalize_hex(val: Optional[str]) -> Optional[str]:
   """
   Accepts '#189e4a' or '189e4a' and returns a validated '#RRGGBB' (or '#RRGGBBAA').
   Returns None if it doesn't look like hex.
   """
   if not isinstance(val, str):
       return None
   s = val.strip()
   if not s:
       return None
   if not s.startswith("#"):
       s = f"#{s}"
   if re.fullmatch(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{8}|[0-9a-fA-F]{3})", s):
       return s
   return None


# ---------------------------
# Directions (with per-step parsing + transit colors)
# ---------------------------
from typing import Optional, Dict, List
import re


TAG_RE = re.compile(r"<[^>]+>")


def strip_html(s: Optional[str]) -> str:
    return TAG_RE.sub("", s or "").replace("&nbsp;", " ").replace("&amp;", "&").strip()


async def directions(
    origin: str,
    destination: str,
    mode: str = "driving",
    departure_time: Optional[str] = None,
    avoid: Optional[str] = None,
    alternatives: bool = True
):
    params = {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "alternatives": str(alternatives).lower(),
    }
    # traffic ETA and transit schedules need a departure_time
    if mode in ("driving", "transit") and departure_time:
        params["departure_time"] = departure_time
    if avoid:
        params["avoid"] = avoid


    print("[maps_service] calling Google Directions with", params)
    data = await gget("/maps/api/directions/json", params)
    print("[maps_service] Google responded with status", data.get("status"))


    # ---- prepare a function to build one dataset ----
    def build_route_set(data: Dict):
        routes_out = []             # [{route_id, summary}]
        distances = []              # [meters]
        distances_text = []         # ["29.8 km"]
        durations = []              # [seconds]
        durations_text = []         # ["35 mins"]
        durations_in_traffic = []   # [seconds or None]
        durations_in_traffic_text = []  # ["34 mins" or None]
        polylines = []              # [encoded overview polyline]
        start_locations = []        # [{lat,lng}]
        end_locations = []          # [{lat,lng}]
        start_addresses = []        # ["..."]
        end_addresses = []          # ["..."]
        fares = []                  # ["$2.10" or None]
        route_steps = []            # [[ step, step, ... ] per route]


        for i, route in enumerate(data.get("routes", []) or []):
            legs = route.get("legs") or []
            if not legs:
                continue
            leg = legs[0]


            distance_val = (leg.get("distance") or {}).get("value")
            distance_txt = (leg.get("distance") or {}).get("text")
            duration_val = (leg.get("duration") or {}).get("value")
            duration_txt = (leg.get("duration") or {}).get("text")


            dit = leg.get("duration_in_traffic") or {}
            duration_in_traffic_val = dit.get("value")
            duration_in_traffic_txt = dit.get("text")


            start_loc = leg.get("start_location") or None
            end_loc = leg.get("end_location") or None
            encoded_poly = (route.get("overview_polyline") or {}).get("points")


            # ---- NEW: parse per-step instructions ----
            steps_out = []
            for st in leg.get("steps", []) or []:
                step_distance_txt = (st.get("distance") or {}).get("text", "") or ""
                step_duration_txt = (st.get("duration") or {}).get("text", "") or ""
                step_poly = (st.get("polyline") or {}).get("points", "") or ""
                travel_mode = st.get("travel_mode")  # DRIVING/WALKING/TRANSIT/BICYCLING
                maneuver = st.get("maneuver")  # e.g. "turn-left" (driving only)
                html_instr = st.get("html_instructions")
                instruction = strip_html(html_instr)


                # Transit extras (only present when travel_mode == "TRANSIT")
                td = st.get("transit_details") or {}
                line = (td.get("line") or {})
                vehicle = (line.get("vehicle") or {})
                dep_stop = (td.get("departure_stop") or {})
                arr_stop = (td.get("arrival_stop") or {})
                dep_time = (td.get("departure_time") or {})
                arr_time = (td.get("arrival_time") or {})


                steps_out.append({
                    "instruction": instruction,                # clean text
                    "html_instruction": html_instr or "",      # original HTML (optional)
                    "travel_mode": travel_mode,                # "WALKING" | "TRANSIT" | ...
                    "maneuver": maneuver,                      # driving-only
                    "distance_text": step_distance_txt,
                    "duration_text": step_duration_txt,
                    "polyline": step_poly,                     # step-level polyline
                    "start_location": st.get("start_location") or None,
                    "end_location": st.get("end_location") or None,


                    # Transit details (null for non-transit steps)
                    "transit_details": {
                        "headsign": td.get("headsign"),
                        "num_stops": td.get("num_stops"),
                        "line_name": line.get("name"),
                        "line_short_name": line.get("short_name"),
                        "vehicle_type": vehicle.get("type"),   # BUS, HEAVY_RAIL, etc.
                        "vehicle_name": vehicle.get("name"),
                        "departure_stop": dep_stop.get("name"),
                        "arrival_stop": arr_stop.get("name"),
                        "departure_time_text": dep_time.get("text"),
                        "arrival_time_text": arr_time.get("text"),
                        "line_color": normalize_hex(line.get("color")),           # Add hex color
                        "line_text_color": normalize_hex(line.get("text_color")), # Add text color
                    } if travel_mode == "TRANSIT" else None
                })



            routes_out.append({"route_id": i, "summary": route.get("summary")})
            distances.append(distance_val)
            distances_text.append(distance_txt)
            durations.append(duration_val)
            durations_text.append(duration_txt)
            durations_in_traffic.append(duration_in_traffic_val)
            durations_in_traffic_text.append(duration_in_traffic_txt)
            polylines.append(encoded_poly)
            start_locations.append(start_loc)
            end_locations.append(end_loc)
            start_addresses.append(leg.get("start_address"))
            end_addresses.append(leg.get("end_address"))
            fares.append((route.get("fare") or {}).get("text"))  # transit-only typically
            route_steps.append(steps_out)

            # (Optional) You could also collect route warnings:
            # warnings = route.get("warnings", [])


            # (Optional) You could also collect route warnings:
            # warnings = route.get("warnings", [])


        return {
            "status": data.get("status"),
            "route_summaries": routes_out,
            "distances": distances,
            "distances_text": distances_text,
            "durations": durations,
            "durations_text": durations_text,
            "durations_in_traffic": durations_in_traffic,
            "durations_in_traffic_text": durations_in_traffic_text,
            "polylines": polylines,
            "start_locations": start_locations,
            "end_locations": end_locations,
            "start_addresses": start_addresses,
            "end_addresses": end_addresses,
            "fares": fares,
            "steps_by_route": route_steps,   # NEW
        }


    # ---- produce multiple sets (if you really need it) ----
    sets_out = []
    sets_out.append(build_route_set(data))
    # If you want only one set, delete the next line:
    # sets_out.append(build_route_set(data))  # duplicate or new call if needed


    # ---- transform into DirectionsResponse-like objects ----
    transformed = []
    for s in sets_out:
        polylines = s.get("polylines", []) or []
        summaries = s.get("route_summaries", []) or []
        distances = s.get("distances", []) or []
        distances_text = s.get("distances_text", []) or []
        durations = s.get("durations", []) or []
        durations_text = s.get("durations_text", []) or []
        dit_vals = s.get("durations_in_traffic", []) or []
        dit_text = s.get("durations_in_traffic_text", []) or []
        start_locations = s.get("start_locations", []) or []
        end_locations = s.get("end_locations", []) or []
        start_addresses = s.get("start_addresses", []) or []
        end_addresses = s.get("end_addresses", []) or []
        fares = s.get("fares", []) or []
        steps_by_route = s.get("steps_by_route", []) or []


        routes = []
        count = max(len(polylines), len(summaries))
        for i in range(count):
            routes.append({
                "route_id": i,
                "summary": (summaries[i]["summary"] if i < len(summaries) and isinstance(summaries[i], dict) else None),
                "distance": distances[i] if i < len(distances) else None,
                "distance_text": distances_text[i] if i < len(distances_text) else None,
                "duration": durations[i] if i < len(durations) else None,
                "duration_text": durations_text[i] if i < len(durations_text) else None,
                "duration_in_traffic": dit_vals[i] if i < len(dit_vals) else None,
                "duration_in_traffic_text": dit_text[i] if i < len(dit_text) else None,
                "encoded_polyline": polylines[i] if i < len(polylines) else None,
                "start_address": start_addresses[i] if i < len(start_addresses) else None,
                "end_address": end_addresses[i] if i < len(end_addresses) else None,
                "start_location": start_locations[i] if i < len(start_locations) else None,
                "end_location": end_locations[i] if i < len(end_locations) else None,
                "fare": fares[i] if i < len(fares) else None,
                "steps": steps_by_route[i] if i < len(steps_by_route) else [],  # NEW
            })


        overview = polylines[0] if polylines else None
        destination_obj = None
        if end_locations and end_locations[0]:
            el = end_locations[0]
            if isinstance(el, dict) and "lat" in el and "lng" in el:
                destination_obj = {"lat": el.get("lat"), "lng": el.get("lng")}


        transformed.append({
            "status": s.get("status"),
            "routes": routes,
            "overview_polyline": overview,
            "destination": destination_obj,
            "distance_meters": distances[0] if distances else None,
            "duration_seconds": durations[0] if durations else None,
            "distance_text": distances_text[0] if distances_text else None,
            "duration_text": durations_text[0] if durations_text else None,
        })


    return transformed



"""async def geocode(address: str | None = None, latlng: str | None = None):
    if not (address or latlng):
        raise HTTPException(status_code=400, detail="Provide address OR latlng")
    params = {}
    if address: params["address"] = address
    if latlng: params["latlng"] = latlng
    return await gget("/maps/api/geocode/json", params)"""


 #extracting only one address from geocode results for simplicity

async def geocode(address: str):
    params = {"address": address}
    data = await gget("/maps/api/geocode/json", params)
    results = data.get("results", [])

    if not results:
        return {"results": [], "status": "ZERO_RESULTS"}

    result = results[0]
    loc = result["geometry"]["location"]

    return {
        "status": data.get("status", "OK"),
        "results": [
            {
                "formatted_address": result["formatted_address"],
                "lat": loc["lat"],
                "lng": loc["lng"],
                "place_id": result.get("place_id"),
            }
        ],
    }


async def places_autocomplete(input: str, sessiontoken: str | None = None):
    """Proxy to Google Places Autocomplete API.

    Returns a dict containing 'status' and 'predictions' (matching Google shape
    enough for frontend usage).
    """
    params = {"input": input}
    if sessiontoken:
        params["sessiontoken"] = sessiontoken

    data = await gget("/maps/api/place/autocomplete/json", params)

    return {"status": data.get("status"), "predictions": data.get("predictions", [])}


async def place_details(place_id: str, fields: str | None = None):
    """Proxy to Google Place Details API. Returns simplified lat/lng and status.

    The `fields` parameter can be used to restrict response; default to geometry.
    """
    params = {"place_id": place_id, "fields": fields or "geometry"}
    data = await gget("/maps/api/place/details/json", params)

    result = data.get("result") or {}
    geometry = (result.get("geometry") or {}).get("location") or {}
    lat = geometry.get("lat")
    lng = geometry.get("lng")

    return {"status": data.get("status"), "lat": lat, "lng": lng, "result": result}



async def geocode(address: str):
    params = {"address": address}
    data = await gget("/maps/api/geocode/json", params)
    results = data.get("results", [])

    if not results:
        return {"results": [], "status": "ZERO_RESULTS"}

    result = results[0]
    loc = result["geometry"]["location"]

    return {
        "status": data.get("status", "OK"),
        "results": [
            {
                "formatted_address": result["formatted_address"],
                "lat": loc["lat"],
                "lng": loc["lng"],
                "place_id": result.get("place_id"),
            }
        ],
    }


async def places_autocomplete(input: str, sessiontoken: str | None = None):
    """Proxy to Google Places Autocomplete API.

    Returns a dict containing 'status' and 'predictions' (matching Google shape
    enough for frontend usage).
    """
    params = {"input": input}
    if sessiontoken:
        params["sessiontoken"] = sessiontoken

    data = await gget("/maps/api/place/autocomplete/json", params)

    return {"status": data.get("status"), "predictions": data.get("predictions", [])}


async def place_details(place_id: str, fields: str | None = None):
    """Proxy to Google Place Details API. Returns simplified lat/lng and status.

    The `fields` parameter can be used to restrict response; default to geometry.
    """
    params = {"place_id": place_id, "fields": fields or "geometry"}
    data = await gget("/maps/api/place/details/json", params)

    result = data.get("result") or {}
    geometry = (result.get("geometry") or {}).get("location") or {}
    lat = geometry.get("lat")
    lng = geometry.get("lng")

    return {"status": data.get("status"), "lat": lat, "lng": lng, "result": result}



async def geocode(address: str):
    params = {"address": address}
    data = await gget("/maps/api/geocode/json", params)
    results = data.get("results", [])

    if not results:
        return {"results": [], "status": "ZERO_RESULTS"}

    result = results[0]
    loc = result["geometry"]["location"]

    return {
        "status": data.get("status", "OK"),
        "results": [
            {
                "formatted_address": result["formatted_address"],
                "lat": loc["lat"],
                "lng": loc["lng"],
                "place_id": result.get("place_id"),
            }
        ],
    }




# ---------------------------
# Geocoding
# ---------------------------
async def geocode(address: str) -> Dict[str, Any]:
   params = {"address": address}
   data = await gget("/maps/api/geocode/json", params)
   results = data.get("results", [])


   if not results:
       return {"results": [], "status": "ZERO_RESULTS"}


   result = results[0]
   loc = (result.get("geometry") or {}).get("location") or {}


   return {
       "status": data.get("status", "OK"),
       "results": [
           {
               "formatted_address": result.get("formatted_address"),
               "lat": loc.get("lat"),
               "lng": loc.get("lng"),
               "place_id": result.get("place_id"),
           }
       ],
   }




# ---------------------------
# Places: Autocomplete (with optional location bias)
# ---------------------------
async def places_autocomplete(
   input: str,
   sessiontoken: Optional[str] = None,
   location: Optional[str] = None,
   radius: Optional[int] = None,
) -> Dict[str, Any]:
   """
   Proxy to Google Places Autocomplete API with optional location bias.
   Returns {status, predictions}
   """
   params: Dict[str, Any] = {"input": input}
   if sessiontoken:
       params["sessiontoken"] = sessiontoken
   if location:
       params["location"] = location  # "lat,lng"
       params["radius"] = radius if radius else 10000  # default 10km
       params["strictbounds"] = "true"


   data = await gget("/maps/api/place/autocomplete/json", params)
   return {"status": data.get("status"), "predictions": data.get("predictions", [])}




# ---------------------------
# Places: Details (include photos by default)
# ---------------------------
async def place_details(place_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
   """Place Details → returns {status, lat, lng, photos, result}."""
   params = {"place_id": place_id, "fields": fields or "geometry,photos"}
   data = await gget("/maps/api/place/details/json", params)


   result = data.get("result") or {}
   geometry = (result.get("geometry") or {}).get("location") or {}
   lat = geometry.get("lat")
   lng = geometry.get("lng")


   raw_photos = result.get("photos") or []
   photos = [
       {
           "photo_reference": p.get("photo_reference"),
           "width": p.get("width"),
           "height": p.get("height"),
           "html_attributions": p.get("html_attributions"),
       }
       for p in raw_photos
   ]


   return {
       "status": data.get("status"),
       "lat": lat,
       "lng": lng,
       "photos": photos,
       "result": result,  # keep full result in case frontend needs extras
   }




# ---------------------------
# Place Photos: binary fetch for router to return
# ---------------------------
async def fetch_photo(
   photo_reference: str,
   maxwidth: int = 800,
   maxheight: Optional[int] = None,
) -> Tuple[bytes, str]:
   """
   Download a Place Photo (binary) so the router can return Response(...).
   Returns (content_bytes, content_type).
   """
   if not photo_reference:
       raise HTTPException(status_code=400, detail="Missing photo_reference")


   params: Dict[str, Any] = {
       "key": GOOGLE_MAPS_API_KEY,
       "photo_reference": photo_reference,
       "maxwidth": maxwidth,
   }
   if maxheight:
       params["maxheight"] = maxheight


   url = f"{BASE}/maps/api/place/photo"
   resp = await _get_binary_with_retries(url, params)


   if resp.status_code != 200:
       raise HTTPException(status_code=502, detail=f"Google photo error {resp.status_code}")


   content_type = resp.headers.get("content-type", "image/jpeg")
   return resp.content, content_type


## tom tom API
###--------------------------------------------------------------------------------------
async def tomtom_incidents(
    bbox: str,                     # "west,south,east,north" (e.g. "103.6,1.20,104.1,1.50")
    time_validity: str = "present",# present | future | planned | all
    language: str = "en-GB",
):
    """
    Fetch traffic incidents (road works, accidents, closures) from TomTom Traffic API v5.
    Returns TomTom's JSON (key 'incidents': [...]).
    """
    if not TOMTOM_KEY:
        raise HTTPException(status_code=500, detail="Missing TOMTOM_KEY environment variable")

    # Build request
    url = "https://api.tomtom.com/traffic/services/5/incidentDetails"
    params = {
        "key": TOMTOM_KEY,
        "bbox": bbox,                         # required; order matters (W,S,E,N)
        "language": language,
        "timeValidityFilter": time_validity,  # present/future/planned/all
        # Keep payload lean; add/remove fields as you wish
        "fields": "{incidents{type,geometry{type,coordinates},properties{"
                  "iconCategory,magnitudeOfDelay,roadNumbers,startTime,endTime,"
                  "from,to,events{description},probabilityOfOccurrence}}}"
    }

    # Cache key compatible with your TTLCache
    ck = ("tomtom_incidents", tuple(sorted(params.items())))
    if ck in cache:
        return cache[ck]

    resp = await _get_with_retries(url, params)
    if resp.status_code != 200:
        error_detail = f"TomTom API Error: {resp.status_code} - {resp.text}"
        print(f"TomTom Incidents API failed: {error_detail}")
        raise HTTPException(status_code=resp.status_code, detail=error_detail)

    data = resp.json() or {}
    # TomTom returns {"incidents": [...]} — store as-is
    cache[ck] = data
    return data








