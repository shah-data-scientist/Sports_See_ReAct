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
def mock_embedding_service():
    service = MagicMock()
    service.embed_query.return_value = np.random.rand(64).astype(np.float32)
    return service


@pytest.fixture
def mock_client():
    """Mock Gemini client."""
    client = MagicMock()
    response = MagicMock()
    response.text = "The Denver Nuggets won the 2023 NBA Championship."
    client.models.generate_content.return_value = response
    return client


@pytest.fixture
def chat_service(mock_vector_store, mock_embedding_service, mock_client):
    service = ChatService(
        vector_store=mock_vector_store,
        embedding_service=mock_embedding_service,
        api_key="test-key",
        model="test-model",
    )
    service._client = mock_client
    return service


class TestChatServiceInit:
    def test_init_with_injected_dependencies(self, mock_vector_store, mock_embedding_service):
        service = ChatService(
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            api_key="my-key",
            model="my-model",
        )
        assert service._api_key == "my-key"
        assert service._model == "my-model"
        assert service._vector_store is mock_vector_store
        assert service._embedding_service is mock_embedding_service

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

    def test_ensure_ready_loads_index(self, chat_service, mock_vector_store):
        mock_vector_store.is_loaded = False
        mock_vector_store.load.return_value = True
        chat_service.ensure_ready()
        mock_vector_store.load.assert_called_once()

    def test_ensure_ready_raises_when_no_index(self, chat_service, mock_vector_store):
        mock_vector_store.is_loaded = False
        mock_vector_store.load.return_value = False
        with pytest.raises(IndexNotFoundError):
            chat_service.ensure_ready()


class TestChatServiceSearch:
    def test_search_returns_results(self, chat_service, mock_vector_store):
        chunk1 = DocumentChunk(
            id="0_0",
            text="The Nuggets won the championship.",
            metadata={"source": "nba_history.pdf", "page": 1},
        )
        chunk2 = DocumentChunk(
            id="0_1",
            text="Jokic was named MVP.",
            metadata={"source": "players.txt"},
        )
        mock_vector_store.search.return_value = [(chunk1, 95.0), (chunk2, 82.5)]

        results = chat_service.search(query="Who won?")

        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].text == "The Nuggets won the championship."
        assert results[0].score == 95.0
        assert results[0].source == "nba_history.pdf"
        assert results[0].metadata == {"page": 1}

    def test_search_empty_results(self, chat_service, mock_vector_store):
        mock_vector_store.search.return_value = []

        results = chat_service.search(query="Something obscure")

        assert results == []

    def test_search_passes_k_and_min_score(self, chat_service, mock_vector_store):
        mock_vector_store.search.return_value = []

        chat_service.search(query="test query", k=3, min_score=0.5)

        call_kwargs = mock_vector_store.search.call_args.kwargs
        assert call_kwargs["k"] == 3
        assert call_kwargs["min_score"] == 0.5

    def test_search_raises_when_index_not_loaded(self, chat_service, mock_vector_store):
        mock_vector_store.is_loaded = False
        mock_vector_store.load.return_value = False

        with pytest.raises(IndexNotFoundError):
            chat_service.search(query="test")

    def test_search_filters_source_from_metadata(self, chat_service, mock_vector_store):
        chunk = DocumentChunk(
            id="0_0",
            text="Some text",
            metadata={"source": "file.pdf", "page": 5, "category": "stats"},
        )
        mock_vector_store.search.return_value = [(chunk, 90.0)]

        results = chat_service.search(query="test")

        assert results[0].source == "file.pdf"
        assert "source" not in results[0].metadata
        assert results[0].metadata == {"page": 5, "category": "stats"}


class TestChatServiceGenerateResponse:
    def test_generate_response_success(self, chat_service):
        answer = chat_service.generate_response(query="Who won?", context="The Nuggets won.")

        assert answer == "The Denver Nuggets won the 2023 NBA Championship."

    def test_generate_response_no_choices(self, chat_service, mock_client):
        mock_client.models.generate_content.return_value.text = ""

        answer = chat_service.generate_response(query="test", context="ctx")

        assert answer == "I could not generate a response."

    def test_generate_response_sdk_error_raises_llm_error(self, chat_service, mock_client):
        from google.genai.errors import ClientError

        mock_client.models.generate_content.side_effect = ClientError(
            "API error", response_json={"error": "rate limit"}
        )

        with pytest.raises(LLMError, match="LLM API error"):
            chat_service.generate_response(query="test", context="ctx")

    def test_generate_response_generic_error_raises_llm_error(self, chat_service, mock_client):
        mock_client.models.generate_content.side_effect = ConnectionError("timeout")

        with pytest.raises(LLMError, match="LLM call failed"):
            chat_service.generate_response(query="test", context="ctx")

    def test_generate_response_calls_correct_model(self, chat_service, mock_client):
        chat_service.generate_response(query="q", context="c")

        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        assert call_kwargs["model"] == "test-model"

    def test_generate_response_includes_query_in_prompt(self, chat_service, mock_client):
        chat_service.generate_response(query="Who is MVP?", context="ctx")

        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        prompt = call_kwargs["contents"]
        assert "Who is MVP?" in prompt
        assert "ctx" in prompt


