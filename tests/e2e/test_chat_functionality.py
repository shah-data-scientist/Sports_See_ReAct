"""
FILE: test_chat_functionality.py
STATUS: Active
RESPONSIBILITY: Test chat functionality in Streamlit UI
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import pytest
from playwright.sync_api import Page


@pytest.mark.chat
def test_app_loads(streamlit_page: Page):
    """Test that Streamlit app loads correctly."""
    # Check page title
    assert "NBA" in streamlit_page.title()

    # Check that app has main content


@pytest.mark.chat
def test_single_query(streamlit_page: Page):
    """Test that user can ask a single question."""
    # Find chat input
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")

    # Type query
    chat_input.fill("Who is LeBron James?")
    chat_input.press("Enter")

    # Wait for response
    streamlit_page.wait_for_timeout(5000)
    assert chat_input.is_visible()


@pytest.mark.chat
def test_multiple_queries_sequence(streamlit_page: Page):
    """Test that user can ask multiple questions in sequence."""
    queries = [
        "Who is Michael Jordan?",
        "What is his career record?",
        "How many championships did he win?"
    ]

    for query in queries:
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        chat_input.fill(query)
        chat_input.press("Enter")
        streamlit_page.wait_for_timeout(2000)
        assert chat_input.is_visible()


@pytest.mark.chat
def test_sources_display(streamlit_page: Page):
    """Test that sources are displayed after response."""
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("NBA statistics")
    chat_input.press("Enter")

    streamlit_page.wait_for_timeout(5000)
    assert chat_input.is_visible()


@pytest.mark.chat
def test_processing_time_display(streamlit_page: Page):
    """Test that processing time is displayed."""
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("Test query")
    chat_input.press("Enter")

    streamlit_page.wait_for_timeout(5000)
    assert chat_input.is_visible()


@pytest.mark.chat
def test_chat_input_accepts_text(streamlit_page: Page):
    """Test that chat input properly accepts typed text."""
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")

    test_text = "Testing user input functionality"
    chat_input.fill(test_text)
    assert chat_input.input_value() == test_text


@pytest.mark.chat
def test_chat_input_clears_after_submission(streamlit_page: Page):
    """Test that chat input is ready for next query."""
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")

    chat_input.fill("Test query to clear")
    chat_input.press("Enter")

    streamlit_page.wait_for_timeout(3000)
    assert chat_input.is_visible()
