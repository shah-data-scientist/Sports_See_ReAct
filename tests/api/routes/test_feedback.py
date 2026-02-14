"""
FILE: test_feedback.py
STATUS: Active
RESPONSIBILITY: Tests for feedback API routes
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.api.routes.feedback import router
from src.models.feedback import (
    ChatInteractionResponse,
    FeedbackCreate,
    FeedbackRating,
    FeedbackResponse,
    FeedbackStats,
)


@pytest.fixture
def mock_feedback_service():
    """Create a mock FeedbackService."""
    return MagicMock()


@pytest.fixture
def test_client(mock_feedback_service):
    """Create FastAPI test client with mocked service."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    # Patch the get_feedback_service dependency
    with patch("src.api.routes.feedback.get_feedback_service", return_value=mock_feedback_service):
        yield TestClient(app)


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


class TestSubmitFeedback:
    """Tests for POST /feedback endpoint."""

    def test_submit_positive_feedback_success(self, test_client, mock_feedback_service, sample_feedback):
        """Test submitting positive feedback successfully."""
        mock_feedback_service.submit_feedback.return_value = sample_feedback

        response = test_client.post(
            "/feedback",
            json={
                "interaction_id": "int-123",
                "rating": "positive",
                "comment": "Great answer!",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["interaction_id"] == "int-123"
        assert data["rating"] == "positive"
        assert data["comment"] == "Great answer!"

        mock_feedback_service.submit_feedback.assert_called_once_with(
            interaction_id="int-123",
            rating=FeedbackRating.POSITIVE,
            comment="Great answer!",
        )

    def test_submit_negative_feedback_with_comment(self, test_client, mock_feedback_service):
        """Test submitting negative feedback with comment."""
        negative_feedback = FeedbackResponse(
            id=2,
            interaction_id="int-456",
            rating=FeedbackRating.NEGATIVE,
            comment="Incorrect stats",
            created_at=datetime.utcnow(),
        )
        mock_feedback_service.submit_feedback.return_value = negative_feedback

        response = test_client.post(
            "/feedback",
            json={
                "interaction_id": "int-456",
                "rating": "negative",
                "comment": "Incorrect stats",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["rating"] == "negative"
        assert data["comment"] == "Incorrect stats"

    def test_submit_feedback_without_comment(self, test_client, mock_feedback_service):
        """Test submitting feedback without optional comment."""
        feedback_no_comment = FeedbackResponse(
            id=3,
            interaction_id="int-789",
            rating=FeedbackRating.POSITIVE,
            comment=None,
            created_at=datetime.utcnow(),
        )
        mock_feedback_service.submit_feedback.return_value = feedback_no_comment

        response = test_client.post(
            "/feedback",
            json={
                "interaction_id": "int-789",
                "rating": "positive",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["comment"] is None

    def test_submit_feedback_interaction_not_found(self, test_client, mock_feedback_service):
        """Test submitting feedback for non-existent interaction."""
        mock_feedback_service.submit_feedback.side_effect = ValueError("Interaction not-found not found")

        response = test_client.post(
            "/feedback",
            json={
                "interaction_id": "not-found",
                "rating": "positive",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not found" in response.json()["detail"]

    def test_submit_feedback_duplicate_fails(self, test_client, mock_feedback_service):
        """Test submitting duplicate feedback fails."""
        mock_feedback_service.submit_feedback.side_effect = ValueError(
            "Feedback already exists for interaction int-123"
        )

        response = test_client.post(
            "/feedback",
            json={
                "interaction_id": "int-123",
                "rating": "positive",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]


class TestUpdateFeedback:
    """Tests for PUT /feedback/{interaction_id} endpoint."""

    def test_update_feedback_success(self, test_client, mock_feedback_service):
        """Test updating feedback successfully."""
        updated_feedback = FeedbackResponse(
            id=1,
            interaction_id="int-123",
            rating=FeedbackRating.NEGATIVE,
            comment="Changed my mind",
            created_at=datetime.utcnow(),
        )
        mock_feedback_service.update_feedback.return_value = updated_feedback

        response = test_client.put(
            "/feedback/int-123",
            params={"rating": "negative", "comment": "Changed my mind"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["rating"] == "negative"
        assert data["comment"] == "Changed my mind"

        mock_feedback_service.update_feedback.assert_called_once_with(
            "int-123", FeedbackRating.NEGATIVE, "Changed my mind"
        )

    def test_update_feedback_not_found(self, test_client, mock_feedback_service):
        """Test updating non-existent feedback returns 404."""
        mock_feedback_service.update_feedback.return_value = None

        response = test_client.put(
            "/feedback/not-found",
            params={"rating": "positive"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]


class TestGetStats:
    """Tests for GET /feedback/stats endpoint."""

    def test_get_stats_success(self, test_client, mock_feedback_service):
        """Test getting feedback statistics."""
        stats = FeedbackStats(
            total_interactions=100,
            total_feedback=75,
            positive_count=60,
            negative_count=15,
            feedback_rate=75.0,
            positive_rate=80.0,
        )
        mock_feedback_service.get_stats.return_value = stats

        response = test_client.get("/feedback/stats")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_interactions"] == 100
        assert data["total_feedback"] == 75
        assert data["positive_count"] == 60
        assert data["negative_count"] == 15
        assert data["feedback_rate"] == 75.0
        assert data["positive_rate"] == 80.0

    def test_get_stats_empty_database(self, test_client, mock_feedback_service):
        """Test getting stats with no data."""
        stats = FeedbackStats(
            total_interactions=0,
            total_feedback=0,
            positive_count=0,
            negative_count=0,
            feedback_rate=0.0,
            positive_rate=0.0,
        )
        mock_feedback_service.get_stats.return_value = stats

        response = test_client.get("/feedback/stats")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_interactions"] == 0


class TestGetNegativeFeedback:
    """Tests for GET /feedback/negative endpoint."""

    def test_get_negative_feedback_success(self, test_client, mock_feedback_service):
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
        ]
        mock_feedback_service.get_negative_feedback_with_comments.return_value = interactions

        response = test_client.get("/feedback/negative")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "int-1"
        assert data[0]["feedback"]["rating"] == "negative"

    def test_get_negative_feedback_empty(self, test_client, mock_feedback_service):
        """Test getting negative feedback when none exists."""
        mock_feedback_service.get_negative_feedback_with_comments.return_value = []

        response = test_client.get("/feedback/negative")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []


class TestGetInteractions:
    """Tests for GET /feedback/interactions endpoint."""

    def test_get_interactions_default_pagination(self, test_client, mock_feedback_service, sample_interaction):
        """Test getting recent interactions with default pagination."""
        mock_feedback_service.get_recent_interactions.return_value = [sample_interaction]

        response = test_client.get("/feedback/interactions")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "int-123"

        mock_feedback_service.get_recent_interactions.assert_called_once_with(limit=50, offset=0)

    def test_get_interactions_custom_pagination(self, test_client, mock_feedback_service):
        """Test getting interactions with custom limit and offset."""
        mock_feedback_service.get_recent_interactions.return_value = []

        response = test_client.get("/feedback/interactions?limit=10&offset=20")

        assert response.status_code == status.HTTP_200_OK
        mock_feedback_service.get_recent_interactions.assert_called_once_with(limit=10, offset=20)

    def test_get_interactions_limit_exceeds_max(self, test_client, mock_feedback_service):
        """Test getting interactions with limit exceeding max (100)."""
        response = test_client.get("/feedback/interactions?limit=200")

        # FastAPI validation should reject this
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_interactions_negative_offset_fails(self, test_client, mock_feedback_service):
        """Test getting interactions with negative offset fails."""
        response = test_client.get("/feedback/interactions?offset=-1")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetInteraction:
    """Tests for GET /feedback/interactions/{interaction_id} endpoint."""

    def test_get_interaction_success(self, test_client, mock_feedback_service, sample_interaction):
        """Test getting a specific interaction by ID."""
        mock_feedback_service.get_interaction.return_value = sample_interaction

        response = test_client.get("/feedback/interactions/int-123")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "int-123"
        assert data["query"] == "What is LeBron's average?"

    def test_get_interaction_not_found(self, test_client, mock_feedback_service):
        """Test getting non-existent interaction returns 404."""
        mock_feedback_service.get_interaction.return_value = None

        response = test_client.get("/feedback/interactions/not-found")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
