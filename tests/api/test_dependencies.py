"""
FILE: test_dependencies.py
STATUS: Active
RESPONSIBILITY: Unit tests for API dependency injection functions
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

from unittest.mock import MagicMock

import pytest

from src.api.dependencies import get_chat_service, set_chat_service


class TestSetChatService:
    def test_set_service_with_valid_instance(self):
        mock_service = MagicMock()
        set_chat_service(mock_service)
        result = get_chat_service()
        assert result is mock_service
        # Cleanup
        set_chat_service(None)

    def test_set_service_to_none_clears_service(self):
        mock_service = MagicMock()
        set_chat_service(mock_service)
        set_chat_service(None)
        with pytest.raises(RuntimeError, match="Chat service not initialized"):
            get_chat_service()


class TestGetChatService:
    def test_raises_runtime_error_when_not_initialized(self):
        set_chat_service(None)
        with pytest.raises(RuntimeError, match="Chat service not initialized"):
            get_chat_service()

    def test_returns_service_when_initialized(self):
        mock_service = MagicMock()
        set_chat_service(mock_service)
        result = get_chat_service()
        assert result is mock_service
        # Cleanup
        set_chat_service(None)

    def test_returns_same_instance_on_multiple_calls(self):
        mock_service = MagicMock()
        set_chat_service(mock_service)
        result1 = get_chat_service()
        result2 = get_chat_service()
        assert result1 is result2
        # Cleanup
        set_chat_service(None)
