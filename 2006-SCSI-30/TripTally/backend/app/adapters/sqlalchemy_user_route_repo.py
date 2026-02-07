"""
SQLAlchemy repository for UserRoute domain model.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user_route import UserRoute, RoutePoint, UserRouteLike
from app.adapters.tables import UserRouteTable, UserRouteLikeTable


class SQLAlchemyUserRouteRepository:
    """Repository for managing user-created routes."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user_route: UserRoute) -> UserRoute:
        """Create a new user route."""
        # Convert RoutePoint objects to dicts for JSON storage
        points_data = [
            {"latitude": p.latitude, "longitude": p.longitude, "order": p.order}
            for p in (user_route.route_points or [])
        ]
        
        db_route = UserRouteTable(
            user_id=user_route.user_id,
            title=user_route.title,
            description=user_route.description,
            route_points=points_data,
            transport_mode=user_route.transport_mode,
            distance=user_route.distance,
            duration=user_route.duration,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_public=user_route.is_public,
            likes=0,
            created_by=user_route.created_by
        )
        
        self.db.add(db_route)
        self.db.commit()
        self.db.refresh(db_route)
        
        return self._to_domain(db_route)
    
    def get_by_id(self, route_id: int) -> Optional[UserRoute]:
        """Get a route by ID."""
        db_route = self.db.query(UserRouteTable).filter(UserRouteTable.id == route_id).first()
        return self._to_domain(db_route) if db_route else None
    
    def get_all_public(self, user_id: Optional[int] = None) -> List[UserRoute]:
        """Get all public routes, optionally including like status for a user."""
        query = self.db.query(UserRouteTable).filter(UserRouteTable.is_public == True)
        db_routes = query.order_by(UserRouteTable.created_at.desc()).all()
        
        routes = [self._to_domain(r) for r in db_routes]
        
        # Add user like status if user_id provided
        if user_id:
            for route in routes:
                is_liked = self.db.query(UserRouteLikeTable).filter(
                    UserRouteLikeTable.route_id == route.id,
                    UserRouteLikeTable.user_id == user_id
                ).first() is not None
                route.is_liked_by_user = is_liked
        
        return routes
    
    def get_by_user(self, user_id: int) -> List[UserRoute]:
        """Get all routes created by a specific user."""
        db_routes = self.db.query(UserRouteTable).filter(
            UserRouteTable.user_id == user_id
        ).order_by(UserRouteTable.created_at.desc()).all()
        
        return [self._to_domain(r) for r in db_routes]
    
    def update(self, route_id: int, user_route: UserRoute) -> Optional[UserRoute]:
        """Update an existing route."""
        db_route = self.db.query(UserRouteTable).filter(UserRouteTable.id == route_id).first()
        if not db_route:
            return None
        
        # Convert RoutePoint objects to dicts
        points_data = [
            {"latitude": p.latitude, "longitude": p.longitude, "order": p.order}
            for p in (user_route.route_points or [])
        ]
        
        db_route.title = user_route.title
        db_route.description = user_route.description
        db_route.route_points = points_data
        db_route.transport_mode = user_route.transport_mode
        db_route.distance = user_route.distance
        db_route.duration = user_route.duration
        db_route.is_public = user_route.is_public
        db_route.updated_at = datetime.now().isoformat()
        
        self.db.commit()
        self.db.refresh(db_route)
        
        return self._to_domain(db_route)
    
    def delete(self, route_id: int) -> bool:
        """Delete a route."""
        db_route = self.db.query(UserRouteTable).filter(UserRouteTable.id == route_id).first()
        if not db_route:
            return False
        
        self.db.delete(db_route)
        self.db.commit()
        return True
    
    def add_like(self, route_id: int, user_id: int) -> bool:
        """Add a like to a route."""
        # Check if already liked
        existing = self.db.query(UserRouteLikeTable).filter(
            UserRouteLikeTable.route_id == route_id,
            UserRouteLikeTable.user_id == user_id
        ).first()
        
        if existing:
            return False  # Already liked
        
        # Add like
        like = UserRouteLikeTable(
            route_id=route_id,
            user_id=user_id,
            created_at=datetime.now().isoformat()
        )
        self.db.add(like)
        
        # Increment likes count
        db_route = self.db.query(UserRouteTable).filter(UserRouteTable.id == route_id).first()
        if db_route:
            db_route.likes += 1
        
        self.db.commit()
        return True
    
    def remove_like(self, route_id: int, user_id: int) -> bool:
        """Remove a like from a route."""
        like = self.db.query(UserRouteLikeTable).filter(
            UserRouteLikeTable.route_id == route_id,
            UserRouteLikeTable.user_id == user_id
        ).first()
        
        if not like:
            return False  # Not liked
        
        self.db.delete(like)
        
        # Decrement likes count
        db_route = self.db.query(UserRouteTable).filter(UserRouteTable.id == route_id).first()
        if db_route and db_route.likes > 0:
            db_route.likes -= 1
        
        self.db.commit()
        return True
    
    def _to_domain(self, db_route: UserRouteTable) -> UserRoute:
        """Convert database model to domain model."""
        # Convert JSON points back to RoutePoint objects
        route_points = []
        if db_route.route_points:
            route_points = [
                RoutePoint(
                    latitude=p["latitude"],
                    longitude=p["longitude"],
                    order=p["order"]
                )
                for p in db_route.route_points
            ]
        
        return UserRoute(
            id=db_route.id,
            user_id=db_route.user_id,
            title=db_route.title,
            description=db_route.description,
            route_points=route_points,
            transport_mode=db_route.transport_mode,
            distance=db_route.distance,
            duration=db_route.duration,
            created_at=datetime.fromisoformat(db_route.created_at) if db_route.created_at else None,
            updated_at=datetime.fromisoformat(db_route.updated_at) if db_route.updated_at else None,
            is_public=db_route.is_public,
            likes=db_route.likes,
            created_by=db_route.created_by
        )
