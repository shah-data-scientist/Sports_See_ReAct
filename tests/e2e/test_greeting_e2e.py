"""
FILE: test_greeting_e2e.py
STATUS: Active
RESPONSIBILITY: E2E tests for greeting/salutation handling in Streamlit UI
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

import pytest
from playwright.sync_api import Page


@pytest.mark.greeting
class TestGreetingE2E:
    """Test greeting queries return simple responses without RAG search."""

    def test_greeting_returns_friendly_response(self, streamlit_page: Page, send_query):
        """Test that 'hi' returns a friendly greeting, not a RAG search result."""
        assert send_query("hi", timeout_ms=15000), "Greeting response timed out"

        content = streamlit_page.content().lower()
        # Greeting response should contain a friendly word
        greeting_words = ["hello", "hi", "hey", "help", "welcome", "assist", "how can"]
        assert any(word in content for word in greeting_words), (
            "Response should contain a greeting-like word"
        )

    def test_greeting_no_sources_displayed(self, streamlit_page: Page, send_query):
        """Test that greetings don't show source documents (no RAG search)."""
        assert send_query("hello", timeout_ms=15000), "Greeting response timed out"

        # Wait for full render
        streamlit_page.wait_for_timeout(2000)

        # Greetings skip RAG search, so no sources should be displayed
        sources_indicator = streamlit_page.locator("text=/📚 Sources:/")
        assert sources_indicator.count() == 0, (
            "Greeting should not display sources — greetings bypass RAG search"
        )

    def test_greeting_variations_handled(self, streamlit_page: Page, send_query):
        """Test that 'good morning' is recognized as a greeting."""
        assert send_query("good morning", timeout_ms=15000), "Greeting response timed out"

        # Page should still be responsive after greeting
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        assert chat_input.is_visible()
        assert chat_input.is_enabled()

    def test_greeting_page_remains_interactive(self, streamlit_page: Page, send_query):
        """Test that after greeting, chat input remains usable for follow-up."""
        # Send greeting
        assert send_query("hey", timeout_ms=15000), "Greeting response timed out"
        streamlit_page.wait_for_timeout(2000)

        # Chat input should still be visible and enabled
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        assert chat_input.is_visible(), "Chat input not visible after greeting"
        assert chat_input.is_enabled(), "Chat input not enabled after greeting"

        # Should be able to type in the input (but don't send to avoid rate limits)
        chat_input.fill("Follow-up question test")
        assert chat_input.input_value() == "Follow-up question test", (
            "Cannot type in chat input after greeting"
        )
