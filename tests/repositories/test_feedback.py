"""
FILE: test_feedback.py
STATUS: Active
RESPONSIBILITY: Tests for feedback models, repository, and service
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

import tempfile
from pathlib import Path

import pytest

from src.models.feedback import (
    ChatInteractionCreate,
    FeedbackCreate,
    FeedbackRating,
)
from src.repositories.feedback import FeedbackRepository
from src.services.feedback import FeedbackService


@pytest.fixture
def temp_db():
    """Create a temporary database path for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        yield db_path


@pytest.fixture
def repository(temp_db):
    """Create a FeedbackRepository with temporary database."""
    repo = FeedbackRepository(db_path=temp_db)
    yield repo
    repo.close()  # Properly close to release file lock on Windows


@pytest.fixture
def service(repository):
    """Create a FeedbackService with test repository."""
    return FeedbackService(repository=repository)


class TestFeedbackModels:
    """Tests for feedback Pydantic models."""

    def test_feedback_rating_enum(self):
        """Test FeedbackRating enum values."""
        assert FeedbackRating.POSITIVE.value == "positive"
        assert FeedbackRating.NEGATIVE.value == "negative"

    def test_chat_interaction_create(self):
        """Test ChatInteractionCreate model."""
        interaction = ChatInteractionCreate(
            query="Test query",
            response="Test response",
            sources=["source1", "source2"],
            processing_time_ms=100,
        )
        assert interaction.query == "Test query"
        assert interaction.response == "Test response"
        assert len(interaction.sources) == 2
        assert interaction.processing_time_ms == 100

    def test_feedback_create(self):
        """Test FeedbackCreate model."""
        feedback = FeedbackCreate(
            interaction_id="test-id",
            rating=FeedbackRating.POSITIVE,
            comment=None,
        )
        assert feedback.interaction_id == "test-id"
        assert feedback.rating == FeedbackRating.POSITIVE
        assert feedback.comment is None

    def test_feedback_create_with_comment(self):
        """Test FeedbackCreate with comment."""
        feedback = FeedbackCreate(
            interaction_id="test-id",
            rating=FeedbackRating.NEGATIVE,
            comment="Response was inaccurate",
        )
        assert feedback.rating == FeedbackRating.NEGATIVE
        assert feedback.comment == "Response was inaccurate"


