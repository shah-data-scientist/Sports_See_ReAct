"""
FILE: test_exceptions.py
STATUS: Active
RESPONSIBILITY: Unit tests for custom exception hierarchy
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import pytest

from src.core.exceptions import (
    AppException,
    ConfigurationError,
    DocumentError,
    EmbeddingError,
    IndexNotFoundError,
    LLMError,
    RateLimitError,
    SearchError,
    ValidationError,
)


class TestAppException:
    def test_default_code(self):
        exc = AppException("something went wrong")
        assert exc.message == "something went wrong"
        assert exc.code == "APP_ERROR"
        assert exc.details == {}

    def test_custom_code_and_details(self):
        exc = AppException("bad", code="CUSTOM", details={"key": "val"})
        assert exc.code == "CUSTOM"
        assert exc.details == {"key": "val"}

    def test_to_dict(self):
        exc = AppException("msg", code="CODE", details={"x": 1})
        d = exc.to_dict()
        assert d == {"error": {"code": "CODE", "message": "msg", "details": {"x": 1}}}

    def test_inherits_from_exception(self):
        exc = AppException("test")
        assert isinstance(exc, Exception)
        assert str(exc) == "test"


class TestSubclassExceptions:
    def test_configuration_error(self):
        exc = ConfigurationError("missing key")
        assert exc.code == "CONFIG_ERROR"
        assert isinstance(exc, AppException)

    def test_validation_error(self):
        exc = ValidationError("bad input", details={"field": "name"})
        assert exc.code == "VALIDATION_ERROR"
        assert exc.details == {"field": "name"}

    def test_embedding_error(self):
        exc = EmbeddingError("embed failed")
        assert exc.code == "EMBEDDING_ERROR"

    def test_search_error(self):
        exc = SearchError("search failed")
        assert exc.code == "SEARCH_ERROR"

    def test_llm_error(self):
        exc = LLMError("llm failed")
        assert exc.code == "LLM_ERROR"

    def test_document_error(self):
        exc = DocumentError("doc error")
        assert exc.code == "DOCUMENT_ERROR"


class TestRateLimitError:
    def test_default_message_and_retry(self):
        exc = RateLimitError()
        assert exc.message == "Rate limit exceeded"
        assert exc.retry_after == 60
        assert exc.code == "RATE_LIMIT_ERROR"
        assert exc.details == {"retry_after": 60}

    def test_custom_retry_after(self):
        exc = RateLimitError(message="slow down", retry_after=120)
        assert exc.retry_after == 120
        assert exc.details == {"retry_after": 120}


class TestIndexNotFoundError:
    def test_default_message(self):
        exc = IndexNotFoundError()
        assert "Vector index not found" in exc.message
        assert exc.code == "INDEX_NOT_FOUND"

    def test_custom_message(self):
        exc = IndexNotFoundError("custom msg")
        assert exc.message == "custom msg"
