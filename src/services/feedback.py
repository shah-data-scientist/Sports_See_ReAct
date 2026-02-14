"""
FILE: feedback.py
STATUS: Active
RESPONSIBILITY: Business logic layer for feedback management and interaction logging
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

import logging
from functools import lru_cache

from src.models.feedback import (
    ChatInteractionCreate,
    ChatInteractionResponse,
    FeedbackCreate,
    FeedbackRating,
    FeedbackResponse,
    FeedbackStats,
)
from src.repositories.feedback import FeedbackRepository

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for managing feedback and chat interactions."""

    def __init__(self, repository: FeedbackRepository | None = None):
        """Initialize the service.

        Args:
            repository: FeedbackRepository instance. Created if not provided.
        """
        self.repository = repository or FeedbackRepository()

    def log_interaction(
        self,
        query: str,
        response: str,
        sources: list[str] | None = None,
        processing_time_ms: int | None = None,
    ) -> ChatInteractionResponse:
        """Log a chat interaction.

        Args:
            query: User's query
            response: AI's response
            sources: List of source documents used
            processing_time_ms: Processing time in milliseconds

        Returns:
            Saved interaction with generated ID
        """
        interaction = ChatInteractionCreate(
            query=query,
            response=response,
            sources=sources or [],
            processing_time_ms=processing_time_ms,
        )
        saved = self.repository.save_interaction(interaction)
        logger.info("Logged interaction %s", saved.id)
        return saved

    def submit_feedback(
        self,
        interaction_id: str,
        rating: FeedbackRating,
        comment: str | None = None,
    ) -> FeedbackResponse:
        """Submit feedback for an interaction.

        Args:
            interaction_id: ID of the interaction to rate
            rating: Positive or negative rating
            comment: Optional comment (encouraged for negative)

        Returns:
            Saved feedback

        Raises:
            ValueError: If interaction not found or feedback exists
        """
        feedback = FeedbackCreate(
            interaction_id=interaction_id,
            rating=rating,
            comment=comment,
        )
        saved = self.repository.save_feedback(feedback)
        logger.info(
            "Submitted %s feedback for interaction %s",
            rating.value,
            interaction_id,
        )
        return saved

    def update_feedback(
        self,
        interaction_id: str,
        rating: FeedbackRating,
        comment: str | None = None,
    ) -> FeedbackResponse | None:
        """Update existing feedback.

        Args:
            interaction_id: Interaction ID
            rating: New rating
            comment: New comment

        Returns:
            Updated feedback or None if not found
        """
        return self.repository.update_feedback(interaction_id, rating, comment)

    def get_interaction(self, interaction_id: str) -> ChatInteractionResponse | None:
        """Get a specific interaction by ID.

        Args:
            interaction_id: Interaction ID

        Returns:
            Interaction or None if not found
        """
        return self.repository.get_interaction(interaction_id)

    def get_recent_interactions(
        self, limit: int = 50, offset: int = 0
    ) -> list[ChatInteractionResponse]:
        """Get recent chat interactions.

        Args:
            limit: Maximum number to return
            offset: Number to skip

        Returns:
            List of recent interactions
        """
        return self.repository.get_recent_interactions(limit, offset)

    def get_stats(self) -> FeedbackStats:
        """Get feedback statistics.

        Returns:
            Statistics about feedback
        """
        return self.repository.get_stats()

    def get_negative_feedback_with_comments(self) -> list[ChatInteractionResponse]:
        """Get all negative feedback with comments for review.

        Returns:
            List of interactions with negative feedback and comments
        """
        return self.repository.get_negative_feedback_with_comments()


@lru_cache
def get_feedback_service() -> FeedbackService:
    """Get cached feedback service instance.

    Returns:
        FeedbackService instance
    """
    return FeedbackService()
