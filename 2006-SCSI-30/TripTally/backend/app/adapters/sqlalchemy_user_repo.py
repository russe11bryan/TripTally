"""
SQLAlchemy adapter implementation for UserRepository.
"""
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from app.models.account import User
from app.adapters.tables import UserTable
from app.ports.user_repo import UserRepository


class SqlUserRepo(UserRepository):
    """SQLAlchemy implementation of UserRepository following best practices."""
    
    def __init__(self, db: Session):
        self.db = db

    def add(self, user: User) -> User:
        """Add a new user to the database."""
        row = UserTable(
            email=user.email,
            username=user.username,
            hashed_password=user.hashed_password,
            contact_number=user.contact_number,
            status=user.status,
            display_name=user.display_name,
            saved_locations=user.saved_locations or [],
            google_id=user.google_id
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        user.id = row.id
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        row = self.db.query(UserTable).filter(UserTable.id == user_id).first()
        if not row:
            return None
        return self._to_domain(row)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        row = self.db.query(UserTable).filter(UserTable.email == email).first()
        if not row:
            return None
        return self._to_domain(row)

    def get_by_username(self, username: str) -> Optional[User]:
        row = self.db.query(UserTable).filter(UserTable.username == username).first()
        if not row:
            return None
        return self._to_domain(row)

    def get_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID."""
        row = self.db.query(UserTable).filter(UserTable.google_id == google_id).first()
        if not row:
            return None
        return self._to_domain(row)

    def list(self) -> list[User]:
        """List all users."""
        rows = self.db.query(UserTable).all()
        return [self._to_domain(r) for r in rows]

    def update(self, user: User) -> User:
        """Update an existing user."""
        row = self.db.query(UserTable).filter(UserTable.id == user.id).first()
        if row:
            row.email = user.email
            row.username = user.username
            row.hashed_password = user.hashed_password
            row.contact_number = user.contact_number
            row.status = user.status
            row.display_name = user.display_name
            row.saved_locations = user.saved_locations or []
            row.google_id = user.google_id
            # Update location fields
            row.home_latitude = user.home_latitude
            row.home_longitude = user.home_longitude
            row.home_address = user.home_address
            row.work_latitude = user.work_latitude
            row.work_longitude = user.work_longitude
            row.work_address = user.work_address
            self.db.commit()
            self.db.refresh(row)
        return user

    def delete(self, user_id: int) -> bool:
        """Delete a user."""
        row = self.db.query(UserTable).filter(UserTable.id == user_id).first()
        if row:
            self.db.delete(row)
            self.db.commit()
            return True
        return False

    def add_saved_location(self, user_id: int, location_id: int) -> bool:
        """Add a location id to the user's saved_locations list.

        Returns True if the location was added, False if the user was not found
        or the location was already saved.
        """
        row = self.db.query(UserTable).filter(UserTable.id == user_id).first()
        if not row:
            return False
        saved = row.saved_locations or []
        # Ensure we operate on a list
        if not isinstance(saved, list):
            saved = list(saved)
        if location_id in saved:
            return False
        saved.append(location_id)
        row.saved_locations = saved
        self.db.commit()
        self.db.refresh(row)
        return True

    def remove_saved_location(self, user_id: int, location_id: int) -> bool:
        """Remove a location id from the user's saved_locations list.

        Returns True if removed, False if user not found or location not present.
        """
        row = self.db.query(UserTable).filter(UserTable.id == user_id).first()
        if not row:
            return False
        saved = row.saved_locations or []
        if not isinstance(saved, list):
            saved = list(saved)
        if location_id not in saved:
            return False
        saved.remove(location_id)
        row.saved_locations = saved
        self.db.commit()
        self.db.refresh(row)
        return True

    def get_saved_locations(self, user_id: int) -> list[int]:
        """Return saved location ids for a user, or empty list if none/found."""
        row = self.db.query(UserTable).filter(UserTable.id == user_id).first()
        if not row:
            return []
        saved = row.saved_locations or []
        # Ensure result is a list of ints
        if not isinstance(saved, list):
            try:
                return list(saved)
            except Exception:
                return []
        return saved

    def _to_domain(self, row: UserTable) -> User:
        """Convert database row to domain model."""
        return User(
            id=row.id,
            email=row.email,
            username=row.username,
            hashed_password=row.hashed_password,
            contact_number=row.contact_number,
            status=row.status,
            display_name=row.display_name,
            saved_locations=row.saved_locations or [],
            google_id=row.google_id,
            home_latitude=row.home_latitude,
            home_longitude=row.home_longitude,
            home_address=row.home_address,
            work_latitude=row.work_latitude,
            work_longitude=row.work_longitude,
            work_address=row.work_address
        )
