"""
Domain model for SuggestionVote (for voting on user-suggested routes)
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class SuggestionVote:
    id: int
    route_id: int  # UserSuggestedRoute ID
    user_id: int  # User who voted
    vote_type: str  # "upvote" or "downvote"
    comment: str = ""
    created_at: Optional[datetime] = None
