"""
FILE: test_api_client.py
STATUS: Active
RESPONSIBILITY: Unit tests for APIClient HTTP client using mocks
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

import pytest
from unittest.mock import MagicMock, patch
from src.ui.api_client import APIClient, ChatRequest


class TestChatRequest:
    """Tests for ChatRequest dataclass."""

    def test_chat_request_default_values(self):
        """Test ChatRequest instantiation with default values."""
        request = ChatRequest(query="What is the top scorer?")

        assert request.query == "What is the top scorer?"
        assert request.k == 5
        assert request.include_sources is True
        assert request.conversation_id is None
        assert request.turn_number is None

    def test_chat_request_custom_values(self):
        """Test ChatRequest with custom parameter values."""
        request = ChatRequest(
            query="Who is LeBron?",
            k=10,
            include_sources=False,
            conversation_id="conv_123",
            turn_number=5,
        )

        assert request.query == "Who is LeBron?"
        assert request.k == 10
        assert request.include_sources is False
        assert request.conversation_id == "conv_123"
        assert request.turn_number == 5


class TestAPIClient:
    """Tests for APIClient HTTP client."""

    def test_init_default_base_url(self):
        """Test APIClient initialization with default base URL."""
        client = APIClient()

        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 60

    def test_init_custom_base_url(self):
        """Test APIClient initialization with custom base URL."""
        client = APIClient(base_url="http://api.example.com:9000")

        assert client.base_url == "http://api.example.com:9000"
        assert client.timeout == 60

    @patch("src.ui.api_client.requests.request")
    def test_health_check_success(self, mock_request):
        """Test health_check() with mocked successful response."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "healthy",
            "index_loaded": True,
            "total_chunks": 42,
        }
        mock_request.return_value = mock_response

        client = APIClient()

        # Act
        result = client.health_check()

        # Assert
        assert result["status"] == "healthy"
        assert result["index_loaded"] is True
        assert result["total_chunks"] == 42
        mock_request.assert_called_once_with(
            "GET",
            "http://localhost:8000/health",
            timeout=60,
        )

    @patch("src.ui.api_client.requests.request")
    def test_chat_success(self, mock_request):
        """Test chat() with mocked successful response."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "LeBron James is a professional basketball player.",
            "sources": ["nba_overview.pdf", "players_bio.txt"],
            "query_type": "contextual",
        }
        mock_request.return_value = mock_response

        client = APIClient()
        request = ChatRequest(query="Who is LeBron?", k=5)

        # Act
        result = client.chat(request)

        # Assert
        assert result["answer"] == "LeBron James is a professional basketball player."
        assert len(result["sources"]) == 2
        assert result["query_type"] == "contextual"
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "http://localhost:8000/api/v1/chat"
