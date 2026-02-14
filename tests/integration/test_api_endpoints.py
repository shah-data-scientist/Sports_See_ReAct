"""
FILE: test_api_endpoints.py
STATUS: Active
RESPONSIBILITY: Test all API endpoints used by Streamlit
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import pytest
import requests
from src.ui.api_client import APIClient, ChatRequest


class TestAPIEndpoints:
    """Test suite for all API endpoints."""

    @pytest.fixture
    def client(self):
        """Get API client."""
        return APIClient()

    # ==================== HEALTH ENDPOINTS ====================

    def test_health_check(self, client):
        """Test GET /health endpoint."""
        response = client.health_check()
        assert response is not None
        assert "status" in response
        assert response["status"] in ["healthy", "degraded", "unhealthy"]

    def test_readiness_check(self, client):
        """Test GET /ready endpoint."""
        response = client.readiness_check()
        assert response is not None
        assert "ready" in response
        assert isinstance(response["ready"], bool)

    def test_liveness_check(self, client):
        """Test GET /live endpoint."""
        response = client.liveness_check()
        assert response is not None
        assert "alive" in response
        assert response["alive"] is True

    # ==================== CHAT ENDPOINTS ====================

    def test_chat_endpoint(self, client):
        """Test POST /api/chat endpoint."""
        request = ChatRequest(
            query="Who won the NBA championship in 2023?",
            k=3,
        )
        response = client.chat(request)

        assert response is not None
        assert "answer" in response
        assert "sources" in response
        assert "processing_time_ms" in response
        assert isinstance(response["sources"], list)

    def test_search_endpoint(self, client):
        """Test GET /api/search endpoint."""
        results = client.search(
            query="LeBron James",
            k=3,
        )

        assert results is not None
        assert isinstance(results, list)
        if len(results) > 0:
            result = results[0]
            assert "source" in result
            assert "score" in result
            assert "text" in result

    # ==================== CONVERSATION ENDPOINTS ====================

    def test_create_conversation(self, client):
        """Test POST /api/conversations endpoint."""
        response = client.start_conversation()

        assert response is not None
        assert "id" in response
        assert isinstance(response["id"], str)
        assert len(response["id"]) > 0

    def test_list_conversations(self, client):
        """Test GET /api/conversations endpoint."""
        conversations = client.list_conversations(limit=5)

        assert conversations is not None
        assert isinstance(conversations, list)

    def test_get_conversation(self, client):
        """Test GET /api/conversations/{id} endpoint."""
        # First create a conversation
        created = client.start_conversation()
        conv_id = created["id"]

        # Then get it
        response = client.get_conversation(conv_id)

        assert response is not None
        assert response["id"] == conv_id

    def test_get_conversation_history(self, client):
        """Test GET /api/conversations/{id}/messages endpoint."""
        # First create a conversation
        created = client.start_conversation()
        conv_id = created["id"]

        # Then get its history
        response = client.get_conversation_history(conv_id)

        assert response is not None
        assert "id" in response
        assert "messages" in response
        assert isinstance(response["messages"], list)

    def test_archive_conversation(self, client):
        """Test DELETE /api/conversations/{id} endpoint (soft delete)."""
        # First create a conversation
        created = client.start_conversation()
        conv_id = created["id"]

        # Then archive it
        response = client.archive_conversation(conv_id)

        assert response is not None
        assert "id" in response

    # ==================== FEEDBACK ENDPOINTS ====================

    def test_log_interaction(self, client):
        """Test POST /api/feedback/log-interaction endpoint."""
        response = client.log_interaction(
            query="Test query",
            response="Test response",
            sources=["doc1.pdf", "doc2.pdf"],
            processing_time_ms=1234,
        )

        assert response is not None
        assert "id" in response

    def test_submit_feedback(self, client):
        """Test POST /api/feedback endpoint."""
        # First log an interaction
        interaction = client.log_interaction(
            query="Test",
            response="Test response",
            sources=["doc.pdf"],
            processing_time_ms=100,
        )
        interaction_id = interaction["id"]

        # Then submit feedback
        response = client.submit_feedback(
            interaction_id=interaction_id,
            rating="POSITIVE",
        )

        assert response is not None

    def test_submit_feedback_with_comment(self, client):
        """Test POST /api/feedback endpoint with comment."""
        # First log an interaction
        interaction = client.log_interaction(
            query="Test",
            response="Test response",
            sources=["doc.pdf"],
            processing_time_ms=100,
        )
        interaction_id = interaction["id"]

        # Submit negative feedback with comment
        response = client.submit_feedback(
            interaction_id=interaction_id,
            rating="NEGATIVE",
            comment="Not accurate",
        )

        assert response is not None

    def test_get_feedback_stats(self, client):
        """Test GET /api/feedback/stats endpoint."""
        response = client.get_feedback_stats()

        assert response is not None
        assert "total_interactions" in response
        assert "total_feedback" in response
        assert "positive_count" in response
        assert "negative_count" in response
        assert "positive_rate" in response

    def test_get_negative_feedback(self, client):
        """Test GET /api/feedback/negative endpoint."""
        response = client.get_negative_feedback()

        assert response is not None
        assert isinstance(response, list)

    def test_get_recent_interactions(self, client):
        """Test GET /api/feedback/interactions endpoint."""
        response = client.get_recent_interactions(limit=5)

        assert response is not None
        assert isinstance(response, list)

    # ==================== ERROR HANDLING ====================

    def test_connection_error(self):
        """Test that connection errors are properly raised."""
        # Create client pointing to non-existent server
        bad_client = APIClient(base_url="http://localhost:9999")

        with pytest.raises(requests.exceptions.RequestException):
            bad_client.health_check()

    def test_timeout_error(self, client):
        """Test that timeout errors are properly raised."""
        # Create client with very short timeout
        client.timeout = 0.001

        with pytest.raises(requests.exceptions.Timeout):
            client.chat(ChatRequest(query="Who won the championship?"))


class TestEndpointIntegration:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def client(self):
        """Get API client."""
        return APIClient()

    def test_complete_chat_workflow(self, client):
        """Test complete workflow: create conversation, chat, log interaction, feedback."""
        # 1. Create conversation
        conversation = client.start_conversation()
        conv_id = conversation["id"]
        assert conv_id is not None

        # 2. Chat
        request = ChatRequest(
            query="Who is LeBron James?",
            k=3,
            conversation_id=conv_id,
            turn_number=1,
        )
        response = client.chat(request)
        assert "answer" in response
        assert len(response["answer"]) > 0

        # 3. Log interaction
        interaction = client.log_interaction(
            query="Who is LeBron James?",
            response=response["answer"],
            sources=[s.get("source", "") for s in response.get("sources", [])],
            processing_time_ms=int(response.get("processing_time_ms", 0)),
            conversation_id=conv_id,
            turn_number=1,
        )
        interaction_id = interaction["id"]
        assert interaction_id is not None

        # 4. Submit positive feedback
        feedback = client.submit_feedback(
            interaction_id=interaction_id,
            rating="POSITIVE",
        )
        assert feedback is not None

        # 5. Get stats
        stats = client.get_feedback_stats()
        assert stats["total_interactions"] >= 1

        # 6. Get conversation history
        history = client.get_conversation_history(conv_id)
        assert history is not None
        assert "messages" in history

    def test_search_and_no_chat(self, client):
        """Test search endpoint (used for knowledge base search without generation)."""
        results = client.search(
            query="NBA statistics",
            k=5,
        )

        assert results is not None
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
