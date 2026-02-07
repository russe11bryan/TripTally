from __future__ import annotations

"""
Service layer for Route business logic.

Handles route creation, retrieval, updates, and management for different route types
(recommended, alternate, user-suggested).
"""
from typing import Optional
from app.models.route import Route, UserSuggestedRoute
from app.schemas.route import RouteCreate, UserSuggestedRouteCreate, RouteUpdate
from app.ports.route_repo import RouteRepository


def create_route(route_repo: RouteRepository, data: RouteCreate) -> Route:
    """
    Create a new route.
    
    Args:
        route_repo: Repository for route persistence
        data: Route creation data
        
    Returns:
        Newly created Route domain model
        
    Raises:
        ValueError: If invalid subtype or data validation fails
    """
    valid_subtypes = ["recommended", "alternate", "user_suggested"]
    if data.subtype not in valid_subtypes:
        raise ValueError(f"Invalid subtype. Must be one of: {', '.join(valid_subtypes)}")
    
    # Create domain model
    route = Route(
        id=0,  # Will be assigned by database
        start_location_id=data.start_location_id,
        end_location_id=data.end_location_id,
        subtype=data.subtype,
        transport_mode=data.transport_mode,
        route_line=data.route_line,
        metrics_id=data.metrics_id,
        type="route"
    )
    
    # Persist through repository
    return route_repo.add(route)


def create_user_suggested_route(
    route_repo: RouteRepository,
    data: UserSuggestedRouteCreate
) -> UserSuggestedRoute:
    """
    Create a new user-suggested route.
    
    Args:
        route_repo: Repository for route persistence
        data: User-suggested route creation data with user_id
        
    Returns:
        Newly created UserSuggestedRoute domain model
        
    Raises:
        ValueError: If user_id is missing
    """
    if not data.user_id:
        raise ValueError("user_id is required for user-suggested routes")
    
    # Create domain model
    route = UserSuggestedRoute(
        id=0,  # Will be assigned by database
        start_location_id=data.start_location_id,
        end_location_id=data.end_location_id,
        subtype="user_suggested",
        transport_mode=data.transport_mode,
        route_line=data.route_line,
        metrics_id=data.metrics_id,
        user_id=data.user_id,
        type="user_suggested"
    )
    
    # Persist through repository
    return route_repo.add(route)


def get_route_by_id(route_repo: RouteRepository, route_id: int) -> Optional[Route]:
    """
    Get a route by ID.
    
    Args:
        route_repo: Repository for route persistence
        route_id: Route's unique identifier
        
    Returns:
        Route domain model if found, None otherwise
    """
    return route_repo.get_by_id(route_id)


def list_all_routes(route_repo: RouteRepository) -> list[Route]:
    """
    Get all routes.
    
    Args:
        route_repo: Repository for route persistence
        
    Returns:
        List of all Route domain models
    """
    return route_repo.list()


def list_routes_by_user(
    route_repo: RouteRepository,
    user_id: int
) -> list[UserSuggestedRoute]:
    """
    Get all routes suggested by a specific user.
    
    Args:
        route_repo: Repository for route persistence
        user_id: User's unique identifier
        
    Returns:
        List of UserSuggestedRoute domain models for the user
    """
    return route_repo.list_by_user(user_id)


def list_routes_by_subtype(
    route_repo: RouteRepository,
    subtype: str
) -> list[Route]:
    """
    Get all routes of a specific subtype.
    
    Args:
        route_repo: Repository for route persistence
        subtype: Route subtype (recommended, alternate, user_suggested)
        
    Returns:
        List of Route domain models matching the subtype
        
    Raises:
        ValueError: If invalid subtype provided
    """
    valid_subtypes = ["recommended", "alternate", "user_suggested"]
    if subtype not in valid_subtypes:
        raise ValueError(f"Invalid subtype. Must be one of: {', '.join(valid_subtypes)}")
    
    return route_repo.list_by_subtype(subtype)


def update_route(
    route_repo: RouteRepository,
    route_id: int,
    data: RouteUpdate
) -> Route:
    """
    Update an existing route.
    
    Args:
        route_repo: Repository for route persistence
        route_id: Route's unique identifier
        data: Route update data (partial updates supported)
        
    Returns:
        Updated Route domain model
        
    Raises:
        ValueError: If route not found
    """
    route = route_repo.get_by_id(route_id)
    if not route:
        raise ValueError("Route not found")
    
    # Update fields if provided
    if data.transport_mode is not None:
        route.transport_mode = data.transport_mode
    if data.route_line is not None:
        route.route_line = data.route_line
    if data.metrics_id is not None:
        route.metrics_id = data.metrics_id
    
    return route_repo.update(route)


def associate_metrics(
    route_repo: RouteRepository,
    route_id: int,
    metrics_id: int
) -> Route:
    """
    Associate metrics with a route.
    
    Args:
        route_repo: Repository for route persistence
        route_id: Route's unique identifier
        metrics_id: Metrics ID to associate
        
    Returns:
        Updated Route domain model
        
    Raises:
        ValueError: If route not found
    """
    route = route_repo.get_by_id(route_id)
    if not route:
        raise ValueError("Route not found")
    
    route.metrics_id = metrics_id
    return route_repo.update(route)


def delete_route(route_repo: RouteRepository, route_id: int) -> bool:
    """
    Delete a route.
    
    Args:
        route_repo: Repository for route persistence
        route_id: Route's unique identifier
        
    Returns:
        True if route deleted successfully, False if route not found
    """
    return route_repo.delete(route_id)

