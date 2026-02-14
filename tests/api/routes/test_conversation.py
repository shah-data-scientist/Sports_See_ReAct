"""
FILE: test_conversation.py
STATUS: Active
RESPONSIBILITY: Tests for conversation models, API routes, and service layer
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.api.routes.conversation import router
from src.models.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationStatus,
    ConversationUpdate,
    ConversationWithMessages,
)


# ============================================================================
# MODEL TESTS
# ============================================================================


class TestConversationStatus:
    """Tests for ConversationStatus enum."""

    def test_active_value(self):
        """ACTIVE status has correct string value."""
        assert ConversationStatus.ACTIVE == "active"

    def test_archived_value(self):
        """ARCHIVED status has correct string value."""
        assert ConversationStatus.ARCHIVED == "archived"

    def test_deleted_value(self):
        """DELETED status has correct string value."""
        assert ConversationStatus.DELETED == "deleted"

    def test_all_statuses_count(self):
        """Enum has exactly 3 statuses."""
        assert len(ConversationStatus) == 3


class TestConversationCreate:
    """Tests for ConversationCreate model validation."""

    def test_create_with_title(self):
        """ConversationCreate accepts optional title."""
        create = ConversationCreate(title="My Chat")
        assert create.title == "My Chat"

    def test_create_without_title(self):
        """ConversationCreate works without title (defaults to None)."""
        create = ConversationCreate()
        assert create.title is None

    def test_title_max_length_enforced(self):
        """Title exceeding 200 chars is rejected."""
        with pytest.raises(ValidationError):
            ConversationCreate(title="x" * 201)


class TestConversationUpdate:
    """Tests for ConversationUpdate model validation."""

    def test_update_title_only(self):
        """ConversationUpdate with title only."""
        update = ConversationUpdate(title="New Title")
        assert update.title == "New Title"
        assert update.status is None

    def test_update_status_only(self):
        """ConversationUpdate with status only."""
        update = ConversationUpdate(status=ConversationStatus.ARCHIVED)
        assert update.title is None
        assert update.status == ConversationStatus.ARCHIVED


class TestConversationResponse:
    """Tests for ConversationResponse model."""

    def test_from_attributes_config(self):
        """ConversationResponse has from_attributes enabled."""
        assert ConversationResponse.model_config.get("from_attributes") is True

    def test_response_creation(self):
        """ConversationResponse can be created with all fields."""
        now = datetime.utcnow()
        resp = ConversationResponse(
            id="abc-123",
            title="Test",
            created_at=now,
            updated_at=now,
            status=ConversationStatus.ACTIVE,
            message_count=5,
        )
        assert resp.id == "abc-123"
        assert resp.message_count == 5


# ============================================================================
# API ROUTE TESTS
# ============================================================================


@pytest.fixture
def app():
    """Create FastAPI app with conversation router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_conv_response():
    """Build a sample ConversationResponse for mocking."""
    now = datetime.utcnow()
    return ConversationResponse(
        id="conv-001",
        title="Test Conversation",
        created_at=now,
        updated_at=now,
        status=ConversationStatus.ACTIVE,
        message_count=0,
    )


class TestConversationRoutes:
    """Tests for conversation API routes."""

    def test_create_conversation(self, client, mock_conv_response):
        """POST /conversations creates a new conversation."""
        mock_service = MagicMock()
        mock_service.start_conversation.return_value = mock_conv_response

        with patch(
            "src.api.routes.conversation.get_conversation_service",
            return_value=mock_service,
        ):
            response = client.post(
                "/conversations", json={"title": "My New Chat"}
            )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "conv-001"
        assert data["status"] == "active"

    def test_get_nonexistent_conversation_returns_404(self, client):
        """GET /conversations/{id} for missing ID returns 404."""
        mock_service = MagicMock()
        mock_service.get_conversation.return_value = None

        with patch(
            "src.api.routes.conversation.get_conversation_service",
            return_value=mock_service,
        ):
            response = client.get("/conversations/nonexistent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_nonexistent_conversation_returns_404(self, client):
        """DELETE /conversations/{id} for missing ID returns 404."""
        mock_service = MagicMock()
        mock_service.delete.return_value = None

        with patch(
            "src.api.routes.conversation.get_conversation_service",
            return_value=mock_service,
        ):
            response = client.delete("/conversations/nonexistent-id")

        assert response.status_code == 404
