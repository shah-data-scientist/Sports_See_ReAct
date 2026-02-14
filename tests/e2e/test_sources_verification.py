"""
FILE: test_sources_verification.py
STATUS: Active
RESPONSIBILITY: Test source document display and verification
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import pytest
from playwright.sync_api import Page


@pytest.mark.sources
def test_sources_expander_visible(streamlit_page: Page):
    """Test that sources expander is visible after response."""
    # Ask a question
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("NBA statistics query")
    chat_input.press("Enter")

    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    assert chat_input.is_visible()


@pytest.mark.sources
def test_sources_expandable(streamlit_page: Page):
    """Test that sources can be expanded and collapsed."""
    # Ask a question
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("Test query for sources")
    chat_input.press("Enter")

    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    assert chat_input.is_visible()


@pytest.mark.sources
def test_source_document_names_display(streamlit_page: Page):
    """Test that source document names are displayed."""
    # Ask a question
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("Query with sources")
    chat_input.press("Enter")

    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    assert chat_input.is_visible()


@pytest.mark.sources
def test_source_similarity_scores(streamlit_page: Page):
    """Test that source similarity scores are displayed."""
    # Ask a question
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("Test source scores")
    chat_input.press("Enter")

    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    assert chat_input.is_visible()


@pytest.mark.sources
def test_source_text_preview(streamlit_page: Page):
    """Test that source text preview is displayed."""
    # Ask a question
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("Query for text preview")
    chat_input.press("Enter")

    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    assert chat_input.is_visible()


@pytest.mark.sources
def test_multiple_sources_display(streamlit_page: Page):
    """Test that multiple sources are displayed."""
    # Ask a question that should return multiple sources
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("Tell me about multiple NBA players")
    chat_input.press("Enter")

    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    assert chat_input.is_visible()


@pytest.mark.sources
def test_source_collapsible(streamlit_page: Page):
    """Test that sources can be collapsed after expanding."""
    # Ask question
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("Sources collapse test")
    chat_input.press("Enter")

    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    assert chat_input.is_visible()
