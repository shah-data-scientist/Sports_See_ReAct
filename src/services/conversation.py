"""
FILE: conversation.py
STATUS: Active
RESPONSIBILITY: Business logic for conversation management
LAST MAJOR UPDATE: 2026-02-09
MAINTAINER: Shahu
"""

import logging

from src.models.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationStatus,
    ConversationUpdate,
    ConversationWithMessages,
)
from src.repositories.conversation import ConversationRepository

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for conversation lifecycle management.

    Handles business logic for creating, retrieving, updating, and managing
    conversations.

    Attributes:
        repository: Conversation repository for data access
    """

    def __init__(self, repository: ConversationRepository | None = None):
        """Initialize conversation service.

        Args:
            repository: Conversation repository (created if not provided)
        """
        self.repository = repository or ConversationRepository()

    def start_conversation(self, title: str | None = None) -> ConversationResponse:
        """Start a new conversation.

        Args:
            title: Optional conversation title (auto-generated from first message if not provided)

        Returns:
            Created conversation with generated ID
        """
        conversation = ConversationCreate(title=title)
        result = self.repository.create_conversation(conversation)
        logger.info(f"Started new conversation: {result.id}")
        return result

    def get_conversation(self, conversation_id: str) -> ConversationResponse | None:
        """Get a conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation if found, None otherwise
        """
        return self.repository.get_conversation(conversation_id)

    def list_conversations(
        self,
        status: ConversationStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ConversationResponse]:
        """List conversations with pagination and filtering.

        Args:
            status: Filter by status (None = all statuses)
            limit: Maximum number of conversations to return (default: 20)
            offset: Number of conversations to skip (default: 0)

        Returns:
            List of conversations ordered by updated_at (most recent first)
        """
        return self.repository.list_conversations(status=status, limit=limit, offset=offset)

    def get_conversation_history(self, conversation_id: str) -> ConversationWithMessages | None:
        """Get full conversation history with all messages.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation with messages, or None if not found
        """
        return self.repository.get_conversation_with_messages(conversation_id)

    def update_title(self, conversation_id: str, title: str) -> ConversationResponse | None:
        """Update conversation title.

        Args:
            conversation_id: Conversation ID
            title: New title

        Returns:
            Updated conversation if found, None otherwise
        """
        update = ConversationUpdate(title=title)
        result = self.repository.update_conversation(conversation_id, update)
        if result:
            logger.info(f"Updated conversation {conversation_id} title to: {title}")
        return result

    def archive(self, conversation_id: str) -> ConversationResponse | None:
        """Archive a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Archived conversation if found, None otherwise
        """
        result = self.repository.archive_conversation(conversation_id)
        if result:
            logger.info(f"Archived conversation: {conversation_id}")
        return result

    def delete(self, conversation_id: str) -> ConversationResponse | None:
        """Soft delete a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Deleted conversation if found, None otherwise
        """
        result = self.repository.delete_conversation(conversation_id)
        if result:
            logger.info(f"Deleted conversation: {conversation_id}")
        return result

    def auto_generate_title(self, first_message: str, max_length: int = 50) -> str:
        """Auto-generate conversation title from first message.

        Args:
            first_message: First user message in conversation
            max_length: Maximum title length (default: 50)

        Returns:
            Generated title (truncated if needed)
        """
        # Clean and truncate
        title = first_message.strip()

        # Remove newlines and extra whitespace
        title = " ".join(title.split())

        # Truncate with ellipsis if too long
        if len(title) > max_length:
            title = title[: max_length - 3] + "..."

        return title

    def update_conversation_after_message(
        self, conversation_id: str, message_query: str
    ) -> ConversationResponse | None:
        """Update conversation title if it's the first message.

        Args:
            conversation_id: Conversation ID
            message_query: User's message query

        Returns:
            Updated conversation if title was generated, None if conversation not found
        """
        # Get conversation
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None

        # If no title set yet, auto-generate from message
        if not conversation.title:
            title = self.auto_generate_title(message_query)
            return self.update_title(conversation_id, title)

        return conversation
