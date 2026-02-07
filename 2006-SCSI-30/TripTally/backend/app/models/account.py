from __future__ import annotations

## Account (abstract), User, Admin (Inheritance)

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Account:
    id: Optional[int]
    email: str
    hashed_password: str
    username: str = ""
    contact_number: str = ""
    type: str = "account"  # default discriminator for domain logic
    status: str = "active"  # e.g., active, suspended, deactivated

    @property
    def password(self) -> str:
        """Backward compatible alias for hashed password."""
        return self.hashed_password

    @password.setter
    def password(self, value: str) -> None:
        self.hashed_password = value


@dataclass
class User(Account):
    display_name: str = ""
    saved_locations: list[int] = field(default_factory=list)  # List of LocationNode IDs
    home_latitude: Optional[float] = None
    home_longitude: Optional[float] = None
    home_address: Optional[str] = None
    work_latitude: Optional[float] = None
    work_longitude: Optional[float] = None
    work_address: Optional[str] = None
    google_id: Optional[str] = None  # Google OAuth user ID
    type: str = "user"
    
    # Note: Business logic methods (saveLocation, unsaveLocation, suggestRoute, etc.)
    # should be implemented in the Service layer, not in domain models.
    # Domain models should be pure data structures.


@dataclass
class Admin(Account):
    type: str = "admin"
    
    # Note: Business logic methods (verifySuggestedRoute, resolveIncident, etc.)
    # should be implemented in the Service layer, not in domain models.
    # Domain models should be pure data structures.
