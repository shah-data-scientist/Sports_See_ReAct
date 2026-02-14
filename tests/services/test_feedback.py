"""
FILE: test_feedback.py
STATUS: Active
RESPONSIBILITY: Tests for FeedbackService business logic
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.models.feedback import (
    ChatInteractionCreate,
    ChatInteractionResponse,
    FeedbackCreate,
    FeedbackRating,
    FeedbackResponse,
    FeedbackStats,
)
from src.services.feedback import FeedbackService


@pytest.fixture
def mock_repository():
    """Create a mock FeedbackRepository."""
    return MagicMock()


@pytest.fixture
def service(mock_repository):
    """Create FeedbackService with mocked repository."""
    return FeedbackService(repository=mock_repository)


@pytest.fixture
def sample_interaction():
    """Sample ChatInteractionResponse for testing."""
    return ChatInteractionResponse(
        id="int-123",
        query="What is LeBron's average?",
        response="LeBron averages 27.2 points per game.",
        sources=["nba_stats.xlsx"],
        processing_time_ms=1234,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_feedback():
    """Sample FeedbackResponse for testing."""
    return FeedbackResponse(
        id=1,
        interaction_id="int-123",
        rating=FeedbackRating.POSITIVE,
        comment="Great answer!",
        created_at=datetime.utcnow(),
    )


class TestFeedbackServiceInit:
    """Tests for FeedbackService initialization."""

    def test_init_with_repository(self, mock_repository):
        """Test initialization with provided repository."""
        service = FeedbackService(repository=mock_repository)
        assert service.repository is mock_repository

    def test_init_without_repository(self):
        """Test initialization creates default repository."""
        service = FeedbackService()
        assert service.repository is not None


class TestLogInteraction:
    """Tests for log_interaction method."""

    def test_log_interaction_full_params(self, service, mock_repository, sample_interaction):
        """Test logging interaction with all parameters."""
        mock_repository.save_interaction.return_value = sample_interaction

        result = service.log_interaction(
            query="What is LeBron's average?",
            response="LeBron averages 27.2 points per game.",
            sources=["nba_stats.xlsx"],
            processing_time_ms=1234,
        )

        assert result.id == "int-123"
        assert result.query == "What is LeBron's average?"
        assert result.sources == ["nba_stats.xlsx"]

        # Verify repository was called with ChatInteractionCreate
        mock_repository.save_interaction.assert_called_once()
        call_args = mock_repository.save_interaction.call_args[0][0]
        assert isinstance(call_args, ChatInteractionCreate)
        assert call_args.query == "What is LeBron's average?"
        assert call_args.response == "LeBron averages 27.2 points per game."
        assert call_args.sources == ["nba_stats.xlsx"]
        assert call_args.processing_time_ms == 1234

    def test_log_interaction_minimal_params(self, service, mock_repository):
        """Test logging interaction with only required parameters."""
        minimal_interaction = ChatInteractionResponse(
            id="int-456",
            query="Test query",
            response="Test response",
            sources=[],
            processing_time_ms=None,
            created_at=datetime.utcnow(),
        )
        mock_repository.save_interaction.return_value = minimal_interaction

        result = service.log_interaction(
            query="Test query",
            response="Test response",
        )

        assert result.id == "int-456"
        assert result.sources == []
        assert result.processing_time_ms is None

        call_args = mock_repository.save_interaction.call_args[0][0]
        assert call_args.sources == []
        assert call_args.processing_time_ms is None


class TestSubmitFeedback:
    """Tests for submit_feedback method."""

    def test_submit_positive_feedback(self, service, mock_repository, sample_feedback):
        """Test submitting positive feedback."""
        mock_repository.save_feedback.return_value = sample_feedback

        result = service.submit_feedback(
            interaction_id="int-123",
            rating=FeedbackRating.POSITIVE,
            comment="Great answer!",
        )

        assert result.id == 1
        assert result.interaction_id == "int-123"
        assert result.rating == FeedbackRating.POSITIVE
        assert result.comment == "Great answer!"

        mock_repository.save_feedback.assert_called_once()
        call_args = mock_repository.save_feedback.call_args[0][0]
        assert isinstance(call_args, FeedbackCreate)
        assert call_args.interaction_id == "int-123"
        assert call_args.rating == FeedbackRating.POSITIVE
        assert call_args.comment == "Great answer!"

    def test_submit_negative_feedback_with_comment(self, service, mock_repository):
        """Test submitting negative feedback with comment."""
        negative_feedback = FeedbackResponse(
            id=2,
            interaction_id="int-456",
            rating=FeedbackRating.NEGATIVE,
            comment="Incorrect stats",
            created_at=datetime.utcnow(),
        )
        mock_repository.save_feedback.return_value = negative_feedback

        result = service.submit_feedback(
            interaction_id="int-456",
            rating=FeedbackRating.NEGATIVE,
            comment="Incorrect stats",
        )

        assert result.rating == FeedbackRating.NEGATIVE
        assert result.comment == "Incorrect stats"

    def test_submit_feedback_without_comment(self, service, mock_repository):
        """Test submitting feedback without optional comment."""
        feedback_no_comment = FeedbackResponse(
            id=3,
            interaction_id="int-789",
            rating=FeedbackRating.POSITIVE,
            comment=None,
            created_at=datetime.utcnow(),
        )
        mock_repository.save_feedback.return_value = feedback_no_comment

        result = service.submit_feedback(
            interaction_id="int-789",
            rating=FeedbackRating.POSITIVE,
            comment=None,
        )

        assert result.comment is None

        call_args = mock_repository.save_feedback.call_args[0][0]
        assert call_args.comment is None

    def test_submit_feedback_interaction_not_found(self, service, mock_repository):
        """Test submitting feedback for non-existent interaction raises ValueError."""
        mock_repository.save_feedback.side_effect = ValueError("Interaction not-found not found")

        with pytest.raises(ValueError) as exc_info:
            service.submit_feedback(
                interaction_id="not-found",
                rating=FeedbackRating.POSITIVE,
            )
        assert "not found" in str(exc_info.value)

    def test_submit_feedback_duplicate_raises_error(self, service, mock_repository):
        """Test submitting duplicate feedback raises ValueError."""
        mock_repository.save_feedback.side_effect = ValueError(
            "Feedback already exists for interaction int-123"
        )

        with pytest.raises(ValueError) as exc_info:
            service.submit_feedback(
                interaction_id="int-123",
                rating=FeedbackRating.POSITIVE,
            )
        assert "already exists" in str(exc_info.value)


class TestUpdateFeedback:
    """Tests for update_feedback method."""

    def test_update_feedback_success(self, service, mock_repository):
        """Test updating feedback successfully."""
        updated_feedback = FeedbackResponse(
            id=1,
            interaction_id="int-123",
            rating=FeedbackRating.NEGATIVE,
            comment="Changed my mind",
            created_at=datetime.utcnow(),
        )
        mock_repository.update_feedback.return_value = updated_feedback

        result = service.update_feedback(
            interaction_id="int-123",
            rating=FeedbackRating.NEGATIVE,
            comment="Changed my mind",
        )

        assert result is not None
        assert result.rating == FeedbackRating.NEGATIVE
        assert result.comment == "Changed my mind"

        mock_repository.update_feedback.assert_called_once_with(
            "int-123", FeedbackRating.NEGATIVE, "Changed my mind"
        )

    def test_update_feedback_not_found(self, service, mock_repository):
        """Test updating non-existent feedback returns None."""
        mock_repository.update_feedback.return_value = None

        result = service.update_feedback(
            interaction_id="not-found",
            rating=FeedbackRating.POSITIVE,
        )

        assert result is None


class TestGetInteraction:
    """Tests for get_interaction method."""

    def test_get_interaction_success(self, service, mock_repository, sample_interaction):
        """Test getting an existing interaction."""
        mock_repository.get_interaction.return_value = sample_interaction

        result = service.get_interaction("int-123")

        assert result is not None
        assert result.id == "int-123"
        assert result.query == "What is LeBron's average?"

        mock_repository.get_interaction.assert_called_once_with("int-123")

    def test_get_interaction_not_found(self, service, mock_repository):
        """Test getting non-existent interaction returns None."""
        mock_repository.get_interaction.return_value = None

        result = service.get_interaction("not-found")

        assert result is None


class TestGetRecentInteractions:
    """Tests for get_recent_interactions method."""

    def test_get_recent_interactions_default(self, service, mock_repository, sample_interaction):
        """Test getting recent interactions with default pagination."""
        mock_repository.get_recent_interactions.return_value = [sample_interaction]

        results = service.get_recent_interactions()

        assert len(results) == 1
        assert results[0].id == "int-123"

        mock_repository.get_recent_interactions.assert_called_once_with(50, 0)

    def test_get_recent_interactions_custom_pagination(self, service, mock_repository):
        """Test getting recent interactions with custom limit and offset."""
        mock_repository.get_recent_interactions.return_value = []

        results = service.get_recent_interactions(limit=10, offset=20)

        assert results == []
        mock_repository.get_recent_interactions.assert_called_once_with(10, 20)

    def test_get_recent_interactions_empty(self, service, mock_repository):
        """Test getting recent interactions when none exist."""
        mock_repository.get_recent_interactions.return_value = []

        results = service.get_recent_interactions()

        assert results == []


class TestGetStats:
    """Tests for get_stats method."""

    def test_get_stats_success(self, service, mock_repository):
        """Test getting feedback statistics."""
        stats = FeedbackStats(
            total_interactions=100,
            total_feedback=75,
            positive_count=60,
            negative_count=15,
            feedback_rate=75.0,
            positive_rate=80.0,
        )
        mock_repository.get_stats.return_value = stats

        result = service.get_stats()

        assert result.total_interactions == 100
        assert result.total_feedback == 75
        assert result.positive_count == 60
        assert result.negative_count == 15
        assert result.feedback_rate == 75.0
        assert result.positive_rate == 80.0

        mock_repository.get_stats.assert_called_once()

    def test_get_stats_empty_database(self, service, mock_repository):
        """Test getting stats when database is empty."""
        empty_stats = FeedbackStats(
            total_interactions=0,
            total_feedback=0,
            positive_count=0,
            negative_count=0,
            feedback_rate=0.0,
            positive_rate=0.0,
        )
        mock_repository.get_stats.return_value = empty_stats

        result = service.get_stats()

        assert result.total_interactions == 0
        assert result.feedback_rate == 0.0


class TestGetNegativeFeedbackWithComments:
    """Tests for get_negative_feedback_with_comments method."""

    def test_get_negative_feedback_success(self, service, mock_repository):
        """Test getting negative feedback with comments."""
        interactions = [
            ChatInteractionResponse(
                id="int-1",
                query="Query 1",
                response="Response 1",
                sources=[],
                processing_time_ms=100,
                created_at=datetime.utcnow(),
                feedback=FeedbackResponse(
                    id=1,
                    interaction_id="int-1",
                    rating=FeedbackRating.NEGATIVE,
                    comment="Inaccurate",
                    created_at=datetime.utcnow(),
                ),
            ),
            ChatInteractionResponse(
                id="int-2",
                query="Query 2",
                response="Response 2",
                sources=[],
                processing_time_ms=150,
                created_at=datetime.utcnow(),
                feedback=FeedbackResponse(
                    id=2,
                    interaction_id="int-2",
                    rating=FeedbackRating.NEGATIVE,
                    comment="Wrong answer",
                    created_at=datetime.utcnow(),
                ),
            ),
        ]
        mock_repository.get_negative_feedback_with_comments.return_value = interactions

        results = service.get_negative_feedback_with_comments()

        assert len(results) == 2
        assert results[0].feedback.rating == FeedbackRating.NEGATIVE
        assert results[0].feedback.comment == "Inaccurate"
        assert results[1].feedback.comment == "Wrong answer"

        mock_repository.get_negative_feedback_with_comments.assert_called_once()

    def test_get_negative_feedback_empty(self, service, mock_repository):
        """Test getting negative feedback when none exists."""
        mock_repository.get_negative_feedback_with_comments.return_value = []

        results = service.get_negative_feedback_with_comments()

        assert results == []
