"""
SQLAlchemy adapter implementation for RouteRepository.
"""
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from app.models.route import Route, UserSuggestedRoute
from app.adapters.tables import RouteTable, UserSuggestedRouteTable
from app.ports.route_repo import RouteRepository


class SqlRouteRepo(RouteRepository):
    """SQLAlchemy implementation of RouteRepository following best practices."""
    
    def __init__(self, db: Session):
        self.db = db

    def add(self, route: Route) -> Route:
        """Add a new route to the database."""
        if isinstance(route, UserSuggestedRoute):
            row = UserSuggestedRouteTable(
                start_location_id=route.start_location_id,
                end_location_id=route.end_location_id,
                subtype=route.subtype,
                transport_mode=route.transport_mode,
                route_line=route.route_line,
                metrics_id=route.metrics_id,
                user_id=route.user_id
            )
        else:
            row = RouteTable(
                start_location_id=route.start_location_id,
                end_location_id=route.end_location_id,
                subtype=route.subtype,
                transport_mode=route.transport_mode,
                route_line=route.route_line,
                metrics_id=route.metrics_id
            )
        
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        route.id = row.id
        return route

    def get_by_id(self, route_id: int) -> Optional[Route]:
        """Get route by ID."""
        row = self.db.query(RouteTable).filter(RouteTable.id == route_id).first()
        if not row:
            return None
        return self._to_domain(row)

    def list(self) -> list[Route]:
        """List all routes."""
        rows = self.db.query(RouteTable).all()
        return [self._to_domain(r) for r in rows]

    def list_by_user(self, user_id: int) -> list[UserSuggestedRoute]:
        """List all routes suggested by a specific user."""
        rows = self.db.query(UserSuggestedRouteTable).filter(
            UserSuggestedRouteTable.user_id == user_id
        ).all()
        return [self._to_domain(r) for r in rows]

    def update(self, route: Route) -> Route:
        """Update an existing route."""
        row = self.db.query(RouteTable).filter(RouteTable.id == route.id).first()
        if row:
            row.start_location_id = route.start_location_id
            row.end_location_id = route.end_location_id
            row.subtype = route.subtype
            row.transport_mode = route.transport_mode
            row.route_line = route.route_line
            row.metrics_id = route.metrics_id
            
            if isinstance(route, UserSuggestedRoute) and isinstance(row, UserSuggestedRouteTable):
                row.user_id = route.user_id
            
            self.db.commit()
            self.db.refresh(row)
        return route

    def delete(self, route_id: int) -> bool:
        """Delete a route."""
        row = self.db.query(RouteTable).filter(RouteTable.id == route_id).first()
        if row:
            self.db.delete(row)
            self.db.commit()
            return True
        return False

    def _to_domain(self, row: RouteTable) -> Route:
        """Convert database row to domain model based on type."""
        if row.type == "user_suggested":
            return UserSuggestedRoute(
                id=row.id,
                start_location_id=row.start_location_id,
                end_location_id=row.end_location_id,
                subtype=row.subtype,
                transport_mode=row.transport_mode,
                route_line=row.route_line or [],
                metrics_id=row.metrics_id,
                user_id=getattr(row, 'user_id', None)
            )
        else:
            return Route(
                id=row.id,
                start_location_id=row.start_location_id,
                end_location_id=row.end_location_id,
                subtype=row.subtype,
                transport_mode=row.transport_mode,
                route_line=row.route_line or [],
                metrics_id=row.metrics_id
            )
