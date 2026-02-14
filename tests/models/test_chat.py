"""
FILE: test_chat.py
STATUS: Active
RESPONSIBILITY: Tests for chat model validation (ChatMessage, ChatRequest, SearchResult, ChatResponse, generated_sql field)
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models.chat import ChatMessage, ChatRequest, ChatResponse, SearchResult


class TestChatMessage:
    """Tests for ChatMessage model."""

    def test_valid_user_message(self):
        """Test creating a valid user message."""
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp is not None

    def test_valid_assistant_message(self):
        """Test creating a valid assistant message."""
        msg = ChatMessage(role="assistant", content="Hi there!")
        assert msg.role == "assistant"

    def test_invalid_role_raises(self):
        """Test that invalid role raises ValidationError."""
        with pytest.raises(ValidationError):
            ChatMessage(role="system", content="test")

    def test_empty_content_raises(self):
        """Test that empty content raises ValidationError."""
        with pytest.raises(ValidationError):
            ChatMessage(role="user", content="")

    def test_content_stripped(self):
        """Test that content is stripped."""
        msg = ChatMessage(role="user", content="  test  ")
        assert msg.content == "test"


class TestChatRequest:
    """Tests for ChatRequest model."""

    def test_valid_request(self):
        """Test creating a valid request."""
        req = ChatRequest(query="Who won?")
        assert req.query == "Who won?"
        assert req.k == 5  # default
        assert req.include_sources is True  # default

    def test_custom_params(self):
        """Test request with custom parameters."""
        req = ChatRequest(query="Test", k=10, min_score=0.5, include_sources=False)
        assert req.k == 10
        assert req.min_score == 0.5
        assert req.include_sources is False

    def test_empty_query_raises(self):
        """Test that empty query raises ValidationError."""
        with pytest.raises(ValidationError):
            ChatRequest(query="")

    def test_k_out_of_range_raises(self):
        """Test that k outside valid range raises ValidationError."""
        with pytest.raises(ValidationError):
            ChatRequest(query="test", k=0)

        with pytest.raises(ValidationError):
            ChatRequest(query="test", k=100)

    def test_min_score_out_of_range_raises(self):
        """Test that min_score outside 0-1 raises ValidationError."""
        with pytest.raises(ValidationError):
            ChatRequest(query="test", min_score=1.5)


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_valid_result(self):
        """Test creating a valid search result."""
        result = SearchResult(
            text="Document content",
            score=85.5,
            source="doc.pdf",
        )
        assert result.text == "Document content"
        assert result.score == 85.5
        assert result.source == "doc.pdf"

    def test_score_bounds(self):
        """Test that score must be 0-100."""
        with pytest.raises(ValidationError):
            SearchResult(text="test", score=150, source="doc")

        with pytest.raises(ValidationError):
            SearchResult(text="test", score=-10, source="doc")

    def test_metadata_optional(self):
        """Test that metadata is optional."""
        result = SearchResult(text="test", score=50, source="doc")
        assert result.metadata == {}


class TestChatResponse:
    """Tests for ChatResponse model."""

    def test_valid_response(self):
        """Test creating a valid response."""
        resp = ChatResponse(
            answer="The answer is 42",
            query="What is the answer?",
            processing_time_ms=150.5,
            model="mistral-small",
        )
        assert resp.answer == "The answer is 42"
        assert resp.processing_time_ms == 150.5

    def test_sources_default_empty(self):
        """Test that sources default to empty list."""
        resp = ChatResponse(
            answer="test",
            query="test",
            processing_time_ms=100,
            model="test",
        )
        assert resp.sources == []

    def test_chat_response_with_generated_sql(self):
        """Test ChatResponse can include generated_sql field."""
        response = ChatResponse(
            answer="Test answer",
            sources=[],
            query="Test query",
            processing_time_ms=100.0,
            model="test-model",
            timestamp=datetime.utcnow(),
            generated_sql="SELECT * FROM test"
        )
        assert response.generated_sql == "SELECT * FROM test"

    def test_chat_response_without_generated_sql(self):
        """Test ChatResponse works with generated_sql=None."""
        response = ChatResponse(
            answer="Test answer",
            sources=[],
            query="Test query",
            processing_time_ms=100.0,
            model="test-model",
            timestamp=datetime.utcnow(),
            generated_sql=None
        )
        assert response.generated_sql is None

    def test_chat_response_default_generated_sql(self):
        """Test ChatResponse defaults to None for generated_sql."""
        response = ChatResponse(
            answer="Test answer",
            sources=[],
            query="Test query",
            processing_time_ms=100.0,
            model="test-model",
            timestamp=datetime.utcnow()
        )
        assert response.generated_sql is None

    def test_chat_response_serialization_with_sql(self):
        """Test ChatResponse serializes correctly with generated_sql."""
        response = ChatResponse(
            answer="Test answer",
            sources=[],
            query="Test query",
            processing_time_ms=100.0,
            model="test-model",
            timestamp=datetime.utcnow(),
            generated_sql="SELECT name FROM players LIMIT 1"
        )
        # Serialize to dict
        response_dict = response.model_dump()
        assert "generated_sql" in response_dict
        assert response_dict["generated_sql"] == "SELECT name FROM players LIMIT 1"

    def test_chat_response_deserialization_with_sql(self):
        """Test ChatResponse deserializes correctly with generated_sql."""
        data = {
            "answer": "Test answer",
            "sources": [],
            "query": "Test query",
            "processing_time_ms": 100.0,
            "model": "test-model",
            "timestamp": datetime.utcnow().isoformat(),
            "generated_sql": "SELECT * FROM player_stats"
        }
        response = ChatResponse.model_validate(data)
        assert response.generated_sql == "SELECT * FROM player_stats"

    def test_chat_response_with_sources_and_sql(self):
        """Test ChatResponse can have both sources and generated_sql."""
        response = ChatResponse(
            answer="Test answer",
            sources=[
                SearchResult(
                    text="Test text",
                    score=85.0,
                    source="test.pdf",
                    metadata={}
                )
            ],
            query="Test query",
            processing_time_ms=100.0,
            model="test-model",
            timestamp=datetime.utcnow(),
            generated_sql="SELECT name FROM players"
        )
        assert len(response.sources) == 1
        assert response.generated_sql == "SELECT name FROM players"

    def test_chat_response_sql_optional_field(self):
        """Test that generated_sql is truly optional."""
        response = ChatResponse(
            answer="Answer",
            sources=[],
            query="Query",
            processing_time_ms=50.0,
            model="model"
        )
        assert hasattr(response, 'generated_sql')
        assert response.generated_sql is None
