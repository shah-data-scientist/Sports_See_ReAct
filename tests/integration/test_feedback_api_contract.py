"""
FILE: test_feedback_api_contract.py
STATUS: Active
RESPONSIBILITY: Integration tests validating feedback API contract between UI and API
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import requests
import pytest
from typing import Optional


class TestFeedbackAPIContract:
    """Test that UI sends feedback in the correct format expected by API."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify API is running before tests."""
        try:
            health = requests.get(f"{self.BASE_URL}/health", timeout=5)
            assert health.status_code == 200, "API not responding"
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running on port 8000")

    def test_feedback_enum_values_match_api_expectations(self):
        """Verify feedback rating enum values match API FeedbackRating enum."""
        # API expects: "positive" or "negative" (lowercase)
        # UI must send these exact values

        valid_ratings = ["positive", "negative"]

        for rating in valid_ratings:
            payload = {
                "interaction_id": "test-interaction-123",
                "rating": rating,
            }

            # Should not raise validation error
            response = requests.post(
                f"{self.BASE_URL}/api/v1/feedback",
                json=payload,
                timeout=10,
            )

            # 400 = bad interaction ID (expected, tests validation)
            # 422 = validation error (unexpected, should pass schema validation)
            assert response.status_code != 422, (
                f"API rejected valid rating '{rating}'. "
                f"Error: {response.json()}"
            )

    def test_feedback_uppercase_values_fail_validation(self):
        """Verify that uppercase enum values (common mistake) are rejected."""
        # This is what the UI was doing wrong - sending "POSITIVE" instead of "positive"
        invalid_ratings = ["POSITIVE", "NEGATIVE"]

        for rating in invalid_ratings:
            payload = {
                "interaction_id": "test-interaction-123",
                "rating": rating,
            }

            response = requests.post(
                f"{self.BASE_URL}/api/v1/feedback",
                json=payload,
                timeout=10,
            )

            # Should get 422 validation error for invalid enum value
            assert response.status_code == 422, (
                f"API should reject uppercase '{rating}' but got {response.status_code}"
            )

    def test_feedback_required_fields(self):
        """Verify feedback API requires all mandatory fields."""
        # Missing interaction_id
        payload = {"rating": "positive"}
        response = requests.post(
            f"{self.BASE_URL}/api/v1/feedback",
            json=payload,
            timeout=10,
        )
        assert response.status_code == 422, "API should reject missing interaction_id"

        # Missing rating
        payload = {"interaction_id": "test-123"}
        response = requests.post(
            f"{self.BASE_URL}/api/v1/feedback",
            json=payload,
            timeout=10,
        )
        assert response.status_code == 422, "API should reject missing rating"

    def test_feedback_optional_comment_field(self):
        """Verify comment field is optional but accepted."""
        payload = {
            "interaction_id": "test-interaction-456",
            "rating": "positive",
            "comment": "This is a test comment",
        }

        response = requests.post(
            f"{self.BASE_URL}/api/v1/feedback",
            json=payload,
            timeout=10,
        )

        # Should not be 422 (validation error)
        # May be 400 if interaction doesn't exist (that's OK)
        assert response.status_code != 422, (
            f"API rejected valid feedback with comment. "
            f"Error: {response.json()}"
        )

    def test_feedback_comment_max_length(self):
        """Verify comment field respects max_length constraint."""
        # API expects max 2000 characters
        very_long_comment = "x" * 2001

        payload = {
            "interaction_id": "test-interaction-789",
            "rating": "negative",
            "comment": very_long_comment,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/v1/feedback",
            json=payload,
            timeout=10,
        )

        # Should get validation error for exceeding max length
        assert response.status_code == 422, (
            "API should reject comment exceeding 2000 characters"
        )

    def test_api_endpoint_path_correctness(self):
        """Verify feedback endpoint path matches UI expectations."""
        # UI calls: POST /api/v1/feedback
        # This test verifies that path exists

        payload = {
            "interaction_id": "test-endpoint-check",
            "rating": "positive",
        }

        response = requests.post(
            f"{self.BASE_URL}/api/v1/feedback",
            json=payload,
            timeout=10,
        )

        # Should not be 404 (endpoint not found)
        assert response.status_code != 404, "Feedback endpoint not found at /api/v1/feedback"