class TestChatServiceChat:
    def _make_search_results(self):
        return [
            SearchResult(text="The Nuggets won.", score=95.0, source="nba.pdf", metadata={}),
            SearchResult(text="Jokic was MVP.", score=82.0, source="players.txt", metadata={}),
        ]

    def test_chat_returns_response(self, chat_service, mock_vector_store, mock_client):
        chunk = DocumentChunk(
            id="0_0",
            text="The Nuggets won.",
            metadata={"source": "nba.pdf"},
        )
        mock_vector_store.search.return_value = [(chunk, 95.0)]

        request = ChatRequest(query="Who won the championship?")
        response = chat_service.chat(request)

        assert isinstance(response, ChatResponse)
        assert response.answer == "The Denver Nuggets won the 2023 NBA Championship."
        assert response.query == "Who won the championship?"
        assert response.model == "test-model"
        assert response.processing_time_ms >= 0
        assert len(response.sources) == 1

    def test_chat_no_search_results_uses_fallback_context(
        self, chat_service, mock_vector_store, mock_client
    ):
        mock_vector_store.search.return_value = []

        request = ChatRequest(query="Something unknown")
        chat_service.chat(request)

        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        prompt = call_kwargs["contents"]
        assert "No relevant information found" in prompt

    def test_chat_include_sources_false(self, chat_service, mock_vector_store, mock_client):
        chunk = DocumentChunk(
            id="0_0",
            text="Some text",
            metadata={"source": "file.pdf"},
        )
        mock_vector_store.search.return_value = [(chunk, 90.0)]

        request = ChatRequest(query="test", include_sources=False)
        response = chat_service.chat(request)

        assert response.sources == []

    def test_chat_formats_context_with_sources(self, chat_service, mock_vector_store, mock_client):
        chunk1 = DocumentChunk(id="0_0", text="Chunk A", metadata={"source": "a.pdf"})
        chunk2 = DocumentChunk(id="0_1", text="Chunk B", metadata={"source": "b.pdf"})
        mock_vector_store.search.return_value = [(chunk1, 90.0), (chunk2, 80.0)]

        request = ChatRequest(query="test")
        chat_service.chat(request)

        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        prompt = call_kwargs["contents"]
        assert "Source: a.pdf" in prompt
        assert "Source: b.pdf" in prompt
        assert "Chunk A" in prompt
        assert "Chunk B" in prompt

    def test_chat_passes_k_from_request(self, chat_service, mock_vector_store, mock_client):
        mock_vector_store.search.return_value = []

        request = ChatRequest(query="test", k=3)
        chat_service.chat(request)

        call_kwargs = mock_vector_store.search.call_args.kwargs
        assert call_kwargs["k"] == 3


class TestGreetingHandling:
    """Tests for greeting detection and early return in chat() (Phase 15)."""

    def test_greeting_returns_without_rag_search(self, chat_service, mock_vector_store):
        request = ChatRequest(query="hi")
        response = chat_service.chat(request)

        assert isinstance(response, ChatResponse)
        mock_vector_store.search.assert_not_called()
        assert "hi" in response.answer.lower() or "hello" in response.answer.lower() or "ask" in response.answer.lower()

    def test_greeting_returns_empty_sources(self, chat_service, mock_vector_store):
        request = ChatRequest(query="hello")
        response = chat_service.chat(request)

        assert response.sources == []
        mock_vector_store.search.assert_not_called()

    def test_thanks_greeting_response(self, chat_service, mock_vector_store):
        request = ChatRequest(query="thanks")
        response = chat_service.chat(request)

        assert "welcome" in response.answer.lower() or "help" in response.answer.lower()
        mock_vector_store.search.assert_not_called()

    def test_non_greeting_proceeds_to_search(self, chat_service, mock_vector_store, mock_client):
        from src.models.document import DocumentChunk

        chunk = DocumentChunk(id="0_0", text="NBA info", metadata={"source": "nba.pdf"})
        mock_vector_store.search.return_value = [(chunk, 90.0)]

        request = ChatRequest(query="Who are the top 5 scorers?")
        chat_service.chat(request)

        mock_vector_store.search.assert_called_once()


class TestBiographicalRewrite:
    """Tests for ChatService._rewrite_biographical_for_sql() static method (Phase 17)."""

    def test_rewrite_who_is_lebron(self):
        result = ChatService._rewrite_biographical_for_sql("Who is LeBron?")
        assert "name" in result.lower()
        assert "team" in result.lower()
        assert "age" in result.lower()
        assert "LeBron" in result

    def test_rewrite_tell_me_about(self):
        result = ChatService._rewrite_biographical_for_sql("Tell me about Kobe")
        assert "name" in result.lower()
        assert "points" in result.lower()
        assert "Kobe" in result

    def test_rewrite_preserves_player_name(self):
        result = ChatService._rewrite_biographical_for_sql("Who is Stephen Curry?")
        assert "Stephen Curry" in result

    def test_rewrite_fallback_uses_full_query(self):
        result = ChatService._rewrite_biographical_for_sql("random query")
        assert "random query" in result


class TestQuestionComplexity:
    """Tests verifying _estimate_question_complexity moved to QueryClassifier.

    Full tests are in test_query_classifier.py::TestEstimateQuestionComplexity.
    This test confirms the method is accessible via QueryClassifier.
    """

    def test_method_moved_to_classifier(self):
        from src.services.query_classifier import QueryClassifier
        assert hasattr(QueryClassifier, "_estimate_question_complexity")
        assert QueryClassifier._estimate_question_complexity("How many teams?") == 3
