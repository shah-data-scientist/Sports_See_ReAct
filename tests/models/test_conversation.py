"""
FILE: test_conversation_models.py
STATUS: Active
RESPONSIBILITY: Test conversation Pydantic models and validation
LAST MAJOR UPDATE: 2026-02-09
MAINTAINER: Shahu
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationStatus,
    ConversationUpdate,
    ConversationWithMessages,
)


class TestConversationModels:
    """Test suite for conversation Pydantic models."""

    def test_conversation_status_enum(self):
        """Test ConversationStatus enum values."""
        assert ConversationStatus.ACTIVE == "active"
        assert ConversationStatus.ARCHIVED == "archived"
        assert ConversationStatus.DELETED == "deleted"
        assert len(ConversationStatus) == 3

    def test_conversation_create_minimal(self):
        """Test ConversationCreate with minimal fields."""
        conv = ConversationCreate()
        assert conv.title is None

    def test_conversation_create_with_title(self):
        """Test ConversationCreate with title."""
        conv = ConversationCreate(title="My Conversation")
        assert conv.title == "My Conversation"

    def test_conversation_create_title_too_long(self):
        """Test ConversationCreate rejects overly long titles."""
        with pytest.raises(ValidationError) as exc_info:
            ConversationCreate(title="a" * 201)
        assert "at most 200 characters" in str(exc_info.value)

    def test_conversation_update_minimal(self):
        """Test ConversationUpdate with no fields."""
        update = ConversationUpdate()
        assert update.title is None
        assert update.status is None

    def test_conversation_update_title(self):
        """Test ConversationUpdate with title."""
        update = ConversationUpdate(title="New Title")
        assert update.title == "New Title"
        assert update.status is None

    def test_conversation_update_status(self):
        """Test ConversationUpdate with status."""
        update = ConversationUpdate(status=ConversationStatus.ARCHIVED)
        assert update.title is None
        assert update.status == ConversationStatus.ARCHIVED

    def test_conversation_update_both(self):
        """Test ConversationUpdate with both fields."""
        update = ConversationUpdate(
            title="Archived Chat",
            status=ConversationStatus.ARCHIVED
        )
        assert update.title == "Archived Chat"
        assert update.status == ConversationStatus.ARCHIVED

    def test_conversation_response(self):
        """Test ConversationResponse model."""
        now = datetime.utcnow()
        response = ConversationResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            title="Test Conversation",
            created_at=now,
            updated_at=now,
            status=ConversationStatus.ACTIVE,
            message_count=5,
        )
        assert response.id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.title == "Test Conversation"
        assert response.status == ConversationStatus.ACTIVE
        assert response.message_count == 5

    def test_conversation_response_default_message_count(self):
        """Test ConversationResponse with default message count."""
        now = datetime.utcnow()
        response = ConversationResponse(
            id="123",
            title=None,
            created_at=now,
            updated_at=now,
            status=ConversationStatus.ACTIVE,
        )
        assert response.message_count == 0

    def test_conversation_with_messages_empty(self):
        """Test ConversationWithMessages with no messages."""
        now = datetime.utcnow()
        conv = ConversationWithMessages(
            id="123",
            title="Empty Chat",
            created_at=now,
            updated_at=now,
            status=ConversationStatus.ACTIVE,
            messages=[],
        )
        assert conv.id == "123"
        assert conv.title == "Empty Chat"
        assert len(conv.messages) == 0

    def test_conversation_with_messages_default_empty_list(self):
        """Test ConversationWithMessages defaults to empty message list."""
        now = datetime.utcnow()
        conv = ConversationWithMessages(
            id="123",
            title="Chat",
            created_at=now,
            updated_at=now,
            status=ConversationStatus.ACTIVE,
        )
        assert conv.messages == []
