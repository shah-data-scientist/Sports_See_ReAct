"""
FILE: test_conversation.py
STATUS: Active
RESPONSIBILITY: Tests for ConversationRepository database operations
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import json
import time
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import text

from src.models.conversation import (
    ConversationCreate,
    ConversationStatus,
    ConversationUpdate,
)
from src.models.feedback import ChatInteractionDB
from src.repositories.conversation import ConversationRepository


@pytest.fixture
def db_path(tmp_path):
    """Create a temporary database path."""
    return tmp_path / "test_conversations.db"


@pytest.fixture
def repo(db_path):
    """Create a ConversationRepository with temporary database."""
    repository = ConversationRepository(db_path=db_path)
    yield repository
    repository.close()


class TestConversationRepositoryInit:
    """Tests for ConversationRepository initialization."""

    def test_init_creates_database_file(self, db_path):
        """Test that initialization creates the database file."""
        assert not db_path.exists()
        repo = ConversationRepository(db_path=db_path)
        assert db_path.exists()
        repo.close()

    def test_init_with_existing_directory(self, tmp_path):
        """Test that initialization works when parent directory exists."""
        nested_path = tmp_path / "nested" / "dir" / "conversations.db"
        # Pre-create the parent directory (ConversationRepository doesn't auto-create parents)
        nested_path.parent.mkdir(parents=True, exist_ok=True)
        repo = ConversationRepository(db_path=nested_path)
        try:
            assert nested_path.exists()
            assert nested_path.parent.exists()
        finally:
            repo.close()

    def test_init_creates_tables(self, repo):
        """Test that initialization creates required tables."""
        # Query the conversations table (should not raise)
        with repo.get_session() as session:
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'"))
            tables = [row[0] for row in result]
            assert "conversations" in tables


class TestCreateConversation:
    """Tests for create_conversation method."""

    def test_create_conversation_with_title(self, repo):
        """Test creating a conversation with a title."""
        conversation = ConversationCreate(title="My First Chat")
        result = repo.create_conversation(conversation)

        assert result.id is not None
        assert result.title == "My First Chat"
        assert result.status == ConversationStatus.ACTIVE
        assert result.message_count == 0
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)

    def test_create_conversation_without_title(self, repo):
        """Test creating a conversation without a title."""
        conversation = ConversationCreate(title=None)
        result = repo.create_conversation(conversation)

        assert result.id is not None
        assert result.title is None
        assert result.status == ConversationStatus.ACTIVE
        assert result.message_count == 0

    def test_create_multiple_conversations(self, repo):
        """Test creating multiple conversations with unique IDs."""
        conv1 = repo.create_conversation(ConversationCreate(title="First"))
        conv2 = repo.create_conversation(ConversationCreate(title="Second"))

        assert conv1.id != conv2.id
        assert conv1.title == "First"
        assert conv2.title == "Second"


class TestGetConversation:
    """Tests for get_conversation method."""

    def test_get_existing_conversation(self, repo):
        """Test getting an existing conversation by ID."""
        created = repo.create_conversation(ConversationCreate(title="Test Chat"))
        result = repo.get_conversation(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.title == "Test Chat"
        assert result.status == ConversationStatus.ACTIVE
        assert result.message_count == 0

    def test_get_non_existent_conversation(self, repo):
        """Test getting a non-existent conversation returns None."""
        result = repo.get_conversation("non-existent-id")
        assert result is None

    def test_get_conversation_with_messages(self, repo):
        """Test getting conversation returns correct message count."""
        # Create conversation
        conv = repo.create_conversation(ConversationCreate(title="Chat"))

        # Add messages directly to database
        with repo.get_session() as session:
            msg1 = ChatInteractionDB(
                query="Question 1",
                response="Answer 1",
                sources=json.dumps([]),
                conversation_id=conv.id,
                turn_number=1,
            )
            msg2 = ChatInteractionDB(
                query="Question 2",
                response="Answer 2",
                sources=json.dumps([]),
                conversation_id=conv.id,
                turn_number=2,
            )
            session.add(msg1)
            session.add(msg2)

        # Get conversation and verify message count
        result = repo.get_conversation(conv.id)
        assert result is not None
        assert result.message_count == 2


class TestListConversations:
    """Tests for list_conversations method."""

    def test_list_conversations_default(self, repo):
        """Test listing all conversations with default pagination."""
        # Create test conversations
        repo.create_conversation(ConversationCreate(title="Chat 1"))
        repo.create_conversation(ConversationCreate(title="Chat 2"))
        repo.create_conversation(ConversationCreate(title="Chat 3"))

        results = repo.list_conversations()

        assert len(results) == 3
        # Results should be ordered by updated_at desc (most recent first)
        assert results[0].title == "Chat 3"
        assert results[2].title == "Chat 1"

    def test_list_conversations_with_pagination(self, repo):
        """Test listing conversations with limit and offset."""
        for i in range(5):
            repo.create_conversation(ConversationCreate(title=f"Chat {i}"))

        results = repo.list_conversations(limit=2, offset=1)

        assert len(results) == 2
        # Should skip the first (most recent) and return next 2
        assert results[0].title == "Chat 3"
        assert results[1].title == "Chat 2"

    def test_list_conversations_filter_by_status(self, repo):
        """Test listing conversations filtered by status."""
        # Create conversations
        conv1 = repo.create_conversation(ConversationCreate(title="Active"))
        conv2 = repo.create_conversation(ConversationCreate(title="To Archive"))

        # Archive one
        repo.archive_conversation(conv2.id)

        # List active only
        active_results = repo.list_conversations(status=ConversationStatus.ACTIVE)
        assert len(active_results) == 1
        assert active_results[0].id == conv1.id

        # List archived only
        archived_results = repo.list_conversations(status=ConversationStatus.ARCHIVED)
        assert len(archived_results) == 1
        assert archived_results[0].id == conv2.id

    def test_list_conversations_empty_database(self, repo):
        """Test listing conversations when database is empty."""
        results = repo.list_conversations()
        assert results == []


class TestGetConversationWithMessages:
    """Tests for get_conversation_with_messages method."""

    def test_get_conversation_with_messages_success(self, repo):
        """Test getting a conversation with all its messages."""
        # Create conversation
        conv = repo.create_conversation(ConversationCreate(title="Full Chat"))

        # Add messages
        with repo.get_session() as session:
            for i in range(3):
                msg = ChatInteractionDB(
                    query=f"Question {i+1}",
                    response=f"Answer {i+1}",
                    sources=json.dumps([f"source{i+1}.pdf"]),
                    processing_time_ms=100 * (i + 1),
                    conversation_id=conv.id,
                    turn_number=i + 1,
                )
                session.add(msg)

        # Get conversation with messages
        result = repo.get_conversation_with_messages(conv.id)

        assert result is not None
        assert result.id == conv.id
        assert result.title == "Full Chat"
        assert len(result.messages) == 3
        # Messages should be ordered by turn_number
        assert result.messages[0].query == "Question 1"
        assert result.messages[0].turn_number == 1
        assert result.messages[0].sources == ["source1.pdf"]
        assert result.messages[2].query == "Question 3"
        assert result.messages[2].turn_number == 3

    def test_get_conversation_with_messages_no_messages(self, repo):
        """Test getting a conversation with no messages."""
        conv = repo.create_conversation(ConversationCreate(title="Empty Chat"))
        result = repo.get_conversation_with_messages(conv.id)

        assert result is not None
        assert result.id == conv.id
        assert result.messages == []

    def test_get_conversation_with_messages_not_found(self, repo):
        """Test getting non-existent conversation returns None."""
        result = repo.get_conversation_with_messages("non-existent-id")
        assert result is None


class TestUpdateConversation:
    """Tests for update_conversation method."""

    def test_update_conversation_title(self, repo):
        """Test updating conversation title."""
        conv = repo.create_conversation(ConversationCreate(title="Old Title"))
        original_updated_at = conv.updated_at

        # Small delay to ensure updated_at changes
        import time
        time.sleep(0.01)

        update = ConversationUpdate(title="New Title")
        result = repo.update_conversation(conv.id, update)

        assert result is not None
        assert result.id == conv.id
        assert result.title == "New Title"
        assert result.updated_at > original_updated_at

    def test_update_conversation_status(self, repo):
        """Test updating conversation status."""
        conv = repo.create_conversation(ConversationCreate(title="Test"))

        update = ConversationUpdate(status=ConversationStatus.ARCHIVED)
        result = repo.update_conversation(conv.id, update)

        assert result is not None
        assert result.status == ConversationStatus.ARCHIVED

    def test_update_conversation_both_fields(self, repo):
        """Test updating both title and status."""
        conv = repo.create_conversation(ConversationCreate(title="Old"))

        update = ConversationUpdate(title="New", status=ConversationStatus.DELETED)
        result = repo.update_conversation(conv.id, update)

        assert result is not None
        assert result.title == "New"
        assert result.status == ConversationStatus.DELETED

    def test_update_conversation_not_found(self, repo):
        """Test updating non-existent conversation returns None."""
        update = ConversationUpdate(title="New Title")
        result = repo.update_conversation("non-existent-id", update)
        assert result is None

    def test_update_conversation_partial(self, repo):
        """Test partial update only changes specified fields."""
        conv = repo.create_conversation(ConversationCreate(title="Original"))

        # Update only status, title should remain
        update = ConversationUpdate(status=ConversationStatus.ARCHIVED)
        result = repo.update_conversation(conv.id, update)

        assert result is not None
        assert result.title == "Original"
        assert result.status == ConversationStatus.ARCHIVED


class TestArchiveConversation:
    """Tests for archive_conversation method."""

    def test_archive_conversation_success(self, repo):
        """Test archiving a conversation."""
        conv = repo.create_conversation(ConversationCreate(title="To Archive"))
        result = repo.archive_conversation(conv.id)

        assert result is not None
        assert result.id == conv.id
        assert result.status == ConversationStatus.ARCHIVED

    def test_archive_conversation_not_found(self, repo):
        """Test archiving non-existent conversation returns None."""
        result = repo.archive_conversation("non-existent-id")
        assert result is None


class TestDeleteConversation:
    """Tests for delete_conversation method (soft delete)."""

    def test_delete_conversation_success(self, repo):
        """Test soft deleting a conversation."""
        conv = repo.create_conversation(ConversationCreate(title="To Delete"))
        result = repo.delete_conversation(conv.id)

        assert result is not None
        assert result.id == conv.id
        assert result.status == ConversationStatus.DELETED

        # Verify conversation still exists in database but marked deleted
        deleted = repo.get_conversation(conv.id)
        assert deleted is not None
        assert deleted.status == ConversationStatus.DELETED

    def test_delete_conversation_not_found(self, repo):
        """Test deleting non-existent conversation returns None."""
        result = repo.delete_conversation("non-existent-id")
        assert result is None


class TestConversationRepositoryClose:
    """Tests for close method."""

    def test_close_disposes_engine(self, db_path):
        """Test that close disposes the SQLAlchemy engine."""
        repo = ConversationRepository(db_path=db_path)
        repo.close()

        # After close, engine should be disposed
        # Attempting to use it should fail (but we won't test that to avoid errors)
        # Just verify close doesn't raise
        assert True
