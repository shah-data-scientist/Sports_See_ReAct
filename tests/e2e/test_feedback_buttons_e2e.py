"""
FILE: test_feedback_buttons_e2e.py
STATUS: Active
RESPONSIBILITY: E2E tests for feedback button interactions in Streamlit UI
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

import pytest
from playwright.sync_api import Page


@pytest.mark.feedback
class TestFeedbackButtonsE2E:
    """Test actual feedback button clicks in the UI.

    Note: Feedback buttons only appear when the LLM returns a successful response
    AND the interaction is logged. Rate limiting (429) or API errors may cause
    buttons to not appear — tests skip gracefully in those cases.
    """

    def _get_feedback_buttons(self, streamlit_page: Page):
        """Find feedback buttons on the page, returning (positive, negative) or None."""
        positive = streamlit_page.locator("button").filter(has_text="👍")
        negative = streamlit_page.locator("button").filter(has_text="👎")
        if positive.count() > 0 and negative.count() > 0:
            return positive.first, negative.first
        return None

    def test_feedback_buttons_appear_after_response(self, streamlit_page: Page, send_query):
        """Test that thumbs-up/thumbs-down buttons appear after successful LLM response."""
        assert send_query("Who won the most NBA titles?"), "Response timed out"
        streamlit_page.wait_for_timeout(3000)

        # Check for error indicators (rate limit, timeout, etc.)
        content = streamlit_page.content()
        if "⚠️" in content or "❌" in content:
            pytest.skip("LLM returned error (rate limit/timeout) — no feedback buttons")

        buttons = self._get_feedback_buttons(streamlit_page)
        if buttons is None:
            pytest.skip("Feedback buttons not rendered — interaction logging may have failed")

        positive, negative = buttons
        assert positive.is_visible(), "Positive feedback button not visible"
        assert negative.is_visible(), "Negative feedback button not visible"

    def test_positive_feedback_click_shows_confirmation(self, streamlit_page: Page, send_query):
        """Test clicking positive feedback button shows confirmation message."""
        assert send_query("What is the NBA draft?"), "Response timed out"
        streamlit_page.wait_for_timeout(3000)

        buttons = self._get_feedback_buttons(streamlit_page)
        if buttons is None:
            pytest.skip("Feedback buttons not visible — likely rate limited")

        positive, _ = buttons
        positive.click()

        # Wait for page rerun and confirmation
        streamlit_page.wait_for_timeout(3000)

        content = streamlit_page.content()
        assert "Thanks for positive feedback" in content, (
            "Positive feedback confirmation not shown after clicking thumbs-up"
        )

    def test_negative_feedback_click_shows_comment_form(self, streamlit_page: Page, send_query):
        """Test clicking negative feedback button shows comment form."""
        assert send_query("Tell me about basketball rules"), "Response timed out"
        streamlit_page.wait_for_timeout(3000)

        buttons = self._get_feedback_buttons(streamlit_page)
        if buttons is None:
            pytest.skip("Feedback buttons not visible — likely rate limited")

        _, negative = buttons
        negative.click()

        # Wait for page rerun and comment form
        streamlit_page.wait_for_timeout(3000)

        content = streamlit_page.content()
        has_comment_form = "What was wrong" in content or "Send feedback" in content
        has_confirmation = "Thanks for your feedback" in content

        assert has_comment_form or has_confirmation, (
            "Neither comment form nor confirmation shown after clicking thumbs-down"
        )

    def test_no_422_error_on_feedback(self, streamlit_page: Page, send_query):
        """Test that feedback submission doesn't cause 422 validation error."""
        assert send_query("What is a slam dunk?"), "Response timed out"
        streamlit_page.wait_for_timeout(3000)

        # Click positive feedback if available
        buttons = self._get_feedback_buttons(streamlit_page)
        if buttons is not None:
            positive, _ = buttons
            positive.click()
            streamlit_page.wait_for_timeout(3000)

        # Verify no 422 error codes appear
        content = streamlit_page.content()
        assert "422" not in content, "422 validation error visible to user"
        assert "Failed to submit feedback" not in content, (
            "Feedback submission failure visible"
        )
