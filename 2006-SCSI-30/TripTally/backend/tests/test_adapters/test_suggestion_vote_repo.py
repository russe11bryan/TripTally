"""
Integration tests for SqlSuggestionVoteRepo adapter.
Tests the SQLAlchemy implementation of SuggestionVoteRepository.
"""
import pytest
from datetime import datetime
from app.models.suggestion_vote import SuggestionVote
from app.adapters.sqlalchemy_suggestion_vote_repo import SqlSuggestionVoteRepo


class TestSqlSuggestionVoteRepo:
    """Tests for SqlSuggestionVoteRepo adapter"""
    
    def test_add_upvote(self, test_db_session):
        """Test adding an upvote"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        vote = SuggestionVote(
            id=0,
            route_id=100,
            user_id=42,
            vote_type="upvote",
            comment="Great alternative route!"
        )
        
        result = repo.add(vote)
        
        assert result.id > 0
        assert result.route_id == 100
        assert result.user_id == 42
        assert result.vote_type == "upvote"
        assert result.comment == "Great alternative route!"
    
    def test_add_downvote(self, test_db_session):
        """Test adding a downvote"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        vote = SuggestionVote(
            id=0,
            route_id=101,
            user_id=43,
            vote_type="downvote",
            comment="Route is too long"
        )
        
        result = repo.add(vote)
        
        assert result.id > 0
        assert result.vote_type == "downvote"
        assert result.comment == "Route is too long"
    
    def test_add_vote_without_comment(self, test_db_session):
        """Test adding a vote without comment"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        vote = SuggestionVote(
            id=0,
            route_id=102,
            user_id=44,
            vote_type="upvote"
        )
        
        result = repo.add(vote)
        
        assert result.id > 0
        assert result.comment == ""
    
    def test_add_vote_with_timestamp(self, test_db_session):
        """Test adding a vote with timestamp"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        now = datetime.now()
        vote = SuggestionVote(
            id=0,
            route_id=103,
            user_id=45,
            vote_type="upvote",
            created_at=now
        )
        
        result = repo.add(vote)
        
        assert result.id > 0
        assert result.created_at is not None
    
    def test_get_by_id(self, test_db_session):
        """Test retrieving vote by ID"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        # Add a vote
        vote = SuggestionVote(
            id=0,
            route_id=100,
            user_id=42,
            vote_type="upvote",
            comment="Excellent route"
        )
        added = repo.add(vote)
        
        # Retrieve it
        found = repo.get_by_id(added.id)
        
        assert found is not None
        assert found.id == added.id
        assert found.route_id == 100
        assert found.vote_type == "upvote"
    
    def test_get_by_id_not_found(self, test_db_session):
        """Test retrieving non-existent vote"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        result = repo.get_by_id(99999)
        
        assert result is None
    
    def test_list_votes(self, test_db_session):
        """Test listing all votes"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        # Add multiple votes
        vote1 = SuggestionVote(id=0, route_id=100, user_id=10, vote_type="upvote")
        vote2 = SuggestionVote(id=0, route_id=101, user_id=11, vote_type="downvote")
        
        repo.add(vote1)
        repo.add(vote2)
        
        # List all
        votes = repo.list()
        
        assert len(votes) >= 2
    
    def test_list_by_route(self, test_db_session):
        """Test listing votes for a specific route"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        # Add votes for different routes
        vote1 = SuggestionVote(id=0, route_id=200, user_id=10, vote_type="upvote")
        vote2 = SuggestionVote(id=0, route_id=200, user_id=11, vote_type="upvote")
        vote3 = SuggestionVote(id=0, route_id=200, user_id=12, vote_type="downvote")
        vote4 = SuggestionVote(id=0, route_id=300, user_id=13, vote_type="upvote")
        
        repo.add(vote1)
        repo.add(vote2)
        repo.add(vote3)
        repo.add(vote4)
        
        # Get votes for route 200
        route_votes = repo.list_by_route(200)
        
        assert len(route_votes) == 3
        assert all(v.route_id == 200 for v in route_votes)
    
    def test_list_by_user(self, test_db_session):
        """Test listing votes by a specific user"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        # Add votes from different users
        vote1 = SuggestionVote(id=0, route_id=100, user_id=50, vote_type="upvote")
        vote2 = SuggestionVote(id=0, route_id=101, user_id=50, vote_type="downvote")
        vote3 = SuggestionVote(id=0, route_id=102, user_id=60, vote_type="upvote")
        
        repo.add(vote1)
        repo.add(vote2)
        repo.add(vote3)
        
        # Get votes by user 50
        user_votes = repo.list_by_user(50)
        
        assert len(user_votes) == 2
        assert all(v.user_id == 50 for v in user_votes)
    
    def test_get_user_vote_for_route(self, test_db_session):
        """Test getting specific user's vote for a specific route"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        # Add votes
        vote1 = SuggestionVote(id=0, route_id=200, user_id=42, vote_type="upvote")
        vote2 = SuggestionVote(id=0, route_id=200, user_id=43, vote_type="downvote")
        vote3 = SuggestionVote(id=0, route_id=201, user_id=42, vote_type="downvote")
        
        repo.add(vote1)
        repo.add(vote2)
        repo.add(vote3)
        
        # Get user 42's vote for route 200
        user_vote = repo.get_user_vote_for_route(42, 200)
        
        assert user_vote is not None
        assert user_vote.user_id == 42
        assert user_vote.route_id == 200
        assert user_vote.vote_type == "upvote"
    
    def test_get_user_vote_for_route_not_found(self, test_db_session):
        """Test getting vote when user hasn't voted on route"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        result = repo.get_user_vote_for_route(99, 99)
        
        assert result is None
    
    def test_count_votes_for_route(self, test_db_session):
        """Test counting upvotes and downvotes for a route"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        # Add votes for a route
        vote1 = SuggestionVote(id=0, route_id=300, user_id=10, vote_type="upvote")
        vote2 = SuggestionVote(id=0, route_id=300, user_id=11, vote_type="upvote")
        vote3 = SuggestionVote(id=0, route_id=300, user_id=12, vote_type="upvote")
        vote4 = SuggestionVote(id=0, route_id=300, user_id=13, vote_type="downvote")
        vote5 = SuggestionVote(id=0, route_id=300, user_id=14, vote_type="downvote")
        
        repo.add(vote1)
        repo.add(vote2)
        repo.add(vote3)
        repo.add(vote4)
        repo.add(vote5)
        
        # Count votes
        counts = repo.count_votes_for_route(300)
        
        assert counts["upvotes"] == 3
        assert counts["downvotes"] == 2
    
    def test_count_votes_no_votes(self, test_db_session):
        """Test counting votes for route with no votes"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        counts = repo.count_votes_for_route(999)
        
        assert counts["upvotes"] == 0
        assert counts["downvotes"] == 0
    
    def test_update_vote(self, test_db_session):
        """Test updating a vote"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        # Add a vote
        vote = SuggestionVote(
            id=0,
            route_id=100,
            user_id=42,
            vote_type="upvote",
            comment="Good route"
        )
        added = repo.add(vote)
        
        # Update it (user changes their mind)
        added.vote_type = "downvote"
        added.comment = "Actually, route is too long"
        repo.update(added)
        
        # Verify update
        updated = repo.get_by_id(added.id)
        assert updated.vote_type == "downvote"
        assert updated.comment == "Actually, route is too long"
    
    def test_delete_vote(self, test_db_session):
        """Test deleting a vote"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        # Add a vote
        vote = SuggestionVote(
            id=0,
            route_id=100,
            user_id=42,
            vote_type="upvote"
        )
        added = repo.add(vote)
        
        # Delete it
        result = repo.delete(added.id)
        assert result is True
        
        # Verify deletion
        found = repo.get_by_id(added.id)
        assert found is None
    
    def test_delete_nonexistent_vote(self, test_db_session):
        """Test deleting non-existent vote"""
        repo = SqlSuggestionVoteRepo(test_db_session)
        
        result = repo.delete(99999)
        
        assert result is False