class TestFeedbackRepository:
    """Tests for FeedbackRepository."""

    def test_repository_init(self, repository):
        """Test repository initialization creates database."""
        assert repository.db_path.exists()

    def test_save_interaction(self, repository):
        """Test saving a chat interaction."""
        interaction = ChatInteractionCreate(
            query="Who won the NBA championship?",
            response="The Lakers won in 2020.",
            sources=["nba_history.pdf"],
            processing_time_ms=150,
        )
        saved = repository.save_interaction(interaction)

        assert saved.id is not None
        assert saved.query == interaction.query
        assert saved.response == interaction.response
        assert saved.sources == interaction.sources
        assert saved.processing_time_ms == 150
        assert saved.created_at is not None

    def test_get_interaction(self, repository):
        """Test retrieving an interaction by ID."""
        interaction = ChatInteractionCreate(
            query="Test query",
            response="Test response",
        )
        saved = repository.save_interaction(interaction)

        retrieved = repository.get_interaction(saved.id)
        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.query == "Test query"

    def test_get_interaction_not_found(self, repository):
        """Test retrieving non-existent interaction."""
        result = repository.get_interaction("non-existent-id")
        assert result is None

    def test_save_feedback(self, repository):
        """Test saving feedback for an interaction."""
        # First save an interaction
        interaction = ChatInteractionCreate(
            query="Test query",
            response="Test response",
        )
        saved_interaction = repository.save_interaction(interaction)

        # Now save feedback
        feedback = FeedbackCreate(
            interaction_id=saved_interaction.id,
            rating=FeedbackRating.POSITIVE,
        )
        saved_feedback = repository.save_feedback(feedback)

        assert saved_feedback.id is not None
        assert saved_feedback.interaction_id == saved_interaction.id
        assert saved_feedback.rating == FeedbackRating.POSITIVE
        assert saved_feedback.created_at is not None

    def test_save_feedback_with_comment(self, repository):
        """Test saving negative feedback with comment."""
        interaction = ChatInteractionCreate(
            query="Test query",
            response="Test response",
        )
        saved_interaction = repository.save_interaction(interaction)

        feedback = FeedbackCreate(
            interaction_id=saved_interaction.id,
            rating=FeedbackRating.NEGATIVE,
            comment="The answer was wrong",
        )
        saved_feedback = repository.save_feedback(feedback)

        assert saved_feedback.rating == FeedbackRating.NEGATIVE
        assert saved_feedback.comment == "The answer was wrong"

    def test_save_feedback_interaction_not_found(self, repository):
        """Test saving feedback for non-existent interaction."""
        feedback = FeedbackCreate(
            interaction_id="non-existent-id",
            rating=FeedbackRating.POSITIVE,
        )
        with pytest.raises(ValueError, match="not found"):
            repository.save_feedback(feedback)

    def test_save_feedback_duplicate(self, repository):
        """Test duplicate feedback is rejected."""
        interaction = ChatInteractionCreate(
            query="Test query",
            response="Test response",
        )
        saved_interaction = repository.save_interaction(interaction)

        feedback = FeedbackCreate(
            interaction_id=saved_interaction.id,
            rating=FeedbackRating.POSITIVE,
        )
        repository.save_feedback(feedback)

        # Try to save again
        with pytest.raises(ValueError, match="already exists"):
            repository.save_feedback(feedback)

    def test_get_recent_interactions(self, repository):
        """Test retrieving recent interactions."""
        # Save multiple interactions
        for i in range(5):
            interaction = ChatInteractionCreate(
                query=f"Query {i}",
                response=f"Response {i}",
            )
            repository.save_interaction(interaction)

        recent = repository.get_recent_interactions(limit=3)
        assert len(recent) == 3

    def test_get_stats(self, repository):
        """Test getting feedback statistics."""
        # Save interactions and feedback
        for i in range(3):
            interaction = ChatInteractionCreate(
                query=f"Query {i}",
                response=f"Response {i}",
            )
            saved = repository.save_interaction(interaction)

            if i < 2:  # Add feedback to first 2
                rating = FeedbackRating.POSITIVE if i == 0 else FeedbackRating.NEGATIVE
                feedback = FeedbackCreate(
                    interaction_id=saved.id,
                    rating=rating,
                )
                repository.save_feedback(feedback)

        stats = repository.get_stats()
        assert stats.total_interactions == 3
        assert stats.total_feedback == 2
        assert stats.positive_count == 1
        assert stats.negative_count == 1


class TestFeedbackService:
    """Tests for FeedbackService."""

    def test_log_interaction(self, service):
        """Test logging a chat interaction."""
        result = service.log_interaction(
            query="Who is the GOAT?",
            response="Many consider Michael Jordan the GOAT.",
            sources=["nba_legends.pdf"],
            processing_time_ms=200,
        )

        assert result.id is not None
        assert result.query == "Who is the GOAT?"
        assert result.response == "Many consider Michael Jordan the GOAT."

    def test_submit_feedback(self, service):
        """Test submitting feedback."""
        interaction = service.log_interaction(
            query="Test",
            response="Test response",
        )

        feedback = service.submit_feedback(
            interaction_id=interaction.id,
            rating=FeedbackRating.POSITIVE,
        )

        assert feedback.interaction_id == interaction.id
        assert feedback.rating == FeedbackRating.POSITIVE

    def test_submit_negative_feedback_with_comment(self, service):
        """Test submitting negative feedback with comment."""
        interaction = service.log_interaction(
            query="Test",
            response="Test response",
        )

        feedback = service.submit_feedback(
            interaction_id=interaction.id,
            rating=FeedbackRating.NEGATIVE,
            comment="Response was not helpful",
        )

        assert feedback.rating == FeedbackRating.NEGATIVE
        assert feedback.comment == "Response was not helpful"

    def test_get_stats(self, service):
        """Test getting statistics."""
        stats = service.get_stats()
        assert stats.total_interactions >= 0
        assert stats.total_feedback >= 0

    def test_get_negative_feedback_with_comments(self, service):
        """Test retrieving negative feedback with comments."""
        # Create interaction with negative feedback
        interaction = service.log_interaction(
            query="Bad query",
            response="Bad response",
        )
        service.submit_feedback(
            interaction_id=interaction.id,
            rating=FeedbackRating.NEGATIVE,
            comment="This was wrong",
        )

        results = service.get_negative_feedback_with_comments()
        assert len(results) >= 1
        assert any(r.feedback.comment == "This was wrong" for r in results)
