"""
FILE: exceptions.py
STATUS: Active
RESPONSIBILITY: Custom exception hierarchy for structured error handling
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

from typing import Any


class AppException(Exception):
    """Base exception for all application errors.

    Attributes:
        message: Human-readable error message
        code: Machine-readable error code
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class ConfigurationError(AppException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, code="CONFIG_ERROR", details=details)


class ValidationError(AppException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class EmbeddingError(AppException):
    """Raised when embedding generation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, code="EMBEDDING_ERROR", details=details)


class SearchError(AppException):
    """Raised when vector search fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, code="SEARCH_ERROR", details=details)


class LLMError(AppException):
    """Raised when LLM API call fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, code="LLM_ERROR", details=details)


class DocumentError(AppException):
    """Raised when document processing fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, code="DOCUMENT_ERROR", details=details)


class RateLimitError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            message,
            code="RATE_LIMIT_ERROR",
            details={"retry_after": retry_after},
        )
        self.retry_after = retry_after


class IndexNotFoundError(AppException):
    """Raised when vector index is not found or not loaded."""

    def __init__(self, message: str = "Vector index not found. Run indexer first."):
        super().__init__(message, code="INDEX_NOT_FOUND")
