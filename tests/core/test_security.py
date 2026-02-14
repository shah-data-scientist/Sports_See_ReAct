"""
FILE: test_security.py
STATUS: Active
RESPONSIBILITY: Tests for input sanitization and security utilities
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

import pytest

from src.core.exceptions import ValidationError
from src.core.security import (
    mask_sensitive_data,
    sanitize_path,
    sanitize_query,
    validate_search_params,
    validate_url,
)


class TestSanitizeQuery:
    """Tests for query sanitization."""

    def test_valid_query(self):
        """Test that valid queries pass through."""
        query = "Who won the NBA championship?"
        result = sanitize_query(query)
        assert result == query

    def test_strips_whitespace(self):
        """Test that whitespace is stripped."""
        query = "  test query  "
        result = sanitize_query(query)
        assert result == "test query"

    def test_empty_query_raises(self):
        """Test that empty query raises ValidationError."""
        with pytest.raises(ValidationError):
            sanitize_query("")

    def test_whitespace_only_raises(self):
        """Test that whitespace-only query raises ValidationError."""
        with pytest.raises(ValidationError):
            sanitize_query("   ")

    def test_long_query_raises(self):
        """Test that too-long query raises ValidationError."""
        long_query = "x" * 5000
        with pytest.raises(ValidationError) as exc_info:
            sanitize_query(long_query)
        assert "exceeds maximum length" in str(exc_info.value)

    def test_removes_script_tags(self):
        """Test that script tags are removed."""
        query = "test <script>alert('xss')</script> query"
        result = sanitize_query(query)
        assert "<script>" not in result.lower()

    def test_escapes_html(self):
        """Test that HTML is escaped."""
        query = "test <b>bold</b>"
        result = sanitize_query(query)
        assert "&lt;b&gt;" in result


class TestValidateSearchParams:
    """Tests for search parameter validation."""

    def test_valid_params(self):
        """Test that valid params pass."""
        validate_search_params(k=5, min_score=0.5)

    def test_k_too_low_raises(self):
        """Test that k < 1 raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_search_params(k=0)

    def test_k_too_high_raises(self):
        """Test that k > 50 raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_search_params(k=100)

    def test_min_score_out_of_range_raises(self):
        """Test that min_score outside 0-1 raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_search_params(min_score=1.5)

        with pytest.raises(ValidationError):
            validate_search_params(min_score=-0.1)


class TestSanitizePath:
    """Tests for path sanitization."""

    def test_valid_path(self):
        """Test that valid paths pass through."""
        path = "documents/file.pdf"
        result = sanitize_path(path)
        assert result == path

    def test_path_traversal_raises(self):
        """Test that path traversal is blocked."""
        with pytest.raises(ValidationError):
            sanitize_path("../secret/file.txt")

    def test_absolute_path_raises(self):
        """Test that absolute paths are blocked."""
        with pytest.raises(ValidationError):
            sanitize_path("/etc/passwd")


class TestValidateUrl:
    """Tests for URL validation."""

    def test_valid_https_url(self):
        """Test that valid HTTPS URLs pass."""
        url = "https://example.com/file.zip"
        result = validate_url(url)
        assert result == url

    def test_valid_http_url(self):
        """Test that valid HTTP URLs pass."""
        url = "http://example.com/file.zip"
        result = validate_url(url)
        assert result == url

    def test_empty_url_raises(self):
        """Test that empty URL raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_url("")

    def test_invalid_protocol_raises(self):
        """Test that non-HTTP protocols raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_url("ftp://example.com")

    def test_localhost_blocked(self):
        """Test that localhost is blocked (SSRF protection)."""
        with pytest.raises(ValidationError):
            validate_url("http://localhost:8080")

    def test_private_ip_blocked(self):
        """Test that private IPs are blocked (SSRF protection)."""
        with pytest.raises(ValidationError):
            validate_url("http://192.168.1.1")

        with pytest.raises(ValidationError):
            validate_url("http://10.0.0.1")


class TestMaskSensitiveData:
    """Tests for sensitive data masking."""

    def test_masks_api_key(self):
        """Test that API keys are masked."""
        data = {"api_key": "secret123", "name": "test"}
        result = mask_sensitive_data(data)
        assert result["api_key"] == "***MASKED***"
        assert result["name"] == "test"

    def test_masks_nested_data(self):
        """Test that nested sensitive data is masked."""
        data = {"config": {"password": "secret"}}
        result = mask_sensitive_data(data)
        assert result["config"]["password"] == "***MASKED***"

    def test_custom_keys(self):
        """Test custom keys to mask."""
        data = {"custom_field": "value"}
        result = mask_sensitive_data(data, keys_to_mask={"custom"})
        assert result["custom_field"] == "***MASKED***"
