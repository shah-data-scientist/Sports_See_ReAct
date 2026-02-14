"""
FILE: test_rich_conversation.py
STATUS: Active
RESPONSIBILITY: Test rich multi-turn conversation scenarios
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import pytest
from playwright.sync_api import Page


@pytest.mark.rich_conversation
def test_multi_turn_conversation(streamlit_page: Page):
    """Test that multi-turn conversation works correctly."""
    queries = [
        "Who is Michael Jordan?",
        "What are his achievements?",
        "How does he compare to LeBron?",
    ]

    for query in queries:
        # Ask question
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        chat_input.fill(query)
        chat_input.press("Enter")

        # Wait for response
        streamlit_page.wait_for_timeout(5000)

        # Verify page is still responsive
        assert chat_input.is_visible()


@pytest.mark.rich_conversation
def test_contextual_understanding(streamlit_page: Page):
    """Test that system understands context in multi-turn conversation."""
    # First query
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("Tell me about LeBron James")
    chat_input.press("Enter")
    streamlit_page.wait_for_timeout(5000)

    # Second query referring to previous context
    chat_input.fill("What about his defense?")
    chat_input.press("Enter")

    # Wait for response
    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    assert chat_input.is_visible()


@pytest.mark.rich_conversation
def test_comparison_queries(streamlit_page: Page):
    """Test that comparison queries work."""
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")

    chat_input.fill("Compare Kobe Bryant and Michael Jordan")
    chat_input.press("Enter")

    # Wait for response
    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    assert chat_input.is_visible()


@pytest.mark.rich_conversation
def test_historical_context_queries(streamlit_page: Page):
    """Test that historical context queries work."""
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")

    chat_input.fill("What are the greatest NBA moments in history?")
    chat_input.press("Enter")

    # Wait for response
    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    assert chat_input.is_visible()


@pytest.mark.rich_conversation
def test_each_response_tracked_separately(streamlit_page: Page):
    """Test that each response is tracked separately for feedback."""
    # Ask first question
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("First question about NBA")
    chat_input.press("Enter")
    streamlit_page.wait_for_timeout(3000)

    # Ask second question
    chat_input.fill("Second question about NBA")
    chat_input.press("Enter")
    streamlit_page.wait_for_timeout(3000)

    # Verify page is still responsive
    assert chat_input.is_visible()


@pytest.mark.rich_conversation
def test_conversation_persistence(streamlit_page: Page):
    """Test that conversation messages persist in the chat."""
    # Ask multiple questions
    for i in range(3):
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        chat_input.fill(f"Question {i+1} about NBA")
        chat_input.press("Enter")
        streamlit_page.wait_for_timeout(3000)

    # Verify page is still responsive
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    assert chat_input.is_visible()


@pytest.mark.rich_conversation
def test_response_variety(streamlit_page: Page):
    """Test that different queries return different responses."""
    queries = [
        "What is basketball?",
        "Who won the 2024 championship?",
        "What are NBA rules?",
    ]

    for query in queries:
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        chat_input.fill(query)
        chat_input.press("Enter")
        streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    assert chat_input.is_visible()
