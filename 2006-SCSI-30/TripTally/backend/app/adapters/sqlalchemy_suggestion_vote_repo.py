"""
SQLAlchemy adapter implementation for SuggestionVoteRepository.
"""
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.suggestion_vote import SuggestionVote
from app.adapters.tables import SuggestionVoteTable
from app.ports.suggestion_vote_repo import SuggestionVoteRepository


class SqlSuggestionVoteRepo(SuggestionVoteRepository):
    def __init__(self, db: Session):
        self.db = db

    def add(self, vote: SuggestionVote) -> SuggestionVote:
        """Add a new vote for a user-suggested route."""
        row = SuggestionVoteTable(
            route_id=vote.route_id,
            user_id=vote.user_id,
            vote_type=vote.vote_type,
            comment=vote.comment,
            created_at=vote.created_at.isoformat() if vote.created_at else None,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        vote.id = row.id
        return vote

    def get_by_id(self, vote_id: int) -> Optional[SuggestionVote]:
        """Get vote by ID."""
        row = self.db.query(SuggestionVoteTable).filter(
            SuggestionVoteTable.id == vote_id
        ).first()
        if not row:
            return None
        return self._to_domain(row)

    def list(self) -> list[SuggestionVote]:
        """List all votes."""
        rows = self.db.query(SuggestionVoteTable).all()
        return [self._to_domain(r) for r in rows]

    def list_by_route(self, route_id: int) -> list[SuggestionVote]:
        """List all votes for a specific route."""
        rows = self.db.query(SuggestionVoteTable).filter(
            SuggestionVoteTable.route_id == route_id
        ).all()
        return [self._to_domain(r) for r in rows]

    def list_by_user(self, user_id: int) -> list[SuggestionVote]:
        """List all votes by a specific user."""
        rows = self.db.query(SuggestionVoteTable).filter(
            SuggestionVoteTable.user_id == user_id
        ).all()
        return [self._to_domain(r) for r in rows]

    def get_user_vote_for_route(
        self, user_id: int, route_id: int
    ) -> Optional[SuggestionVote]:
        """Get a specific user's vote for a specific route."""
        row = self.db.query(SuggestionVoteTable).filter(
            SuggestionVoteTable.user_id == user_id,
            SuggestionVoteTable.route_id == route_id
        ).first()
        if not row:
            return None
        return self._to_domain(row)

    def count_votes_for_route(self, route_id: int) -> dict[str, int]:
        """Count upvotes and downvotes for a route."""
        upvotes = self.db.query(func.count(SuggestionVoteTable.id)).filter(
            SuggestionVoteTable.route_id == route_id,
            SuggestionVoteTable.vote_type == "upvote"
        ).scalar() or 0
        
        downvotes = self.db.query(func.count(SuggestionVoteTable.id)).filter(
            SuggestionVoteTable.route_id == route_id,
            SuggestionVoteTable.vote_type == "downvote"
        ).scalar() or 0
        
        return {"upvotes": upvotes, "downvotes": downvotes}

    def update(self, vote: SuggestionVote) -> SuggestionVote:
        """Update an existing vote."""
        row = self.db.query(SuggestionVoteTable).filter(
            SuggestionVoteTable.id == vote.id
        ).first()
        if row:
            row.route_id = vote.route_id
            row.user_id = vote.user_id
            row.vote_type = vote.vote_type
            row.comment = vote.comment
            row.created_at = vote.created_at.isoformat() if vote.created_at else None
            self.db.commit()
            self.db.refresh(row)
        return vote

    def delete(self, vote_id: int) -> bool:
        """Delete a vote."""
        row = self.db.query(SuggestionVoteTable).filter(
            SuggestionVoteTable.id == vote_id
        ).first()
        if row:
            self.db.delete(row)
            self.db.commit()
            return True
        return False

    def _to_domain(self, row: SuggestionVoteTable) -> SuggestionVote:
        """Convert database row to domain model."""
        from datetime import datetime
        
        return SuggestionVote(
            id=row.id,
            route_id=row.route_id,
            user_id=row.user_id,
            vote_type=row.vote_type,
            comment=row.comment,
            created_at=datetime.fromisoformat(row.created_at) if row.created_at else None,
        )
