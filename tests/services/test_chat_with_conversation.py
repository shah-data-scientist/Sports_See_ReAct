"""
FILE: test_chat_with_conversation.py
STATUS: Active
RESPONSIBILITY: Tests for ChatService with conversation context (pronoun resolution)
LAST MAJOR UPDATE: 2026-02-09
MAINTAINER: Shahu
"""

from datetime import datetime
from unittest.mock import MagicMock

import numpy as np
import pytest

from src.models.chat import ChatRequest, ChatResponse, SearchResult
from src.models.document import DocumentChunk
from src.models.feedback import ChatInteractionResponse
from src.services.chat import ChatService


@pytest.fixture
def mock_vector_store():
    """Mock vector store."""
    store = MagicMock()
    store.is_loaded = True
    store.load.return_value = True

    # Mock search results
    chunk = DocumentChunk(
        id="chunk-1",
        text="LeBron James scored 30 points in the game.",
        metadata={"source": "test.pdf", "page": 1},
    )
    store.search.return_value = [(chunk, 95.0)]
    return store


@pytest.fixture
def mock_feedback_repo():
    """Mock feedback repository with conversation history."""
    repo = MagicMock()

    # Default: no conversation history
    repo.get_messages_by_conversation.return_value = []

    return repo


@pytest.fixture
def mock_client():
    """Mock Gemini client."""
    client = MagicMock()
    response = MagicMock()
    response.text = "Test response"
    client.models.generate_content.return_value = response
    return client


@pytest.fixture
def chat_service_with_conversation(mock_vector_store, mock_feedback_repo, mock_client):
    """Create ChatService with mocked dependencies (current API)."""
    service = ChatService(
        vector_store=mock_vector_store,
        feedback_repo=mock_feedback_repo,
        enable_sql=False,  # Disable SQL for simpler testing
        model="test-model",
        temperature=0.1,
    )
    service._client = mock_client
    return service


