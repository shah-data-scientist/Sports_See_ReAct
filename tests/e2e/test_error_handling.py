"""
FILE: test_error_handling.py
STATUS: Active
RESPONSIBILITY: E2E tests for error handling and graceful degradation in Streamlit UI
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

import pytest
from playwright.sync_api import Page


@pytest.mark.error_handling
class TestHealthStatus:
    """Test API health status display in UI."""

    def test_api_health_status_displayed(self, streamlit_page: Page):
        """Test that API health status is shown in sidebar when API is running."""
        content = streamlit_page.content()
        # When API is running, should show "API Ready" in sidebar
        assert "API Ready" in content or "✅" in content, (
            "API health status not displayed in sidebar"
        )

    def test_api_connection_indicator(self, streamlit_page: Page):
        """Test that the page shows API connection status."""
        # Wait for full page render including footer
        streamlit_page.wait_for_timeout(5000)
        content = streamlit_page.content()
        # Check for either footer text or sidebar health status
        assert "Connected to API" in content or "API Ready" in content, (
            "API connection indicator not found on page"
        )


@pytest.mark.error_handling
class TestNoRawErrors:
    """Test that raw error codes/exceptions never leak to the UI."""

    def test_no_raw_error_codes_on_healthy_page(self, streamlit_page: Page):
        """Test that no raw HTTP error codes appear on a healthy page."""
        streamlit_page.wait_for_timeout(2000)

        content = streamlit_page.content()
        # Raw error codes should never appear on a healthy page
        assert "422" not in content, "Raw HTTP 422 error visible on healthy page"
        assert "500 Internal" not in content, "Raw HTTP 500 error visible"
        assert "Traceback" not in content, "Python traceback visible to user"
        assert "TypeError" not in content, "TypeError visible to user"

    def test_no_raw_errors_after_query(self, streamlit_page: Page, send_query):
        """Test that no raw error codes appear after a successful query."""
        assert send_query("What is basketball?"), "Query timed out"
        streamlit_page.wait_for_timeout(2000)

        content = streamlit_page.content()
        assert "422" not in content, "Raw 422 error after query"
        assert "Traceback" not in content, "Traceback visible after query"
        assert "[Errno" not in content, "System error visible after query"

    def test_no_exceptions_on_page(self, streamlit_page: Page):
        """Test that no Streamlit exception boxes appear on healthy page."""
        exception_boxes = streamlit_page.locator("[data-testid='stException']")
        assert exception_boxes.count() == 0, (
            f"Found {exception_boxes.count()} exception box(es) on the page"
        )


@pytest.mark.error_handling
class TestErrorMessageFormat:
    """Test that error messages are user-friendly with guidance."""

    def test_error_messages_use_emojis(self, streamlit_page: Page, send_query):
        """Test that any visible error messages contain user-friendly emojis."""
        assert send_query("Test query for error check"), "Query timed out"
        streamlit_page.wait_for_timeout(2000)

        # If any error-like content exists, it should have user-friendly format
        error_elements = streamlit_page.locator("[data-testid='stAlert']")
        for i in range(error_elements.count()):
            error_text = error_elements.nth(i).text_content()
            if error_text:
                # Error messages should contain guidance emoji
                has_emoji = any(e in error_text for e in ["⚠️", "❌", "⏱️", "✅"])
                assert has_emoji, (
                    f"Error message without user-friendly emoji: {error_text[:100]}"
                )


@pytest.mark.error_handling
class TestGracefulRecovery:
    """Test that the UI recovers gracefully from various scenarios."""

    def test_page_responsive_after_query(self, streamlit_page: Page, send_query):
        """Test that page remains interactive after a query."""
        assert send_query("Simple test query"), "Query timed out"
        streamlit_page.wait_for_timeout(2000)

        # Page should still be responsive
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        assert chat_input.is_visible(), "Chat input not visible after query"
        assert chat_input.is_enabled(), "Chat input not enabled after query"

    def test_recovery_after_multiple_queries(self, streamlit_page: Page, send_query):
        """Test that user can send queries after previous queries complete."""
        # First query
        assert send_query("First query"), "First query timed out"
        streamlit_page.wait_for_timeout(2000)

        # Second query should also work
        assert send_query("Second query after first"), "Second query timed out"

        # Page should still be interactive
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        assert chat_input.is_visible(), "Chat input not responsive after multiple queries"

    def test_rapid_queries_dont_crash_ui(self, streamlit_page: Page):
        """Test that rapid query submission doesn't crash the UI."""
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")

        # Send queries rapidly without waiting for responses
        for i in range(3):
            chat_input.fill(f"Rapid query {i + 1}")
            chat_input.press("Enter")
            streamlit_page.wait_for_timeout(1000)

        # Wait for processing to settle
        streamlit_page.wait_for_timeout(10000)

        # Page should still be functional
        assert chat_input.is_visible(), "Chat input disappeared after rapid queries"

    def test_graceful_timeout_handling(self, streamlit_page: Page, send_query):
        """Test that page handles slow responses without crashing."""
        # Send query and wait
        send_query("Complex question about NBA statistics and history", timeout_ms=30000)

        # Regardless of timeout, page should remain functional
        streamlit_page.wait_for_timeout(2000)
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        assert chat_input.is_visible(), "Chat input not visible after slow query"
