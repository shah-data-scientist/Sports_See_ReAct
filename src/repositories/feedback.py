"""
FILE: feedback.py
STATUS: Active
RESPONSIBILITY: SQLite feedback repository for chat interaction and feedback persistence
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

import json
import logging
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import settings
from src.models.feedback import (
    Base,
    ChatInteractionCreate,
    ChatInteractionDB,
    ChatInteractionResponse,
    FeedbackCreate,
    FeedbackDB,
    FeedbackRating,
    FeedbackResponse,
    FeedbackStats,
)

logger = logging.getLogger(__name__)


class FeedbackRepository:
    """Repository for managing chat interactions and feedback in SQLite."""

    def __init__(self, db_path: Path | None = None):
        """Initialize the repository.

        Args:
            db_path: Path to SQLite database. Defaults to settings.database_path.
        """
        self.db_path = db_path or settings.database_path
        self._ensure_directory()
        self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._init_db()

    def _ensure_directory(self) -> None:
        """Ensure the database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _init_db(self) -> None:
        """Initialize database tables."""
        Base.metadata.create_all(self.engine)
        logger.info("Database initialized at %s", self.db_path)

    def close(self) -> None:
        """Close database connections and dispose engine."""
        self.engine.dispose()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup.

        Yields:
            SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def _to_feedback_response(db_feedback: FeedbackDB) -> FeedbackResponse:
        """Convert a FeedbackDB row to a FeedbackResponse."""
        return FeedbackResponse(
            id=db_feedback.id,
            interaction_id=db_feedback.interaction_id,
            rating=db_feedback.rating,
            comment=db_feedback.comment,
            created_at=db_feedback.created_at,
        )

    @staticmethod
    def _to_interaction_response(
        db_interaction: ChatInteractionDB,
        feedback: FeedbackResponse | None = None,
    ) -> ChatInteractionResponse:
        """Convert a ChatInteractionDB row to a ChatInteractionResponse."""
        sources = db_interaction.sources
        return ChatInteractionResponse(
            id=db_interaction.id,
            query=db_interaction.query,
            response=db_interaction.response,
            sources=json.loads(sources) if sources else [],
            processing_time_ms=db_interaction.processing_time_ms,
            created_at=db_interaction.created_at,
            conversation_id=db_interaction.conversation_id,
            turn_number=db_interaction.turn_number,
            feedback=feedback,
        )

    def save_interaction(self, interaction: ChatInteractionCreate) -> ChatInteractionResponse:
        """Save a chat interaction.

        Args:
            interaction: Chat interaction data

        Returns:
            Saved interaction with generated ID
        """
        with self.get_session() as session:
            db_interaction = ChatInteractionDB(
                query=interaction.query,
                response=interaction.response,
                sources=json.dumps(interaction.sources),
                processing_time_ms=interaction.processing_time_ms,
                conversation_id=interaction.conversation_id,
                turn_number=interaction.turn_number,
            )
            session.add(db_interaction)
            session.flush()

            return self._to_interaction_response(db_interaction)

    def get_interaction(self, interaction_id: str) -> ChatInteractionResponse | None:
        """Get a chat interaction by ID.

        Args:
            interaction_id: Interaction ID

        Returns:
            Chat interaction or None if not found
        """
        with self.get_session() as session:
            db_interaction = session.query(ChatInteractionDB).filter_by(id=interaction_id).first()
            if not db_interaction:
                return None

            feedback = None
            if db_interaction.feedback:
                feedback = self._to_feedback_response(db_interaction.feedback)

            return self._to_interaction_response(db_interaction, feedback)

    def save_feedback(self, feedback: FeedbackCreate) -> FeedbackResponse:
        """Save feedback for an interaction.

        Args:
            feedback: Feedback data

        Returns:
            Saved feedback

        Raises:
            ValueError: If interaction not found or feedback already exists
        """
        with self.get_session() as session:
            # Verify interaction exists
            interaction = (
                session.query(ChatInteractionDB).filter_by(id=feedback.interaction_id).first()
            )
            if not interaction:
                raise ValueError(f"Interaction {feedback.interaction_id} not found")

            # Check if feedback already exists
            existing = (
                session.query(FeedbackDB).filter_by(interaction_id=feedback.interaction_id).first()
            )
            if existing:
                raise ValueError(
                    f"Feedback already exists for interaction {feedback.interaction_id}"
                )

            db_feedback = FeedbackDB(
                interaction_id=feedback.interaction_id,
                rating=feedback.rating,
                comment=feedback.comment,
            )
            session.add(db_feedback)
            session.flush()

            return self._to_feedback_response(db_feedback)

    def update_feedback(
        self, interaction_id: str, rating: FeedbackRating, comment: str | None = None
    ) -> FeedbackResponse | None:
        """Update existing feedback.

        Args:
            interaction_id: Interaction ID
            rating: New rating
            comment: New comment

        Returns:
            Updated feedback or None if not found
        """
        with self.get_session() as session:
            db_feedback = session.query(FeedbackDB).filter_by(interaction_id=interaction_id).first()
            if not db_feedback:
                return None

            db_feedback.rating = rating
            db_feedback.comment = comment
            session.flush()

            return self._to_feedback_response(db_feedback)

    def get_recent_interactions(
        self, limit: int = 50, offset: int = 0
    ) -> list[ChatInteractionResponse]:
        """Get recent chat interactions.

        Args:
            limit: Maximum number of interactions to return
            offset: Number of interactions to skip

        Returns:
            List of chat interactions
        """
        with self.get_session() as session:
            db_interactions = (
                session.query(ChatInteractionDB)
                .order_by(ChatInteractionDB.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            results = []
            for db_int in db_interactions:
                feedback = None
                if db_int.feedback:
                    feedback = self._to_feedback_response(db_int.feedback)
                results.append(self._to_interaction_response(db_int, feedback))

            return results

    def get_stats(self) -> FeedbackStats:
        """Get feedback statistics.

        Returns:
            Feedback statistics
        """
        with self.get_session() as session:
            total_interactions = session.query(func.count(ChatInteractionDB.id)).scalar() or 0
            total_feedback = session.query(func.count(FeedbackDB.id)).scalar() or 0
            positive_count = (
                session.query(func.count(FeedbackDB.id))
                .filter(FeedbackDB.rating == FeedbackRating.POSITIVE)
                .scalar()
                or 0
            )
            negative_count = (
                session.query(func.count(FeedbackDB.id))
                .filter(FeedbackDB.rating == FeedbackRating.NEGATIVE)
                .scalar()
                or 0
            )

            feedback_rate = (total_feedback / total_interactions * 100) if total_interactions else 0
            positive_rate = (positive_count / total_feedback * 100) if total_feedback else 0

            return FeedbackStats(
                total_interactions=total_interactions,
                total_feedback=total_feedback,
                positive_count=positive_count,
                negative_count=negative_count,
                feedback_rate=round(feedback_rate, 2),
                positive_rate=round(positive_rate, 2),
            )

    def get_negative_feedback_with_comments(self) -> list[ChatInteractionResponse]:
        """Get all interactions with negative feedback that have comments.

        Returns:
            List of interactions with negative feedback and comments
        """
        with self.get_session() as session:
            db_feedbacks = (
                session.query(FeedbackDB)
                .filter(
                    FeedbackDB.rating == FeedbackRating.NEGATIVE,
                    FeedbackDB.comment.isnot(None),
                    FeedbackDB.comment != "",
                )
                .order_by(FeedbackDB.created_at.desc())
                .all()
            )

            results = []
            for fb in db_feedbacks:
                feedback = self._to_feedback_response(fb)
                results.append(self._to_interaction_response(fb.interaction, feedback))

            return results

    def get_messages_by_conversation(self, conversation_id: str) -> list[ChatInteractionResponse]:
        """Get all messages in a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of messages ordered by turn_number
        """
        with self.get_session() as session:
            db_interactions = (
                session.query(ChatInteractionDB)
                .filter(ChatInteractionDB.conversation_id == conversation_id)
                .order_by(ChatInteractionDB.turn_number)
                .all()
            )

            results = []
            for db_int in db_interactions:
                feedback = None
                if db_int.feedback:
                    feedback = self._to_feedback_response(db_int.feedback)
                results.append(self._to_interaction_response(db_int, feedback))

            return results