class TestChatWithConversation:
    """Tests for chat with conversation context."""

    def test_chat_without_conversation_id(self, chat_service_with_conversation, mock_feedback_repo):
        """Test chat without conversation_id (no history)."""
        request = ChatRequest(
            query="Who scored the most points?",
            conversation_id=None,
            turn_number=1,
        )

        response = chat_service_with_conversation.chat(request)

        assert response is not None
        assert response.conversation_id is None
        assert response.turn_number == 1

        # Should not call get_messages_by_conversation
        mock_feedback_repo.get_messages_by_conversation.assert_not_called()

    def test_chat_with_conversation_id_no_history(self, chat_service_with_conversation, mock_feedback_repo):
        """Test chat with conversation_id but no previous messages."""
        mock_feedback_repo.get_messages_by_conversation.return_value = []

        request = ChatRequest(
            query="Who scored the most points?",
            conversation_id="conv-123",
            turn_number=1,
        )

        response = chat_service_with_conversation.chat(request)

        assert response.conversation_id == "conv-123"
        assert response.turn_number == 1

        # Should call get_messages but get empty list
        mock_feedback_repo.get_messages_by_conversation.assert_called_once_with("conv-123")

    def test_chat_with_conversation_history(self, chat_service_with_conversation, mock_feedback_repo, mock_client):
        """Test chat with conversation history."""
        # Setup conversation history
        previous_messages = [
            ChatInteractionResponse(
                id="msg-1",
                query="Who scored the most points?",
                response="LeBron James scored 30 points.",
                sources=[],
                processing_time_ms=100,
                created_at=datetime.utcnow(),
                conversation_id="conv-123",
                turn_number=1,
            )
        ]
        mock_feedback_repo.get_messages_by_conversation.return_value = previous_messages

        # Mock LLM response
        mock_response = MagicMock()
        mock_response.text = "He scored 30 points."
        mock_client.models.generate_content.return_value = mock_response

        request = ChatRequest(
            query="How many points did he score?",  # Pronoun "he"
            conversation_id="conv-123",
            turn_number=2,
        )

        response = chat_service_with_conversation.chat(request)

        assert response.conversation_id == "conv-123"
        assert response.turn_number == 2

        # Verify conversation history was retrieved
        mock_feedback_repo.get_messages_by_conversation.assert_called_once_with("conv-123")

        # Verify LLM was called with prompt containing conversation history
        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]["contents"]

        assert "CONVERSATION HISTORY:" in prompt
        assert "User: Who scored the most points?" in prompt
        assert "Assistant: LeBron James scored 30 points." in prompt

    def test_conversation_history_limit(self, chat_service_with_conversation, mock_feedback_repo, mock_client):
        """Test that conversation history is limited to last N turns."""
        # Create 10 messages (should only include last 5)
        messages = []
        for i in range(1, 11):
            messages.append(ChatInteractionResponse(
                id=f"msg-{i}",
                query=f"Question {i}",
                response=f"Answer {i}",
                sources=[],
                processing_time_ms=100,
                created_at=datetime.utcnow(),
                conversation_id="conv-123",
                turn_number=i,
            ))

        mock_feedback_repo.get_messages_by_conversation.return_value = messages

        request = ChatRequest(
            query="Follow-up question",
            conversation_id="conv-123",
            turn_number=11,
        )

        response = chat_service_with_conversation.chat(request)

        # Verify LLM was called
        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]["contents"]

        # Extract conversation history section
        history_start = prompt.find("CONVERSATION HISTORY:")
        history_end = prompt.find("---", history_start)
        history_section = prompt[history_start:history_end]

        # Should include messages 6-10 (last 5)
        assert "User: Question 6\n" in history_section
        assert "User: Question 10\n" in history_section

        # Should NOT include earlier messages (check with newline to avoid substring matches)
        assert "User: Question 1\n" not in history_section
        assert "User: Question 5\n" not in history_section

    def test_conversation_history_excludes_current_turn(self, chat_service_with_conversation, mock_feedback_repo, mock_client):
        """Test that conversation history excludes the current turn."""
        # Messages with turn numbers 1, 2, 3
        messages = [
            ChatInteractionResponse(
                id="msg-1",
                query="Question 1",
                response="Answer 1",
                sources=[],
                processing_time_ms=100,
                created_at=datetime.utcnow(),
                conversation_id="conv-123",
                turn_number=1,
            ),
            ChatInteractionResponse(
                id="msg-2",
                query="Question 2",
                response="Answer 2",
                sources=[],
                processing_time_ms=100,
                created_at=datetime.utcnow(),
                conversation_id="conv-123",
                turn_number=2,
            ),
            ChatInteractionResponse(
                id="msg-3",
                query="Question 3",  # Current turn - should be excluded
                response="Answer 3",
                sources=[],
                processing_time_ms=100,
                created_at=datetime.utcnow(),
                conversation_id="conv-123",
                turn_number=3,
            ),
        ]

        mock_feedback_repo.get_messages_by_conversation.return_value = messages

        request = ChatRequest(
            query="Question 3",  # Turn 3
            conversation_id="conv-123",
            turn_number=3,
        )

        response = chat_service_with_conversation.chat(request)

        # Verify LLM prompt
        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]["contents"]

        # Should include turns 1 and 2
        assert "Question 1" in prompt
        assert "Question 2" in prompt

        # Should NOT include turn 3 (current turn)
        # The current question appears in the prompt, but not as conversation history
        assert prompt.count("Question 3") == 1  # Only in USER QUESTION section

    def test_build_conversation_context_format(self, chat_service_with_conversation, mock_feedback_repo):
        """Test the format of conversation context."""
        messages = [
            ChatInteractionResponse(
                id="msg-1",
                query="Who is LeBron James?",
                response="LeBron James is a basketball player.",
                sources=[],
                processing_time_ms=100,
                created_at=datetime.utcnow(),
                conversation_id="conv-123",
                turn_number=1,
            ),
        ]
        mock_feedback_repo.get_messages_by_conversation.return_value = messages

        # Call _build_conversation_context directly
        context = chat_service_with_conversation._build_conversation_context("conv-123", 2)

        # Verify format
        assert context.startswith("CONVERSATION HISTORY:")
        assert "User: Who is LeBron James?" in context
        assert "Assistant: LeBron James is a basketball player." in context
        assert context.endswith("---\n")

    def test_build_conversation_context_empty(self, chat_service_with_conversation, mock_feedback_repo):
        """Test conversation context when no history exists."""
        mock_feedback_repo.get_messages_by_conversation.return_value = []

        context = chat_service_with_conversation._build_conversation_context("conv-123", 1)

        assert context == ""

    def test_chat_response_includes_conversation_fields(self, chat_service_with_conversation):
        """Test that ChatResponse includes conversation_id and turn_number."""
        request = ChatRequest(
            query="Test question",
            conversation_id="conv-456",
            turn_number=5,
        )

        response = chat_service_with_conversation.chat(request)

        assert response.conversation_id == "conv-456"
        assert response.turn_number == 5
        assert response.query == "Test question"

    def test_pronoun_resolution_scenario(self, chat_service_with_conversation, mock_feedback_repo, mock_client):
        """Test realistic pronoun resolution scenario."""
        # Conversation: "Who has the most points?" -> "LeBron" -> "What about his assists?"
        previous_messages = [
            ChatInteractionResponse(
                id="msg-1",
                query="Who has the most points in NBA history?",
                response="LeBron James has the most points in NBA history with 40,474 points.",
                sources=[],
                processing_time_ms=100,
                created_at=datetime.utcnow(),
                conversation_id="conv-789",
                turn_number=1,
            ),
        ]
        mock_feedback_repo.get_messages_by_conversation.return_value = previous_messages

        # Mock LLM to demonstrate it has context to resolve "his"
        mock_response = MagicMock()
        mock_response.text = "LeBron James has 10,420 assists in his career."
        mock_client.models.generate_content.return_value = mock_response

        request = ChatRequest(
            query="What about his assists?",  # "his" should resolve to LeBron
            conversation_id="conv-789",
            turn_number=2,
        )

        response = chat_service_with_conversation.chat(request)

        # Verify conversation context was provided
        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]["contents"]

        assert "CONVERSATION HISTORY:" in prompt
        assert "LeBron James" in prompt
        assert "his assists?" in prompt

    def test_conversation_context_with_sql_enabled(self, mock_vector_store, mock_feedback_repo, mock_client):
        """Test conversation context works with SQL tool enabled (current API)."""
        service = ChatService(
            vector_store=mock_vector_store,
            feedback_repo=mock_feedback_repo,
            enable_sql=True,  # Enable SQL
            model="test-model",
            temperature=0.1,
        )
        service._client = mock_client

        # Mock SQL tool to return None (not available)
        service._sql_tool = None

        previous_messages = [
            ChatInteractionResponse(
                id="msg-1",
                query="Previous question",
                response="Previous answer",
                sources=[],
                processing_time_ms=100,
                created_at=datetime.utcnow(),
                conversation_id="conv-123",
                turn_number=1,
            ),
        ]
        mock_feedback_repo.get_messages_by_conversation.return_value = previous_messages

        request = ChatRequest(
            query="Follow-up question",
            conversation_id="conv-123",
            turn_number=2,
        )

        response = service.chat(request)

        # Verify conversation context was included
        assert response.conversation_id == "conv-123"
        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]["contents"]
        assert "CONVERSATION HISTORY:" in prompt
