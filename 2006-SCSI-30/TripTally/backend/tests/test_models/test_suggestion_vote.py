"""
Unit tests for SuggestionVote domain model.
"""
import pytest
from datetime import datetime
from app.models.suggestion_vote import SuggestionVote


class TestSuggestionVote:
    """Tests for SuggestionVote model"""
    
    def test_create_upvote(self):
        """Test creating an upvote"""
        vote = SuggestionVote(
            id=1,
            route_id=100,
            user_id=42,
            vote_type="upvote",
            comment="Great alternative route!"
        )
        
        assert vote.id == 1
        assert vote.route_id == 100
        assert vote.user_id == 42
        assert vote.vote_type == "upvote"
        assert vote.comment == "Great alternative route!"
    
    def test_create_downvote(self):
        """Test creating a downvote"""
        vote = SuggestionVote(
            id=2,
            route_id=101,
            user_id=43,
            vote_type="downvote",
            comment="Route is too long"
        )
        
        assert vote.id == 2
        assert vote.vote_type == "downvote"
        assert vote.comment == "Route is too long"
    
    def test_vote_without_comment(self):
        """Test creating a vote without comment"""
        vote = SuggestionVote(
            id=3,
            route_id=102,
            user_id=44,
            vote_type="upvote"
        )
        
        assert vote.comment == ""
    
    def test_vote_with_timestamp(self):
        """Test SuggestionVote with timestamp"""
        now = datetime.now()
        vote = SuggestionVote(
            id=4,
            route_id=103,
            user_id=45,
            vote_type="upvote",
            created_at=now
        )
        
        assert vote.created_at == now
    
    def test_vote_defaults(self):
        """Test SuggestionVote default values"""
        vote = SuggestionVote(
            id=5,
            route_id=104,
            user_id=46,
            vote_type="downvote"
        )
        
        assert vote.comment == ""
        assert vote.created_at is None
    
    def test_multiple_votes_on_same_route(self):
        """Test multiple users voting on same route"""
        route_id = 200
        
        vote1 = SuggestionVote(
            id=1,
            route_id=route_id,
            user_id=10,
            vote_type="upvote"
        )
        
        vote2 = SuggestionVote(
            id=2,
            route_id=route_id,
            user_id=11,
            vote_type="upvote"
        )
        
        vote3 = SuggestionVote(
            id=3,
            route_id=route_id,
            user_id=12,
            vote_type="downvote"
        )
        
        assert vote1.route_id == vote2.route_id == vote3.route_id == route_id
        assert vote1.user_id != vote2.user_id != vote3.user_id
