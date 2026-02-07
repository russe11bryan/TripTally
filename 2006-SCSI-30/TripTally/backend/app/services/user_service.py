from __future__ import annotations

"""
Service layer for User business logic.
"""
from app.models.account import User
from app.ports.user_repo import UserRepository


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def create_user(self, email: str, username: str, hashed_password: str, display_name: str) -> User:
        """Create a new user."""
        user = User(
            id=None,
            email=email,
            username=username,
            hashed_password=hashed_password,
            display_name=display_name
        )
        return self.repo.add(user)

    def get_user(self, user_id: int) -> User | None:
        """Get a user by ID."""
        return self.repo.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        return self.repo.get_by_email(email)

    def get_user_by_username(self, username: str) -> User | None:
        return self.repo.get_by_username(username)

    def get_all_users(self) -> list[User]:
        """Get all users."""
        return self.repo.list()

    def update_user(self, user_id: int, email: str, username: str, display_name: str) -> User | None:
        """Update a user."""
        user = self.repo.get_by_id(user_id)
        if not user:
            return None
        user.email = email
        user.username = username
        user.display_name = display_name
        return self.repo.update(user)

    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        return self.repo.delete(user_id)
