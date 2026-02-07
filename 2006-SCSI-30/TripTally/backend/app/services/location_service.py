from __future__ import annotations

"""
Service layer for Location business logic.

Handles location node creation, retrieval, updates, and deletion for the routing system.
"""
from typing import Optional
from app.models.location import Location
from app.ports.location_repo import LocationRepository


class LocationService:
    def __init__(self, repo: LocationRepository):
        self.repo = repo

    def create_location(self, name: str, lat: float, lng: float) -> Location:
        """
        Create a new location node.
        
        Args:
            name: Location name/description
            lat: Latitude coordinate
            lng: Longitude coordinate
            
        Returns:
            Newly created Location domain model
            
        Raises:
            ValueError: If coordinates are invalid
        """
        # Validate coordinates
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= lng <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        
        # Create domain model
        location = Location(
            id=0,  # Will be assigned by database
            name=name,
            lat=lat,
            lng=lng
        )
        
        # Persist through repository
        return self.repo.add(location)

    def get_location_by_id(self, location_id: int) -> Optional[Location]:
        """
        Get a location by ID.
        
        Args:
            location_id: Location's unique identifier
            
        Returns:
            Location domain model if found, None otherwise
        """
        return self.repo.get_by_id(location_id)

    def list_all_locations(self) -> list[Location]:
        """
        Get all locations.
        
        Returns:
            List of all Location domain models
        """
        return self.repo.list()

    def update_location(
        self,
        location_id: int,
        name: Optional[str] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None
    ) -> Location:
        """
        Update a location node.
        
        Args:
            location_id: Location's unique identifier
            name: New name (optional)
            lat: New latitude (optional)
            lng: New longitude (optional)
            
        Returns:
            Updated Location domain model
            
        Raises:
            ValueError: If location not found or coordinates are invalid
        """
        location = self.repo.get_by_id(location_id)
        if not location:
            raise ValueError("Location not found")
        
        # Update fields if provided
        if name is not None:
            location.name = name
        
        if lat is not None:
            if not (-90 <= lat <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            location.lat = lat
        
        if lng is not None:
            if not (-180 <= lng <= 180):
                raise ValueError("Longitude must be between -180 and 180")
            location.lng = lng
        
        return self.repo.update(location)

    def delete_location(self, location_id: int) -> bool:
        """
        Delete a location node.
        
        Args:
            location_id: Location's unique identifier
            
        Returns:
            True if location deleted successfully, False if location not found
        """
        return self.repo.delete(location_id)

    def search_locations_by_name(self, search_term: str) -> list[Location]:
        """
        Search locations by name (case-insensitive).
        
        Note: This is a basic implementation. For production, consider using
        a full-text search or geographic search service.
        
        Args:
            search_term: Search term for location name
            
        Returns:
            List of Location domain models matching the search
        """
        all_locations = self.repo.list()
        search_lower = search_term.lower()
        return [
            loc for loc in all_locations
            if search_lower in loc.name.lower()
        ]

    def get_nearby_locations(
        self,
        lat: float,
        lng: float,
        radius_km: float = 5.0
    ) -> list[Location]:
        """
        Get locations within a radius (simplified distance calculation).
        
        Note: This uses a simplified distance calculation. For production,
        consider using PostGIS or a proper geographic search service.
        
        Args:
            lat: Center latitude
            lng: Center longitude
            radius_km: Search radius in kilometers (default: 5km)
            
        Returns:
            List of Location domain models within radius
            
        Raises:
            ValueError: If coordinates are invalid
        """
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= lng <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if radius_km <= 0:
            raise ValueError("Radius must be positive")
        
        all_locations = self.repo.list()
        nearby = []
        
        for location in all_locations:
            # Simplified distance calculation (Haversine formula approximation)
            # For accurate distances, use geopy or PostGIS
            lat_diff = abs(location.lat - lat)
            lng_diff = abs(location.lng - lng)
            
            # Rough approximation: 1 degree ≈ 111 km
            distance_km = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111
            
            if distance_km <= radius_km:
                nearby.append(location)
        
        return nearby
