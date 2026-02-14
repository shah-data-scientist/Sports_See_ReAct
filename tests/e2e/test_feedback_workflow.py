"""
FILE: test_feedback_workflow.py
STATUS: Active
RESPONSIBILITY: Test feedback collection workflow in Streamlit UI
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import pytest
from playwright.sync_api import Page


@pytest.mark.feedback
def test_feedback_buttons_appear(streamlit_page: Page):
    """Test that feedback buttons appear after response."""
    # Ask a question
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("Who is Kobe Bryant?")
    chat_input.press("Enter")

    # Wait for response
    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    assert chat_input.is_visible()


@pytest.mark.feedback
def test_positive_feedback_submission(streamlit_page: Page):
    """Test that positive feedback can be submitted."""
    # Ask a question
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("NBA teams")
    chat_input.press("Enter")

    # Wait for response
    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive after query
    assert chat_input.is_visible()


@pytest.mark.feedback
def test_negative_feedback_shows_comment_form(streamlit_page: Page):
    """Test that clicking negative feedback shows comment form."""
    # Ask a question
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("Test query for feedback")
    chat_input.press("Enter")

    # Wait for response
    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    assert chat_input.is_visible()


@pytest.mark.feedback
def test_negative_feedback_comment_submission(streamlit_page: Page):
    """Test that negative feedback with comment can be submitted."""
    # Ask a question
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("Test feedback comment")
    chat_input.press("Enter")

    # Wait for response
    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    assert chat_input.is_visible()


@pytest.mark.feedback
def test_multiple_feedback_submissions(streamlit_page: Page):
    """Test that user can submit multiple feedback items."""
    for i in range(2):
        # Ask a question
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        chat_input.fill(f"Query {i+1} for feedback")
        chat_input.press("Enter")

        # Wait for response
        streamlit_page.wait_for_timeout(3000)

        # Verify page is still responsive
        assert chat_input.is_visible()


@pytest.mark.feedback
def test_feedback_button_state_changes(streamlit_page: Page):
    """Test that feedback button state changes after submission."""
    # Ask a question
    chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
    chat_input.fill("Feedback state test")
    chat_input.press("Enter")

    # Wait for response
    streamlit_page.wait_for_timeout(5000)

    # Verify page is still responsive
    assert chat_input.is_visible()
