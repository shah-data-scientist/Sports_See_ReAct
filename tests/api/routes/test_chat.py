"""
FILE: test_chat.py
STATUS: Active
RESPONSIBILITY: Tests for chat API routes (POST /chat, GET /search)
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes.chat import router
from src.models.chat import ChatResponse, SearchResult


@pytest.fixture
def app():
    """Create FastAPI app with chat router for testing."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_service():
    """Create a mock ChatService with default return values."""
    service = MagicMock()
    service.chat.return_value = ChatResponse(
        answer="The Denver Nuggets won.",
        sources=[
            SearchResult(text="Nuggets defeated Heat", score=92.5, source="nba.pdf")
        ],
        query="Who won the NBA?",
        processing_time_ms=150.0,
        model="test-model",
    )
    service.search.return_value = [
        SearchResult(text="Relevant chunk", score=85.0, source="doc.pdf")
    ]
    return service


class TestChatEndpoint:
    """Tests for POST /chat endpoint."""

    def test_chat_returns_chat_response(self, client, mock_service):
        """POST /chat with valid request returns ChatResponse."""
        with patch("src.api.routes.chat.get_chat_service", return_value=mock_service):
            response = client.post("/chat", json={"query": "Who won the NBA?"})

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert data["query"] == "Who won the NBA?"
        mock_service.chat.assert_called_once()

    def test_chat_empty_query_rejected(self, client, mock_service):
        """POST /chat with empty query returns 422 validation error."""
        with patch("src.api.routes.chat.get_chat_service", return_value=mock_service):
            response = client.post("/chat", json={"query": ""})

        assert response.status_code == 422

    def test_chat_whitespace_only_query_rejected(self, client, mock_service):
        """POST /chat with whitespace-only query returns 422."""
        with patch("src.api.routes.chat.get_chat_service", return_value=mock_service):
            response = client.post("/chat", json={"query": "   "})

        assert response.status_code == 422


class TestSearchEndpoint:
    """Tests for GET /search endpoint."""

    def test_search_returns_list_of_results(self, client, mock_service):
        """GET /search with valid query returns list of SearchResult."""
        with patch("src.api.routes.chat.get_chat_service", return_value=mock_service):
            response = client.get("/search", params={"query": "NBA championship"})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["source"] == "doc.pdf"
        mock_service.search.assert_called_once()

    def test_search_custom_k_parameter(self, client, mock_service):
        """GET /search respects custom k parameter."""
        with patch("src.api.routes.chat.get_chat_service", return_value=mock_service):
            response = client.get("/search", params={"query": "test", "k": 10})

        assert response.status_code == 200
        mock_service.search.assert_called_once_with(query="test", k=10, min_score=None)


