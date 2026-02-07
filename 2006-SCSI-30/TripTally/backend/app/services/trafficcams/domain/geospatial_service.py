"""
Geospatial Service
Handles geographic calculations and camera-route matching
"""

import math
from typing import List, Tuple
from .route_models import Point, LineString, RouteCameraInfo
from ..models import Camera


class GeospatialService:
    """Service for geographic calculations"""
    
    EARTH_RADIUS_KM = 6371.0
    DEFAULT_SEARCH_RADIUS_KM = 0.5  # 500 meters
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(dlon / 2) ** 2)
        
        c = 2 * math.asin(math.sqrt(a))
        
        return GeospatialService.EARTH_RADIUS_KM * c
    
    @staticmethod
    def point_to_line_distance(
        point_lat: float, 
        point_lon: float,
        line_start_lat: float,
        line_start_lon: float,
        line_end_lat: float,
        line_end_lon: float
    ) -> Tuple[float, float]:
        """
        Calculate minimum distance from point to line segment
        
        Args:
            point_lat, point_lon: Point coordinates
            line_start_lat, line_start_lon: Line segment start
            line_end_lat, line_end_lon: Line segment end
            
        Returns:
            Tuple of (distance_km, position_on_segment)
            position_on_segment: 0.0 (at start) to 1.0 (at end)
        """
        # Convert to radians
        px = math.radians(point_lon)
        py = math.radians(point_lat)
        x1 = math.radians(line_start_lon)
        y1 = math.radians(line_start_lat)
        x2 = math.radians(line_end_lon)
        y2 = math.radians(line_end_lat)
        
        # Calculate line segment vector
        dx = x2 - x1
        dy = y2 - y1
        
        # Handle degenerate case (line segment is a point)
        if dx == 0 and dy == 0:
            distance = GeospatialService.haversine_distance(
                point_lat, point_lon, line_start_lat, line_start_lon
            )
            return distance, 0.0
        
        # Calculate projection parameter t
        # t = 0 means closest to start, t = 1 means closest to end
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        
        # Find closest point on segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Convert back to degrees
        closest_lat = math.degrees(closest_y)
        closest_lon = math.degrees(closest_x)
        
        # Calculate distance
        distance = GeospatialService.haversine_distance(
            point_lat, point_lon, closest_lat, closest_lon
        )
        
        return distance, t
    
    def find_cameras_along_route(
        self,
        route: LineString,
        cameras: List[Camera],
        search_radius_km: float = None
    ) -> List[RouteCameraInfo]:
        """
        Find all cameras within search radius of route
        
        Args:
            route: Route as LineString
            cameras: List of available cameras
            search_radius_km: Search radius (default: 0.5 km)
            
        Returns:
            List of cameras sorted by position along route
        """
        if search_radius_km is None:
            search_radius_km = self.DEFAULT_SEARCH_RADIUS_KM
        
        route_cameras = []
        points = route.points
        
        if len(points) < 2:
            return []
        
        # Check each camera against each route segment
        for camera in cameras:
            min_distance = float('inf')
            best_position = 0.0
            
            # Check distance to each segment of the route
            for i in range(len(points) - 1):
                start = points[i]
                end = points[i + 1]
                
                distance, t = self.point_to_line_distance(
                    camera.latitude, camera.longitude,
                    start.latitude, start.longitude,
                    end.latitude, end.longitude
                )
                
                if distance < min_distance:
                    min_distance = distance
                    # Calculate global position on route (0.0 to 1.0)
                    segment_position = (i + t) / (len(points) - 1)
                    best_position = segment_position
            
            # If camera is within search radius, add it
            if min_distance <= search_radius_km:
                route_cameras.append(RouteCameraInfo(
                    camera_id=camera.camera_id,
                    latitude=camera.latitude,
                    longitude=camera.longitude,
                    distance_to_route=min_distance * 1000,  # Convert to meters
                    position_on_route=best_position
                ))
        
        # Sort by position along route
        route_cameras.sort(key=lambda c: c.position_on_route)
        
        return route_cameras
    
    @staticmethod
    def calculate_route_length(route: LineString) -> float:
        """
        Calculate total route length
        
        Args:
            route: Route as LineString
            
        Returns:
            Total length in kilometers
        """
        total_length = 0.0
        points = route.points
        
        for i in range(len(points) - 1):
            distance = GeospatialService.haversine_distance(
                points[i].latitude, points[i].longitude,
                points[i + 1].latitude, points[i + 1].longitude
            )
            total_length += distance
        
        return total_length
