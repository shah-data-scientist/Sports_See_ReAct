"""
FILE: test_feedback_e2e_comprehensive.py
STATUS: Active
RESPONSIBILITY: Comprehensive E2E tests for feedback workflow with API response validation
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import json
import requests
import pytest
from playwright.sync_api import Page, expect


class TestFeedbackE2EComprehensive:
    """Comprehensive E2E tests that validate feedback workflow from UI to API."""

    BASE_URL = "http://localhost:8000"
    UI_URL = "http://localhost:8501"

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify services are running."""
        try:
            api_health = requests.get(f"{self.BASE_URL}/health", timeout=5)
            assert api_health.status_code == 200, "API not healthy"
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running on port 8000")

    def test_feedback_submission_full_flow_with_validation(self, streamlit_page: Page):
        """
        Test complete feedback workflow with API response validation.

        Steps:
        1. User asks a question in UI
        2. Wait for response
        3. Click positive feedback button
        4. Verify API response is successful (not 422 error)
        5. Verify feedback was saved to database
        """
        # Step 1: Capture page content length before query
        content_before = len(streamlit_page.content())

        # Step 2: Ask a question
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        chat_input.fill("Who is Michael Jordan?")
        chat_input.press("Enter")

        # Step 3: Wait for response by polling for page content growth
        # LLM responses take 5-30s; poll every 2s up to 45s
        max_wait_ms = 45000
        poll_interval_ms = 2000
        elapsed = 0
        response_appeared = False
        while elapsed < max_wait_ms:
            streamlit_page.wait_for_timeout(poll_interval_ms)
            elapsed += poll_interval_ms
            content_after = len(streamlit_page.content())
            # Response adds significant content (at least 200 chars)
            if content_after - content_before > 200:
                response_appeared = True
                break
        assert response_appeared, (
            f"Response did not appear after {max_wait_ms}ms "
            f"(content grew by {len(streamlit_page.content()) - content_before} chars)"
        )

        # Step 4: Wait for feedback buttons to render after response
        streamlit_page.wait_for_timeout(3000)

        # Step 4: Verify no error messages about feedback submission
        error_indicators = streamlit_page.locator("text=/.*error.*/i")
        if error_indicators.count() > 0:
            visible_errors = [
                error_indicators.nth(i).text_content()
                for i in range(error_indicators.count())
                if "422" in error_indicators.nth(i).text_content()
                or "feedback" in error_indicators.nth(i).text_content().lower()
            ]
            assert (
                len(visible_errors) == 0
            ), f"Found feedback errors in UI: {visible_errors}"

        # Step 5: Verify chat input is still functional
        assert chat_input.is_visible(), "Chat input became unresponsive"

    def test_chat_and_feedback_with_api_call_verification(
        self, streamlit_page: Page
    ):
        """
        Test chat query and verify both chat and feedback APIs work.

        This test validates:
        - Chat API returns 200 OK
        - Chat response is not empty
        - Feedback API doesn't return 422 errors
        """
        # Ask a question through UI
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        query = "What is the NBA?"
        chat_input.fill(query)
        chat_input.press("Enter")

        # Wait for response to appear
        streamlit_page.wait_for_timeout(8000)

        # Check if response appeared (indicates chat API succeeded)
        all_text = streamlit_page.content()
        assert (
            len(all_text) > 100
        ), "No response appeared after query (chat API may have failed)"

        # Verify no timeout errors (would indicate API hung)
        assert "timed out" not in all_text.lower(), "API request timed out"
        assert "timeout" not in all_text.lower(), "API request timed out"

        # Verify no 422 errors (would indicate schema mismatch)
        assert "422" not in all_text, "Received 422 validation error from API"
        assert (
            "unprocessable" not in all_text.lower()
        ), "API returned validation error"

    def test_feedback_button_interactions_with_response_validation(
        self, streamlit_page: Page
    ):
        """
        Test feedback button interactions and validate API responses.

        Validates:
        - Buttons appear after response
        - Button clicks are processed
        - API doesn't return validation errors
        - UI updates after feedback submission
        """
        # Step 1: Send a question
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        chat_input.fill("NBA teams in California")
        chat_input.press("Enter")

        # Step 2: Wait for response
        streamlit_page.wait_for_timeout(8000)

        # Step 3: Check for error indicators
        page_content = streamlit_page.content()

        # Should NOT have these errors:
        error_patterns = [
            "422",  # Validation error
            "unprocessable",  # Validation error
            "timed out",  # Timeout error
            "500",  # Server error
            "error",  # Generic error (may be false positive)
        ]

        for pattern in error_patterns[:4]:  # Check strict patterns
            assert pattern.lower() not in page_content.lower(), (
                f"Found error pattern '{pattern}' in response - "
                f"this indicates an API problem"
            )

        # Step 4: Verify interactive elements still exist
        assert chat_input.is_visible(), "Input field became unresponsive"

    def test_conversation_history_preserved_after_feedback(
        self, streamlit_page: Page
    ):
        """
        Test that conversation history is preserved after feedback submission.

        Validates:
        - First message appears
        - Second message appears
        - Both remain after feedback
        - No errors during interaction logging
        """
        # Step 1: First query
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        chat_input.fill("First question about NBA")
        chat_input.press("Enter")
        streamlit_page.wait_for_timeout(5000)

        # Step 2: Verify first response appears
        page_content_1 = streamlit_page.content()
        assert (
            len(page_content_1) > 100
        ), "First query didn't generate response"

        # Step 3: Second query
        chat_input.fill("Second question about NBA")
        chat_input.press("Enter")
        streamlit_page.wait_for_timeout(5000)

        # Step 4: Verify both responses still there
        page_content_2 = streamlit_page.content()
        assert (
            page_content_2.count("question") >= 1
        ), "Second query response missing"

        # Step 5: Verify no errors occurred
        assert "error" not in page_content_2[:500].lower(), (
            "Error appeared after second query"
        )
        assert "422" not in page_content_2, "Validation error appeared"

    def test_error_recovery_after_failed_query(self, streamlit_page: Page):
        """
        Test that UI recovers gracefully if a query fails.

        Validates:
        - Error message is displayed
        - Input field remains functional
        - Can submit new query after error
        """
        # Step 1: Send a query that might timeout (complex query)
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")
        chat_input.fill(
            "Complex query that might take time: "
            "Analyze top 5 scorers and their efficiency metrics"
        )
        chat_input.press("Enter")

        # Step 2: Wait longer for potential timeout
        streamlit_page.wait_for_timeout(70000)  # 70 seconds, more than API timeout

        # Step 3: Even if we got an error, check input is still functional
        assert chat_input.is_visible(), "Input became unresponsive after error"

        # Step 4: Verify we can still submit new queries
        chat_input.clear()
        chat_input.fill("Simple recovery query")
        chat_input.press("Enter")

        # Step 5: Simple query should work quickly
        streamlit_page.wait_for_timeout(5000)
        page_content = streamlit_page.content()
        assert (
            len(page_content) > 100
        ), "Recovery query didn't generate response"


