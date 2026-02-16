"""
FILE: test_chat.py
STATUS: Active
RESPONSIBILITY: Unit tests for ChatService RAG pipeline orchestration
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

from unittest.mock import MagicMock

import numpy as np
import pytest

from src.core.exceptions import IndexNotFoundError, LLMError
from src.models.chat import ChatRequest, ChatResponse, SearchResult
from src.models.document import DocumentChunk
from src.services.chat import ChatService


@pytest.fixture
def mock_vector_store():
    store = MagicMock()
    store.is_loaded = True
    store.load.return_value = True
    return store


@pytest.fixture
def mock_feedback_repo():
    """Mock feedback repository."""
    repo = MagicMock()
    repo.record_interaction.return_value = None
    return repo


@pytest.fixture
def mock_client():
    """Mock Gemini client."""
    client = MagicMock()
    response = MagicMock()
    response.text = "The Denver Nuggets won the 2023 NBA Championship."
    client.models.generate_content.return_value = response
    return client


@pytest.fixture
def chat_service(mock_vector_store, mock_feedback_repo, mock_client):
    """Create ChatService with current API signature."""
    service = ChatService(
        vector_store=mock_vector_store,
        feedback_repo=mock_feedback_repo,
        enable_sql=True,
        model="test-model",
        temperature=0.1,
    )
    service._client = mock_client
    return service


class TestChatServiceInit:
    def test_init_with_injected_dependencies(self, mock_vector_store, mock_feedback_repo):
        """Test initialization with injected dependencies (current API)."""
        service = ChatService(
            vector_store=mock_vector_store,
            feedback_repo=mock_feedback_repo,
            enable_sql=True,
            model="my-model",
            temperature=0.5,
        )
        assert service.model == "my-model"
        assert service._temperature == 0.5
        assert service.vector_store is mock_vector_store
        assert service.feedback_repo is mock_feedback_repo
        assert service._enable_sql is True

    def test_model_property(self, chat_service):
        assert chat_service.model == "test-model"

    def test_is_ready_when_loaded(self, chat_service, mock_vector_store):
        mock_vector_store.is_loaded = True
        assert chat_service.is_ready is True

    def test_is_ready_when_not_loaded(self, chat_service, mock_vector_store):
        mock_vector_store.is_loaded = False
        assert chat_service.is_ready is False


class TestChatServiceEnsureReady:
    def test_ensure_ready_already_loaded(self, chat_service, mock_vector_store):
        mock_vector_store.is_loaded = True
        chat_service.ensure_ready()

    def test_ensure_ready_raises_when_no_index(self, chat_service, mock_vector_store):
        mock_vector_store.is_loaded = False
        mock_vector_store.load.return_value = False
        with pytest.raises(IndexNotFoundError):
            chat_service.ensure_ready()


# ============================================================================
# REMOVED: Tests for OLD RAG Architecture (Pre-ReAct Agent Migration)
# ============================================================================
# The following test classes were removed because they test methods that no
# longer exist after the migration to ReAct agent architecture:
#
# - TestChatServiceSearch (6 tests) - search() method removed
#   The agent now handles search internally via tool selection
#
# - TestChatServiceGenerateResponse (6 tests) - generate_response() removed
#   The agent now generates responses via its own execution flow
#
# - TestChatServiceChat (4 tests) - Old chat() behavior with direct RAG
#   The new chat() uses ReAct agent with tool orchestration
#
# - TestGreetingHandling (4 tests) - Old greeting detection logic
#   Greeting handling now managed by the agent's query classification
#
# Total: 20 tests removed for obsolete methods
# Current ChatService uses ReAct agent for all query processing
# ============================================================================


# NOTE: TestChatServiceSearch removed - search() method no longer exists (see above)
# NOTE: TestChatServiceGenerateResponse removed - generate_response() no longer exists (see above)
# NOTE: TestChatServiceChat removed - Old RAG-based chat() replaced by agent orchestration (see above)
# NOTE: TestGreetingHandling removed - Greeting logic now in agent's query classifier (see above)
