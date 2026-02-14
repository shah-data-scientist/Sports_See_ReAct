"""
FILE: test_conversation.py
STATUS: Active
RESPONSIBILITY: Tests for ConversationService business logic
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

import tempfile
import time
from pathlib import Path

import pytest

from src.models.conversation import ConversationStatus
from src.repositories.conversation import ConversationRepository
from src.services.conversation import ConversationService


@pytest.fixture
def temp_db():
    """Create a temporary database path for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        yield db_path


@pytest.fixture
def repository(temp_db):
    """Create a ConversationRepository with temporary database."""
    repo = ConversationRepository(db_path=temp_db)
    yield repo
    repo.close()  # Properly close to release file lock on Windows


@pytest.fixture
def service(repository):
    """Create a ConversationService with test repository."""
    return ConversationService(repository=repository)


class TestConversationService:
    """Tests for ConversationService business logic."""

    def test_service_init(self, service):
        """Test service initialization."""
        assert service is not None
        assert service.repository is not None

    def test_start_conversation_no_title(self, service):
        """Test starting a conversation without a title."""
        conv = service.start_conversation()
        assert conv.id is not None
        assert conv.title is None
        assert conv.status == ConversationStatus.ACTIVE
        assert conv.message_count == 0

    def test_start_conversation_with_title(self, service):
        """Test starting a conversation with a title."""
        conv = service.start_conversation(title="NBA Discussion")
        assert conv.title == "NBA Discussion"
        assert conv.status == ConversationStatus.ACTIVE

    def test_get_conversation_exists(self, service):
        """Test getting an existing conversation."""
        created = service.start_conversation(title="Test")
        retrieved = service.get_conversation(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Test"

    def test_get_conversation_not_found(self, service):
        """Test getting a non-existent conversation."""
        result = service.get_conversation("nonexistent-id")
        assert result is None

    def test_list_conversations_empty(self, service):
        """Test listing conversations when none exist."""
        conversations = service.list_conversations()
        assert conversations == []

    def test_list_conversations(self, service):
        """Test listing conversations."""
        conv1 = service.start_conversation(title="First")
        time.sleep(0.01)
        conv2 = service.start_conversation(title="Second")
        time.sleep(0.01)
        conv3 = service.start_conversation(title="Third")

        conversations = service.list_conversations()
        assert len(conversations) == 3
        # Should be ordered by updated_at (most recent first)
        assert conversations[0].id == conv3.id
        assert conversations[1].id == conv2.id
        assert conversations[2].id == conv1.id

    def test_list_conversations_with_status_filter(self, service):
        """Test listing conversations filtered by status."""
        conv1 = service.start_conversation(title="Active")
        conv2 = service.start_conversation(title="To Archive")
        service.archive(conv2.id)

        # List only active
        active = service.list_conversations(status=ConversationStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].id == conv1.id

        # List only archived
        archived = service.list_conversations(status=ConversationStatus.ARCHIVED)
        assert len(archived) == 1
        assert archived[0].id == conv2.id

    def test_list_conversations_pagination(self, service):
        """Test pagination in list_conversations."""
        # Create 5 conversations
        for i in range(5):
            service.start_conversation(title=f"Conv {i}")

        # Get first 2
        page1 = service.list_conversations(limit=2, offset=0)
        assert len(page1) == 2

        # Get next 2
        page2 = service.list_conversations(limit=2, offset=2)
        assert len(page2) == 2

        # Ensure different conversations
        assert page1[0].id != page2[0].id

    def test_get_conversation_history_empty(self, service):
        """Test getting history of a conversation with no messages."""
        conv = service.start_conversation(title="Empty")
        history = service.get_conversation_history(conv.id)
        assert history is not None
        assert history.id == conv.id
        assert len(history.messages) == 0

    def test_get_conversation_history_not_found(self, service):
        """Test getting history of non-existent conversation."""
        result = service.get_conversation_history("nonexistent-id")
        assert result is None

    def test_update_title(self, service):
        """Test updating conversation title."""
        conv = service.start_conversation(title="Old Title")
        updated = service.update_title(conv.id, "New Title")
        assert updated is not None
        assert updated.title == "New Title"
        assert updated.id == conv.id

    def test_update_title_not_found(self, service):
        """Test updating title of non-existent conversation."""
        result = service.update_title("nonexistent-id", "New Title")
        assert result is None

    def test_archive_conversation(self, service):
        """Test archiving a conversation."""
        conv = service.start_conversation(title="To Archive")
        archived = service.archive(conv.id)
        assert archived is not None
        assert archived.status == ConversationStatus.ARCHIVED
        assert archived.id == conv.id

    def test_archive_not_found(self, service):
        """Test archiving non-existent conversation."""
        result = service.archive("nonexistent-id")
        assert result is None

    def test_delete_conversation(self, service):
        """Test deleting a conversation (soft delete)."""
        conv = service.start_conversation(title="To Delete")
        deleted = service.delete(conv.id)
        assert deleted is not None
        assert deleted.status == ConversationStatus.DELETED
        assert deleted.id == conv.id

    def test_delete_not_found(self, service):
        """Test deleting non-existent conversation."""
        result = service.delete("nonexistent-id")
        assert result is None

    def test_auto_generate_title_short_message(self, service):
        """Test title generation with short message."""
        message = "Who won the championship?"
        title = service.auto_generate_title(message)
        assert title == "Who won the championship?"

    def test_auto_generate_title_long_message(self, service):
        """Test title generation truncates long messages."""
        message = "This is a very long message that should be truncated to fit within the 50 character limit"
        title = service.auto_generate_title(message, max_length=50)
        assert len(title) <= 50
        assert title.endswith("...")
        assert title.startswith("This is a very long message")

    def test_auto_generate_title_custom_length(self, service):
        """Test title generation with custom max length."""
        message = "This is a medium length message"
        title = service.auto_generate_title(message, max_length=20)
        assert len(title) <= 20
        assert title.endswith("...")

    def test_update_conversation_after_message_new_conversation(self, service):
        """Test updating conversation after first message (creates title)."""
        conv = service.start_conversation()  # No title
        assert conv.title is None

        updated = service.update_conversation_after_message(
            conv.id,
            "Who is the best player?"
        )
        assert updated is not None
        assert updated.title == "Who is the best player?"

    def test_update_conversation_after_message_existing_title(self, service):
        """Test updating conversation that already has a title (doesn't change)."""
        conv = service.start_conversation(title="Existing Title")
        updated = service.update_conversation_after_message(
            conv.id,
            "Follow-up question"
        )
        assert updated is not None
        assert updated.title == "Existing Title"  # Should not change

    def test_update_conversation_after_message_not_found(self, service):
        """Test updating non-existent conversation after message."""
        result = service.update_conversation_after_message(
            "nonexistent-id",
            "Some message"
        )
        assert result is None

    def test_conversation_lifecycle(self, service):
        """Test complete conversation lifecycle."""
        # 1. Start conversation
        conv = service.start_conversation()
        assert conv.status == ConversationStatus.ACTIVE
        assert conv.title is None

        # 2. Update title after first message
        updated = service.update_conversation_after_message(
            conv.id,
            "First message"
        )
        assert updated.title == "First message"

        # 3. List shows conversation
        conversations = service.list_conversations(status=ConversationStatus.ACTIVE)
        assert len(conversations) == 1

        # 4. Archive conversation
        archived = service.archive(conv.id)
        assert archived.status == ConversationStatus.ARCHIVED

        # 5. No longer in active list
        active = service.list_conversations(status=ConversationStatus.ACTIVE)
        assert len(active) == 0

        # 6. Shows in archived list
        archived_list = service.list_conversations(status=ConversationStatus.ARCHIVED)
        assert len(archived_list) == 1
        assert archived_list[0].id == conv.id
