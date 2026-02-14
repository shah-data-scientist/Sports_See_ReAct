"""
FILE: api_client.py
STATUS: Active
RESPONSIBILITY: HTTP client for communicating with API from Streamlit UI
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import logging
import requests
from typing import Any, Optional
from dataclasses import dataclass, asdict

from src.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ChatRequest:
    """Request data for chat endpoint."""

    query: str
    k: int = 5
    include_sources: bool = True
    conversation_id: Optional[str] = None
    turn_number: Optional[int] = None


class APIClient:
    """HTTP client for communicating with API endpoints.

    This replaces direct service instantiation in Streamlit.
    All processing happens on the API server, not in Streamlit.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize API client.

        Args:
            base_url: Base URL of the API server (default: localhost:8000, set to 8000 for standard port)
        """
        self.base_url = base_url
        self.timeout = 60  # 60 second timeout for long queries
        logger.info(f"APIClient initialized with base_url: {base_url}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make HTTP request to API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path (e.g., "/api/v1/chat")
            **kwargs: Additional arguments to pass to requests

        Returns:
            Parsed JSON response

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)

        try:
            logger.info(f"{method} {endpoint}")
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {endpoint}")
            raise
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to API at {self.base_url}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} for {endpoint}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    # ==================== CHAT ENDPOINTS ====================

    def chat(self, request: ChatRequest) -> dict:
        """Send chat request to API.

        Args:
            request: ChatRequest with query and parameters

        Returns:
            ChatResponse dict with answer and sources
        """
        logger.info(f"Chat request: {request.query[:50]}...")
        return self._make_request(
            "POST",
            "/api/v1/chat",
            json={k: v for k, v in asdict(request).items() if v is not None},
        )

    def search(
        self,
        query: str,
        k: int = 5,
        min_score: Optional[float] = None,
    ) -> list[dict]:
        """Search knowledge base without generating answer.

        Args:
            query: Search query
            k: Number of results to return
            min_score: Minimum similarity score (0-1)

        Returns:
            List of SearchResult dicts
        """
        logger.info(f"Search: {query[:50]}...")
        params = {"query": query, "k": k}
        if min_score is not None:
            params["min_score"] = min_score
        return self._make_request(
            "GET",
            "/api/v1/search",
            params=params,
        )

    # ==================== CONVERSATION ENDPOINTS ====================

    def start_conversation(self, title: Optional[str] = None) -> dict:
        """Create new conversation.

        Args:
            title: Optional conversation title

        Returns:
            ConversationResponse dict with id and metadata
        """
        logger.info("Creating new conversation...")
        payload = {}
        if title:
            payload["title"] = title
        return self._make_request(
            "POST",
            "/api/v1/conversations",
            json=payload,
        )

    def get_conversation(self, conversation_id: str) -> dict:
        """Get conversation by ID.

        Args:
            conversation_id: ID of conversation to retrieve

        Returns:
            ConversationResponse dict
        """
        logger.info(f"Getting conversation: {conversation_id}")
        return self._make_request(
            "GET",
            f"/api/v1/conversations/{conversation_id}",
        )

    def list_conversations(
        self,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """List conversations.

        Args:
            status: Filter by conversation status
            limit: Maximum number to return
            offset: Number to skip

        Returns:
            List of ConversationResponse dicts
        """
        logger.info(f"Listing conversations (limit={limit}, offset={offset})")
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        return self._make_request(
            "GET",
            "/api/v1/conversations",
            params=params,
        )

    def get_conversation_history(self, conversation_id: str) -> dict:
        """Get conversation with all messages.

        Args:
            conversation_id: ID of conversation

        Returns:
            ConversationWithMessages dict with messages list
        """
        logger.info(f"Getting conversation history: {conversation_id}")
        return self._make_request(
            "GET",
            f"/api/v1/conversations/{conversation_id}/messages",
        )

    def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        """Update conversation.

        Args:
            conversation_id: ID of conversation to update
            title: New title (optional)
            status: New status (optional)

        Returns:
            Updated ConversationResponse dict
        """
        logger.info(f"Updating conversation: {conversation_id}")
        payload = {}
        if title is not None:
            payload["title"] = title
        if status is not None:
            payload["status"] = status
        return self._make_request(
            "PUT",
            f"/api/v1/conversations/{conversation_id}",
            json=payload,
        )

    def archive_conversation(self, conversation_id: str) -> dict:
        """Archive conversation (soft delete).

        Args:
            conversation_id: ID of conversation to archive

        Returns:
            Updated ConversationResponse dict
        """
        logger.info(f"Archiving conversation: {conversation_id}")
        return self._make_request(
            "DELETE",
            f"/api/v1/conversations/{conversation_id}",
        )

    # ==================== FEEDBACK ENDPOINTS ====================

    def log_interaction(
        self,
        query: str,
        response: str,
        sources: list[str],
        processing_time_ms: int,
        conversation_id: Optional[str] = None,
        turn_number: Optional[int] = None,
    ) -> dict:
        """Log chat interaction to database.

        Args:
            query: User's question
            response: AI-generated answer
            sources: List of source documents
            processing_time_ms: Time taken to generate response
            conversation_id: Optional conversation ID
            turn_number: Optional turn number

        Returns:
            ChatInteractionResponse dict with interaction id
        """
        logger.info(f"Logging interaction: {query[:50]}...")
        payload = {
            "query": query,
            "response": response,
            "sources": sources,
            "processing_time_ms": processing_time_ms,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id
        if turn_number:
            payload["turn_number"] = turn_number
        return self._make_request(
            "POST",
            "/api/v1/feedback/log-interaction",
            json=payload,
        )

    def submit_feedback(
        self,
        interaction_id: str,
        rating: str,
        comment: Optional[str] = None,
    ) -> dict:
        """Submit feedback for an interaction.

        Args:
            interaction_id: ID of the interaction
            rating: "POSITIVE" or "NEGATIVE"
            comment: Optional comment

        Returns:
            FeedbackResponse dict
        """
        logger.info(f"Submitting feedback for interaction: {interaction_id}")
        payload = {
            "interaction_id": interaction_id,
            "rating": rating.lower(),  # Convert to lowercase (API expects "positive" or "negative")
        }
        if comment:
            payload["comment"] = comment
        return self._make_request(
            "POST",
            "/api/v1/feedback",
            json=payload,
        )

    def update_feedback(
        self,
        interaction_id: str,
        rating: str,
        comment: Optional[str] = None,
    ) -> dict:
        """Update feedback for an interaction.

        Args:
            interaction_id: ID of the interaction
            rating: "POSITIVE" or "NEGATIVE"
            comment: Optional comment

        Returns:
            Updated FeedbackResponse dict
        """
        logger.info(f"Updating feedback for interaction: {interaction_id}")
        payload = {
            "rating": rating,
        }
        if comment:
            payload["comment"] = comment
        return self._make_request(
            "PUT",
            f"/api/v1/feedback/{interaction_id}",
            json=payload,
        )

    def get_feedback_stats(self) -> dict:
        """Get feedback statistics.

        Returns:
            FeedbackStats dict with counts and rates
        """
        logger.info("Getting feedback statistics...")
        return self._make_request(
            "GET",
            "/api/v1/feedback/stats",
        )

    def get_negative_feedback(self) -> list[dict]:
        """Get interactions with negative feedback and comments.

        Returns:
            List of ChatInteractionResponse dicts
        """
        logger.info("Getting negative feedback interactions...")
        return self._make_request(
            "GET",
            "/api/v1/feedback/negative",
        )

    def get_recent_interactions(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """Get recent chat interactions.

        Args:
            limit: Maximum number to return
            offset: Number to skip

        Returns:
            List of ChatInteractionResponse dicts
        """
        logger.info(f"Getting recent interactions (limit={limit})")
        return self._make_request(
            "GET",
            "/api/v1/feedback/interactions",
            params={"limit": limit, "offset": offset},
        )

    def get_interaction(self, interaction_id: str) -> dict:
        """Get specific interaction by ID.

        Args:
            interaction_id: ID of interaction to retrieve

        Returns:
            ChatInteractionResponse dict
        """
        logger.info(f"Getting interaction: {interaction_id}")
        return self._make_request(
            "GET",
            f"/api/v1/feedback/interactions/{interaction_id}",
        )

    # ==================== HEALTH ENDPOINTS ====================

    def health_check(self) -> dict:
        """Check API health status.

        Returns:
            HealthResponse dict with status and index info
        """
        logger.info("Health check...")
        return self._make_request(
            "GET",
            "/health",
        )

    def readiness_check(self) -> dict:
        """Check if API is ready to serve requests.

        Returns:
            Dict with ready boolean
        """
        logger.info("Readiness check...")
        return self._make_request(
            "GET",
            "/ready",
        )

    def liveness_check(self) -> dict:
        """Check if API is alive.

        Returns:
            Dict with alive boolean
        """
        logger.info("Liveness check...")
        return self._make_request(
            "GET",
            "/live",
        )
