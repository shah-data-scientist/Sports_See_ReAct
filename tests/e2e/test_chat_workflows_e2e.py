"""
FILE: test_chat_workflows_e2e.py
STATUS: Active
RESPONSIBILITY: E2E tests for chat workflow scenarios (sequential queries, history, stats)
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

import pytest
from playwright.sync_api import Page


@pytest.mark.chat_workflow
class TestMultipleSequentialQueries:
    """Test sending multiple queries in one session."""

    def test_two_sequential_queries(self, streamlit_page: Page, send_query):
        """Test sending two queries in sequence, both producing page responses."""
        # First query
        assert send_query("How many teams are in the NBA?"), "First query timed out"
        streamlit_page.wait_for_timeout(2000)

        # Second query (may hit rate limit — still should produce a page response)
        result = send_query("Who is the tallest NBA player?")

        # At minimum, the first query + user messages should be in history
        messages = streamlit_page.locator("[data-testid='stChatMessage']")
        assert messages.count() >= 2, (
            f"Expected at least 2 messages, got {messages.count()}"
        )

        # If second query succeeded, we should have 4+ messages
        if result:
            assert messages.count() >= 4, (
                f"Expected at least 4 messages after 2 queries, got {messages.count()}"
            )

    def test_page_responsive_after_query(self, streamlit_page: Page, send_query):
        """Test page remains responsive after a query."""
        assert send_query("Test query for responsiveness"), "Query timed out"
        streamlit_page.wait_for_timeout(2000)

        # Input should still work
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        assert chat_input.is_visible(), "Chat input not visible"
        assert chat_input.is_enabled(), "Chat input not enabled"


@pytest.mark.chat_workflow
class TestLongQueryHandling:
    """Test handling of long text queries."""

    def test_long_query_processed(self, streamlit_page: Page, send_query):
        """Test that a very long query is processed without crashing."""
        long_query = (
            "Tell me about the history of the NBA, including the most important "
            "championships, the greatest players of all time, the evolution of "
            "the rules, and how the league has changed over the decades with "
            "expansion teams and international players joining the league"
        )

        assert send_query(long_query), "Long query timed out"

        # Should not show failure message
        content = streamlit_page.content()
        assert "Failed" not in content, "Failure message visible for long query"

        # Page should still be responsive
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        assert chat_input.is_visible()


@pytest.mark.chat_workflow
class TestClearHistory:
    """Test clearing chat history."""

    def test_clear_history_button_works(self, streamlit_page: Page):
        """Test that clicking Clear History shows confirmation message."""
        # Click Clear History button in sidebar (no need to send query first)
        clear_btn = streamlit_page.locator("button").filter(has_text="Clear History")
        assert clear_btn.count() > 0, "Clear History button not found"
        clear_btn.first.click()

        # Wait for page rerun
        streamlit_page.wait_for_timeout(3000)

        # Should show "History cleared" message
        content = streamlit_page.content()
        assert "History cleared" in content or "How can I help" in content, (
            "Clear history confirmation not shown"
        )

        # Should have exactly 1 message (the cleared/welcome message)
        messages_after = streamlit_page.locator(
            "[data-testid='stChatMessage']"
        ).count()
        assert messages_after == 1, (
            f"Expected 1 message after clear, got {messages_after}"
        )


@pytest.mark.chat_workflow
class TestStatsDisplay:
    """Test feedback statistics display in sidebar."""

    def test_feedback_stats_section_visible(self, streamlit_page: Page):
        """Test that Feedback Stats section is visible in sidebar."""
        streamlit_page.wait_for_timeout(2000)

        content = streamlit_page.content()
        assert "Feedback Stats" in content, "Feedback Stats section not found in sidebar"

    def test_total_interactions_metric_visible(self, streamlit_page: Page):
        """Test that Total Interactions metric is displayed."""
        streamlit_page.wait_for_timeout(2000)

        content = streamlit_page.content()
        assert "Total Interactions" in content, "Total Interactions metric not found"

    def test_positive_negative_metrics_visible(self, streamlit_page: Page):
        """Test that positive/negative feedback metrics are displayed."""
        streamlit_page.wait_for_timeout(2000)

        content = streamlit_page.content()
        assert "Positive" in content, "Positive feedback metric not found"
        assert "Negative" in content, "Negative feedback metric not found"


@pytest.mark.chat_workflow
class TestProcessingTime:
    """Test processing time display."""

    def test_processing_time_shown_after_query(self, streamlit_page: Page, send_query):
        """Test that processing time is displayed after response."""
        assert send_query("What is a three-pointer?"), "Query timed out"

        # Wait for full page render (processing time caption renders after response)
        streamlit_page.wait_for_timeout(5000)

        content = streamlit_page.content()
        if "⚠️" in content or "❌" in content:
            pytest.skip("LLM returned error (rate limit/timeout) — no processing time")

        # Check for processing time indicator or millisecond display
        assert "⏱️" in content or "ms" in content, (
            "Processing time indicator not found after query response"
        )


@pytest.mark.chat_workflow
class TestNoSourcesResponse:
    """Test response display when no sources are found."""

    def test_greeting_has_no_sources(self, streamlit_page: Page, send_query):
        """Test that greeting responses show no source documents."""
        assert send_query("thanks", timeout_ms=15000), "Greeting timed out"
        streamlit_page.wait_for_timeout(2000)

        # No sources should be displayed for greetings
        sources = streamlit_page.locator("text=/📚 Sources:/")
        assert sources.count() == 0, "Sources shown for greeting response"


@pytest.mark.chat_workflow
class TestSettingsDisplay:
    """Test settings panel display."""

    def test_settings_section_visible(self, streamlit_page: Page):
        """Test that Settings section is visible in sidebar."""
        content = streamlit_page.content()
        assert "Settings" in content, "Settings section not found"

    def test_model_info_displayed(self, streamlit_page: Page):
        """Test that model information is displayed in settings."""
        content = streamlit_page.content()
        assert "Model:" in content, "Model info not displayed in settings"

    def test_api_url_displayed(self, streamlit_page: Page):
        """Test that API URL is displayed in settings."""
        # Wait for sidebar settings section to fully render
        streamlit_page.wait_for_timeout(5000)
        content = streamlit_page.content()
        assert "localhost:8000" in content or "API" in content, (
            "API URL or API indicator not displayed in settings"
        )