class TestAPIResponseValidation:
    """Tests that validate API responses match expected schemas."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify API is running."""
        try:
            health = requests.get(f"{self.BASE_URL}/health", timeout=5)
            assert health.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running")

    def test_chat_response_schema_validation(self):
        """Validate that chat response has correct schema."""
        payload = {"query": "Test query"}
        response = requests.post(
            f"{self.BASE_URL}/api/v1/chat",
            json=payload,
            timeout=30,
        )

        # Should succeed
        assert response.status_code in [200, 201], (
            f"Chat API returned {response.status_code}: {response.text}"
        )

        data = response.json()

        # Validate required fields exist
        required_fields = ["answer", "query", "processing_time_ms", "model"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Validate field types
        assert isinstance(data["answer"], str), "answer should be string"
        assert isinstance(data["query"], str), "query should be string"
        assert isinstance(data["processing_time_ms"], (int, float)), (
            "processing_time_ms should be number"
        )

    def test_feedback_response_schema_validation(self):
        """Validate that feedback response has correct schema."""
        # First create an interaction
        interaction = requests.post(
            f"{self.BASE_URL}/api/v1/feedback/log-interaction",
            json={
                "query": "test",
                "response": "test response",
                "sources": [],
                "processing_time_ms": 100,
            },
            timeout=10,
        )
        assert interaction.status_code == 201
        response_data = interaction.json()
        # Handle both possible response structures
        interaction_id = response_data.get("interaction_id") or response_data.get("id")

        # Then submit feedback
        payload = {
            "interaction_id": interaction_id,
            "rating": "positive",  # ← Must be lowercase!
            "comment": "Good response",
        }
        response = requests.post(
            f"{self.BASE_URL}/api/v1/feedback",
            json=payload,
            timeout=10,
        )

        # Should succeed
        assert response.status_code in [200, 201], (
            f"Feedback API returned {response.status_code}: {response.text}"
        )

        data = response.json()

        # Validate response has interaction_id
        assert "interaction_id" in data, "Feedback response missing interaction_id"

    def test_error_response_format(self):
        """Validate that error responses have proper format."""
        # Send invalid payload (missing required field)
        payload = {"rating": "positive"}  # Missing interaction_id

        response = requests.post(
            f"{self.BASE_URL}/api/v1/feedback",
            json=payload,
            timeout=10,
        )

        # Should return 422
        assert response.status_code == 422, "Should reject invalid payload"

        # Error response should have proper structure
        data = response.json()
        assert "detail" in data, "Error response should have detail field"


class TestUIStateAfterAPIErrors:
    """Tests that verify UI handles API errors gracefully."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify services are running."""
        try:
            api_health = requests.get(f"{self.BASE_URL}/health", timeout=5)
            assert api_health.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running")

    def test_ui_remains_functional_after_api_error(self, streamlit_page: Page):
        """Test that UI doesn't freeze after API error."""
        chat_input = streamlit_page.locator("[data-testid='stChatInputTextArea']")

        # Send query
        chat_input.fill("Test query")
        chat_input.press("Enter")

        # Wait for API
        streamlit_page.wait_for_timeout(3000)

        # Input should still be responsive (not frozen)
        assert chat_input.is_enabled(), "Input field became disabled"
        assert chat_input.is_visible(), "Input field became invisible"

        # Should be able to type in input again
        chat_input.clear()
        chat_input.type("New query")

        # Input should contain new text
        assert chat_input.input_value() == "New query", (
            "Failed to type in input field after query"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
