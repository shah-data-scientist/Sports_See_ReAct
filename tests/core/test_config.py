"""
FILE: test_config.py
STATUS: Active
RESPONSIBILITY: Tests for configuration module validation and defaults
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError


class TestSettings:
    """Tests for Settings configuration."""

    def test_settings_loads(self):
        """Test that settings can be loaded."""
        from src.core.config import settings

        assert settings is not None
        assert hasattr(settings, "mistral_api_key")

    def test_settings_has_required_attributes(self):
        """Test that settings has all required attributes."""
        from src.core.config import settings

        # Check core settings exist
        assert hasattr(settings, "chunk_size")
        assert hasattr(settings, "chunk_overlap")
        assert hasattr(settings, "search_k")
        assert hasattr(settings, "embedding_model")
        assert hasattr(settings, "chat_model")

    def test_chunk_size_valid(self):
        """Test that chunk size is within valid range."""
        from src.core.config import settings

        assert 100 <= settings.chunk_size <= 10000

    def test_chunk_overlap_less_than_size(self):
        """Test that chunk overlap is less than chunk size."""
        from src.core.config import settings

        assert settings.chunk_overlap < settings.chunk_size

    def test_search_k_valid(self):
        """Test that search_k is within valid range."""
        from src.core.config import settings

        assert 1 <= settings.search_k <= 50

    def test_paths_are_path_objects(self):
        """Test that path properties return Path objects."""
        from pathlib import Path

        from src.core.config import settings

        assert isinstance(settings.faiss_index_path, Path)
        assert isinstance(settings.document_chunks_path, Path)
        assert isinstance(settings.database_path, Path)

    def test_faiss_index_path_correct(self):
        """Test FAISS index path is constructed correctly."""
        from src.core.config import settings

        expected_name = "faiss_index.idx"
        assert settings.faiss_index_path.name == expected_name

    def test_temperature_valid_range(self):
        """Test that temperature is within valid range."""
        from src.core.config import settings

        assert 0.0 <= settings.temperature <= 2.0

    @patch.dict(os.environ, {"MISTRAL_API_KEY": "test_key_12345"}, clear=False)
    def test_api_key_from_env(self):
        """Test that API key can be loaded from environment."""
        from src.core.config import Settings

        # Create new settings instance to pick up env var
        test_settings = Settings()
        assert test_settings.mistral_api_key == "test_key_12345"

    def test_settings_validation_chunk_overlap(self):
        """Test that chunk_overlap validation works."""
        from src.core.config import Settings

        # Overlap greater than chunk_size should fail
        with pytest.raises(ValidationError):
            Settings(
                mistral_api_key="test_key_123",
                chunk_size=1000,
                chunk_overlap=1500,  # Invalid: overlap > size
            )

    def test_settings_default_values(self):
        """Test that default values are set correctly."""
        from src.core.config import settings

        # These should have sensible defaults
        assert settings.embedding_model == "mistral-embed"
        # Defaults are data/inputs and data/vector, but .env may override
        assert "inputs" in settings.input_dir
        assert "vector" in settings.vector_db_dir
        assert settings.app_title == "NBA Analyst AI"

    def test_api_port_valid_range(self):
        """Test that API port is within valid range."""
        from src.core.config import settings

        assert 1 <= settings.api_port <= 65535

    def test_log_level_valid(self):
        """Test that log level is one of the allowed values."""
        from src.core.config import settings

        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}
        assert settings.log_level in valid_levels

    def test_max_query_length_reasonable(self):
        """Test that max query length is reasonable."""
        from src.core.config import settings

        assert 10 <= settings.max_query_length <= 10000


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings(self):
        """Test that get_settings returns a Settings instance."""
        from src.core.config import Settings, get_settings

        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_cached(self):
        """Test that get_settings returns cached instance."""
        from src.core.config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
