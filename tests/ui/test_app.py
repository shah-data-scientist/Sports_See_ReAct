"""
FILE: test_app.py
STATUS: Active
RESPONSIBILITY: Smoke tests for Streamlit chat interface with mocked services
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

from unittest.mock import MagicMock, patch

import pytest


class TestAppImports:
    @patch("streamlit.set_page_config")
    @patch("streamlit.cache_resource", lambda f: f)
    def test_render_sources_empty(self, mock_config):
        with patch("src.ui.app.st") as mock_st:
            from src.ui.app import render_sources

            render_sources([])
            mock_st.expander.assert_not_called()

    @patch("streamlit.set_page_config")
    @patch("streamlit.cache_resource", lambda f: f)
    def test_render_sources_with_items(self, mock_config):
        with patch("src.ui.app.st") as mock_st:
            from src.ui.app import render_sources

            source = MagicMock()
            source.source = "test.pdf"
            source.score = 85.0
            source.text = "Short text"

            # Default compact=True uses st.caption, not st.expander
            render_sources([source])
            mock_st.caption.assert_called_once()


class TestRenderMessage:
    @patch("streamlit.set_page_config")
    @patch("streamlit.cache_resource", lambda f: f)
    def test_render_message_calls_st(self, mock_config):
        with patch("src.ui.app.st") as mock_st:
            mock_chat_msg = MagicMock()
            mock_st.chat_message.return_value.__enter__ = MagicMock(return_value=mock_chat_msg)
            mock_st.chat_message.return_value.__exit__ = MagicMock(return_value=False)

            from src.ui.app import render_message

            render_message("user", "Hello!")
            mock_st.chat_message.assert_called_once_with("user")


class TestCachingFunctions:
    """Test Streamlit caching functions with underscore parameters.

    These tests ensure that non-serializable objects (like APIClient)
    don't cause Streamlit caching hash errors at runtime.
    """

    @patch("streamlit.set_page_config")
    @patch("streamlit.cache_data", lambda **kwargs: lambda f: f)
    def test_cached_feedback_stats_with_mock_client(self, mock_config):
        """Test that get_cached_feedback_stats works with underscore parameter."""
        from src.ui.app import get_cached_feedback_stats
        from src.ui.api_client import APIClient

        mock_client = MagicMock(spec=APIClient)
        mock_client.get_feedback_stats.return_value = {
            "total_interactions": 42,
            "avg_rating": 4.5,
        }

        result = get_cached_feedback_stats(mock_client)

        assert result == {"total_interactions": 42, "avg_rating": 4.5}
        mock_client.get_feedback_stats.assert_called_once()

    @patch("streamlit.set_page_config")
    @patch("streamlit.cache_data", lambda **kwargs: lambda f: f)
    def test_cached_health_status_with_mock_client(self, mock_config):
        """Test that get_cached_health_status works with underscore parameter."""
        from src.ui.app import get_cached_health_status
        from src.ui.api_client import APIClient

        mock_client = MagicMock(spec=APIClient)
        mock_client.health_check.return_value = {"status": "healthy", "uptime": 3600}

        result = get_cached_health_status(mock_client)

        assert result == {"status": "healthy", "uptime": 3600}
        mock_client.health_check.assert_called_once()


class TestRenderSourcesCompact:
    """Tests for render_sources() compact and detailed modes."""

    @patch("streamlit.set_page_config")
    @patch("streamlit.cache_resource", lambda f: f)
    def test_compact_mode_deduplicates(self, mock_config):
        with patch("src.ui.app.st") as mock_st:
            from src.ui.app import render_sources

            source1 = MagicMock()
            source1.source = "nba_stats.pdf"
            source1.score = 90.0
            source1.text = "Text 1"

            source2 = MagicMock()
            source2.source = "nba_stats.pdf"
            source2.score = 85.0
            source2.text = "Text 2"

            render_sources([source1, source2], compact=True)

            # Should deduplicate — only 1 source name in caption
            call_args = mock_st.caption.call_args[0][0]
            assert call_args.count("nba stats") == 1

    @patch("streamlit.set_page_config")
    @patch("streamlit.cache_resource", lambda f: f)
    def test_detailed_mode_uses_expander(self, mock_config):
        with patch("src.ui.app.st") as mock_st:
            from src.ui.app import render_sources

            mock_expander = MagicMock()
            mock_st.expander.return_value.__enter__ = MagicMock(return_value=mock_expander)
            mock_st.expander.return_value.__exit__ = MagicMock(return_value=False)

            source = MagicMock()
            source.source = "players.pdf"
            source.score = 80.0
            source.text = "Player info"

            render_sources([source], compact=False)
            mock_st.expander.assert_called_once()
