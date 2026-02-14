"""
FILE: security.py
STATUS: Active
RESPONSIBILITY: Input sanitization and SSRF protection utilities
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

import html
import re
from typing import Any

from src.core.config import settings
from src.core.exceptions import ValidationError


# Patterns for dangerous content
DANGEROUS_PATTERNS = [
    r"<script[^>]*>.*?</script>",  # Script tags
    r"javascript:",  # JavaScript protocol
    r"on\w+\s*=",  # Event handlers
    r"\{\{.*?\}\}",  # Template injection
    r"\$\{.*?\}",  # Template literals
    r"eval\s*\(",  # Eval calls
    r"exec\s*\(",  # Exec calls
]

# Compile patterns for efficiency
DANGEROUS_REGEX = re.compile("|".join(DANGEROUS_PATTERNS), re.IGNORECASE | re.DOTALL)


def sanitize_query(query: str) -> str:
    """Sanitize user query to prevent injection attacks.

    Args:
        query: Raw user input

    Returns:
        Sanitized query string

    Raises:
        ValidationError: If query is empty or too long
    """
    if not query:
        raise ValidationError("Query cannot be empty")

    # Strip whitespace
    query = query.strip()

    if not query:
        raise ValidationError("Query cannot be empty or whitespace only")

    if len(query) > settings.max_query_length:
        raise ValidationError(
            f"Query exceeds maximum length of {settings.max_query_length} characters",
            details={"length": len(query), "max_length": settings.max_query_length},
        )

    # Remove dangerous patterns
    query = DANGEROUS_REGEX.sub("", query)

    # Escape HTML entities
    query = html.escape(query)

    return query


def validate_search_params(k: int | None = None, min_score: float | None = None) -> None:
    """Validate search parameters.

    Args:
        k: Number of results to return
        min_score: Minimum similarity score

    Raises:
        ValidationError: If parameters are invalid
    """
    if k is not None:
        if k < 1:
            raise ValidationError("k must be at least 1", details={"k": k})
        if k > 50:
            raise ValidationError("k cannot exceed 50", details={"k": k})

    if min_score is not None:
        if min_score < 0 or min_score > 1:
            raise ValidationError(
                "min_score must be between 0 and 1",
                details={"min_score": min_score},
            )


def sanitize_path(path: str) -> str:
    """Sanitize file path to prevent path traversal.

    Args:
        path: Input path

    Returns:
        Sanitized path

    Raises:
        ValidationError: If path contains traversal attempts
    """
    # Check for path traversal patterns
    if ".." in path or path.startswith("/") or path.startswith("\\"):
        raise ValidationError(
            "Invalid path: path traversal not allowed",
            details={"path": path},
        )

    # Remove any null bytes
    path = path.replace("\x00", "")

    return path


def mask_sensitive_data(data: dict[str, Any], keys_to_mask: set[str] | None = None) -> dict:
    """Mask sensitive data in dictionaries for logging.

    Args:
        data: Dictionary potentially containing sensitive data
        keys_to_mask: Set of keys to mask (default: common sensitive keys)

    Returns:
        Dictionary with sensitive values masked
    """
    if keys_to_mask is None:
        keys_to_mask = {"api_key", "password", "secret", "token", "key", "auth"}

    masked = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in keys_to_mask):
            masked[key] = "***MASKED***"
        elif isinstance(value, dict):
            masked[key] = mask_sensitive_data(value, keys_to_mask)
        else:
            masked[key] = value

    return masked


def validate_url(url: str) -> str:
    """Validate and sanitize URL for external requests.

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        ValidationError: If URL is invalid or potentially dangerous
    """
    if not url:
        raise ValidationError("URL cannot be empty")

    # Must start with http:// or https://
    if not url.startswith(("http://", "https://")):
        raise ValidationError(
            "URL must use http:// or https:// protocol",
            details={"url": url},
        )

    # Block private/internal IPs (basic SSRF protection)
    private_patterns = [
        r"https?://localhost",
        r"https?://127\.",
        r"https?://10\.",
        r"https?://172\.(1[6-9]|2[0-9]|3[0-1])\.",
        r"https?://192\.168\.",
        r"https?://0\.",
        r"https?://\[::1\]",
    ]

    for pattern in private_patterns:
        if re.match(pattern, url, re.IGNORECASE):
            raise ValidationError(
                "URLs pointing to private/internal addresses are not allowed",
                details={"url": url},
            )

    return url
