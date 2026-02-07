from fastapi import APIRouter, Query, HTTPException
# app/api/maps_router.py
from fastapi import APIRouter, Query, HTTPException, Response
from typing import Literal
from app.services import maps_service
from app.schemas.directions import DirectionsResponse
from app.schemas.geocode import GeocodeResponse
from app.schemas.places import NearbyResponse


router = APIRouter(prefix="/maps", tags=["Maps"])
@router.get("/nearby",response_model=NearbyResponse)
async def nearby(
    location: str = Query(..., example="1.3521,103.8198"),
    radius: int = Query(1000, ge=1, le=50000),
    type: str | None = Query(None, example="restaurant"),
    keyword: str | None = Query(None, example="coffee"),
    rankby: Literal["distance"] | None = Query(None, description="Use 'distance' to sort by proximity (omit radius)"),
):
    # normalize "lat,lng"
    location = location.replace(" ", "")

    # rankby=distance rules (Google requires keyword or type, and no radius)
    if rankby == "distance":
        if not (keyword or type):
            raise HTTPException(status_code=400, detail="rankby=distance requires 'keyword' or 'type'")
        # radius must not be sent with rankby=distance
        radius = None

    return await maps_service.nearby_places(location=location, radius=radius, type=type, keyword=keyword, rankby=rankby)






# ----------------------------
# Nearby Places
# ----------------------------
@router.get("/nearby", response_model=NearbyResponse)
async def nearby(
   location: str = Query(..., example="1.3521,103.8198"),
   radius: int = Query(1000, ge=1, le=50000),
   type: str | None = Query(None, example="restaurant"),
   keyword: str | None = Query(None, example="coffee"),
   rankby: Literal["distance"] | None = Query(None, description="Use 'distance' to sort by proximity (omit radius)"),
):
   """Proxy to Google Places Nearby Search API (via maps_service)."""
   location = location.replace(" ", "")


   # rankby=distance rules (Google requires keyword or type, and no radius)
   if rankby == "distance":
       if not (keyword or type):
           raise HTTPException(status_code=400, detail="rankby=distance requires 'keyword' or 'type'")
       radius = None


   return await maps_service.nearby_places(
       location=location, radius=radius, type=type, keyword=keyword, rankby=rankby
   )




# ----------------------------
# Directions
# ----------------------------
@router.get("/directions")
async def directions_api(
    origin: str,
    destination: str,
    mode: str = "driving",
    departure_time: str | None = None,
    avoid: str | None = None,
    alternatives: bool = True
):
    print("[/maps/directions] START", {"origin": origin, "destination": destination, "mode": mode})
    results = await maps_service.directions(origin, destination, mode, departure_time, avoid, alternatives)
    # maps_service.directions returns a list of DirectionsResponse-shaped dicts (one per set).
    # For the mobile frontend we return the first set as the canonical response.
    if isinstance(results, list) and len(results) > 0:
        return results[0]
    return {"status": "ZERO_RESULTS", "routes": []}





@router.get("/geocode", response_model=GeocodeResponse)
async def geocode(
    address: str | None = Query(None, example="NTU, Singapore"),
    #latlng: str | None = Query(None, example="1.3483,103.6831")
 ):
    return await maps_service.geocode(address)#, latlng)


@router.get("/places-autocomplete")
async def places_autocomplete(input: str = Query(..., example="Nanyang Technological University"), sessiontoken: str | None = None):
    """Proxy endpoint for Google Places Autocomplete."""
    return await maps_service.places_autocomplete(input=input, sessiontoken=sessiontoken)


@router.get("/place-details")
async def place_details(place_id: str = Query(..., example="ChIJ..."), fields: str | None = None):
    """Proxy endpoint for Google Place Details (returns lat/lng by default)."""
    return await maps_service.place_details(place_id=place_id, fields=fields)



# ----------------------------
# Geocoding
# ----------------------------
@router.get("/geocode", response_model=GeocodeResponse)
async def geocode(
   address: str = Query(..., example="Nanyang Technological University, Singapore"),
):
   """Geocode an address string -> lat/lng."""
   return await maps_service.geocode(address)




# ----------------------------
# Places Autocomplete
# ----------------------------
@router.get("/places-autocomplete")
async def places_autocomplete(
   input: str = Query(..., example="Hougang Mall"),
   sessiontoken: str | None = None,
   location: str | None = Query(None, example="1.3521,103.8198", description="Lat,lng to restrict results"),
   radius: int | None = Query(None, ge=1, le=50000, example=10000, description="Radius in meters (with strictbounds)"),
):
   """Proxy endpoint for Google Places Autocomplete (supports optional location bias)."""
   return await maps_service.places_autocomplete(
       input=input, sessiontoken=sessiontoken, location=location, radius=radius
   )




# ----------------------------
# Place Details (lat/lng + photos)
# ----------------------------
@router.get("/place-details")
async def place_details(
   place_id: str = Query(..., example="ChIJyWEHuEmuEmsRm9hTkapTCrk"),
   fields: str | None = Query(None, description="Comma-separated fields (default = geometry,photos)"),
):
   """Proxy endpoint for Google Place Details (returns geometry + optional photos)."""
   return await maps_service.place_details(place_id=place_id, fields=fields)




# ----------------------------
# Place Photos (binary image)
# ----------------------------
@router.get("/photos")
async def photos(
   photo_reference: str = Query(..., description="Google Places photo_reference token"),
   maxwidth: int = Query(800, ge=1, le=1600),
   maxheight: int | None = Query(None, ge=1, le=1600),
):
   """
   Fetch a Place Photo from Google and return as image/jpeg or image/png.
   This endpoint streams binary content (for <Image> in frontend).
   """
   content, content_type = await maps_service.fetch_photo(
       photo_reference=photo_reference,
       maxwidth=maxwidth,
       maxheight=maxheight,
   )
   return Response(content=content, media_type=content_type)

# ----------------------------
# Traffic Incidents (TomTom)
# ----------------------------
@router.get("/traffic-incidents")
async def traffic_incidents(
    bbox: str = Query("103.6,1.20,104.1,1.50",
                      description="Bounding box: west,south,east,north (e.g., SG)"),
    time_validity: Literal["present", "future", "planned", "all"] = "present",
    language: str = "en-GB",
):
    """
    Road incidents (road works, accidents, closures) from TomTom Traffic API.
    NOTE: bbox order = west,south,east,north.
    """
    return await maps_service.tomtom_incidents(
        bbox=bbox, time_validity=time_validity, language=language
    )


