from __future__ import annotations

"""
SQLAlchemy adapter implementation for AdminRepository.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.account import Admin
from app.adapters.tables import AdminTable
from app.ports.admin_repo import AdminRepository


class SqlAdminRepo(AdminRepository):
    """SQLAlchemy implementation of AdminRepository following best practices."""
    
    def __init__(self, db: Session):
        self.db = db

    def add(self, admin: Admin) -> Admin:
        """Add a new admin to the database."""
        row = AdminTable(
            email=admin.email,
            username=admin.username or admin.email,
            hashed_password=admin.hashed_password,
            contact_number=admin.contact_number,
            status=admin.status
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        admin.id = row.id
        return admin

    def get_by_id(self, admin_id: int) -> Optional[Admin]:
        """Get admin by ID."""
        row = self.db.query(AdminTable).filter(AdminTable.id == admin_id).first()
        if not row:
            return None
        return self._to_domain(row)

    def get_by_email(self, email: str) -> Optional[Admin]:
        """Get admin by email."""
        row = self.db.query(AdminTable).filter(AdminTable.email == email).first()
        if not row:
            return None
        return self._to_domain(row)

    def list(self) -> list[Admin]:
        """List all admins."""
        rows = self.db.query(AdminTable).all()
        return [self._to_domain(r) for r in rows]

    def update(self, admin: Admin) -> Admin:
        """Update an existing admin."""
        row = self.db.query(AdminTable).filter(AdminTable.id == admin.id).first()
        if row:
            row.email = admin.email
            row.username = admin.username or admin.email
            row.hashed_password = admin.hashed_password
            row.contact_number = admin.contact_number
            row.status = admin.status
            self.db.commit()
            self.db.refresh(row)
        return admin

    def delete(self, admin_id: int) -> bool:
        """Delete an admin."""
        row = self.db.query(AdminTable).filter(AdminTable.id == admin_id).first()
        if row:
            self.db.delete(row)
            self.db.commit()
            return True
        return False

    def _to_domain(self, row: AdminTable) -> Admin:
        """Convert database row to domain model."""
        return Admin(
            id=row.id,
            email=row.email,
            username=row.username,
            hashed_password=row.hashed_password,
            contact_number=row.contact_number,
            status=row.status
        )