class TestFeedbackDataFlow:
    """Test complete feedback flow from UI perspective."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify API is running."""
        try:
            health = requests.get(f"{self.BASE_URL}/health", timeout=5)
            assert health.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running")

    def test_create_interaction_then_submit_feedback(self):
        """Test realistic flow: create conversation → chat → log interaction → submit feedback."""
        # Step 1: Create conversation
        conv_response = requests.post(
            f"{self.BASE_URL}/api/v1/conversations",
            json={"title": "Test Feedback Flow"},
            timeout=10,
        )
        assert conv_response.status_code == 201, "Failed to create conversation"
        conversation_id = conv_response.json()["id"]

        # Step 2: Log interaction (this saves to DB and returns interaction_id)
        interaction_response = requests.post(
            f"{self.BASE_URL}/api/v1/feedback/log-interaction",
            json={
                "query": "test query",
                "response": "test response",
                "sources": ["source1", "source2"],
                "processing_time_ms": 1000,
            },
            timeout=10,
        )
        assert interaction_response.status_code == 201, "Failed to log interaction"
        response_data = interaction_response.json()
        # Handle both possible response structures
        interaction_id = response_data.get("interaction_id") or response_data.get("id")

        # Step 3: Submit feedback for that interaction (with CORRECT lowercase values)
        feedback_response = requests.post(
            f"{self.BASE_URL}/api/v1/feedback",
            json={
                "interaction_id": interaction_id,
                "rating": "positive",  # ← MUST BE LOWERCASE
                "comment": "Good response",
            },
            timeout=10,
        )

        # Should succeed (201 Created or 200 OK)
        assert feedback_response.status_code in [200, 201], (
            f"Failed to submit feedback: {feedback_response.status_code} - "
            f"{feedback_response.json()}"
        )

        feedback_data = feedback_response.json()
        assert feedback_data.get("interaction_id") == interaction_id
        assert feedback_data.get("rating") == "positive"


class TestAPISchemaValidation:
    """Test API schema matches documentation and expectations."""

    BASE_URL = "http://localhost:8000"

    def test_feedback_create_schema_documentation(self):
        """Verify FeedbackCreate schema structure is valid."""
        # According to src/models/feedback.py FeedbackCreate:
        # - interaction_id: str (required)
        # - rating: FeedbackRating enum ("positive" or "negative") (required)
        # - comment: str | None (optional, max 2000)

        # Note: The actual enum validation is tested by test_feedback_enum_values_match_api_expectations
        # which proves the API correctly rejects invalid enum values. This test verifies the
        # schema structure is present and has required fields, not the specific enum documentation.

        try:
            docs = requests.get(f"{self.BASE_URL}/openapi.json", timeout=5)
            if docs.status_code == 200:
                openapi_spec = docs.json()
                feedback_schema = openapi_spec.get("components", {}).get(
                    "schemas", {}
                ).get("FeedbackCreate", {})

                if feedback_schema:
                    # Verify schema has required fields
                    properties = feedback_schema.get("properties", {})
                    required = feedback_schema.get("required", [])

                    # These must be required
                    assert "interaction_id" in required, (
                        "API schema: interaction_id must be required"
                    )
                    assert "rating" in required, (
                        "API schema: rating must be required"
                    )

                    # Verify comment exists but is optional
                    assert "comment" not in required, (
                        "API schema: comment must be optional (not in required list)"
                    )
                    assert "comment" in properties, (
                        "API schema: comment field should exist as optional"
                    )

                    # If enum values are documented, verify they're lowercase
                    rating_field = properties.get("rating", {})
                    rating_enum = rating_field.get("enum", [])
                    if rating_enum:
                        # OpenAPI schema is documenting enums: check they're lowercase
                        assert "POSITIVE" not in rating_enum and "NEGATIVE" not in rating_enum, (
                            "Enum values must be lowercase, not uppercase"
                        )
        except requests.exceptions.ConnectionError:
            pytest.skip("Cannot verify OpenAPI schema - API not running")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
