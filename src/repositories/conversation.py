"""
FILE: conversation.py
STATUS: Active
RESPONSIBILITY: Repository layer for conversation CRUD operations
LAST MAJOR UPDATE: 2026-02-09
MAINTAINER: Shahu
"""

import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import settings
from src.models.conversation import (
    ConversationCreate,
    ConversationDB,
    ConversationResponse,
    ConversationStatus,
    ConversationUpdate,
    ConversationWithMessages,
)
from src.models.feedback import Base, ChatInteractionDB, ChatInteractionResponse

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for conversation database operations.

    Handles CRUD operations for conversations with proper session management
    and error handling.

    Attributes:
        db_path: Path to SQLite database file
        engine: SQLAlchemy engine
        SessionLocal: Session factory
    """

    def __init__(self, db_path: Path | None = None):
        """Initialize conversation repository.

        Args:
            db_path: Path to database file (default: from settings)
        """
        self.db_path = db_path or settings.database_path
        self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Create tables if they don't exist
        self._init_db()

    def _init_db(self) -> None:
        """Create database tables if they don't exist."""
        Base.metadata.create_all(self.engine)
        logger.info(f"Initialized conversation database at {self.db_path}")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions.

        Yields:
            SQLAlchemy session

        Handles automatic commit/rollback and session cleanup.
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

    def create_conversation(self, conversation: ConversationCreate) -> ConversationResponse:
        """Create a new conversation.

        Args:
            conversation: Conversation creation data

        Returns:
            Created conversation with generated ID and timestamps
        """
        with self.get_session() as session:
            db_conversation = ConversationDB(
                title=conversation.title,
                status=ConversationStatus.ACTIVE,
            )
            session.add(db_conversation)
            session.flush()  # Generate ID and timestamps

            # Query message count (should be 0 for new conversation)
            message_count = session.query(func.count(ChatInteractionDB.id)).filter(
                ChatInteractionDB.conversation_id == db_conversation.id
            ).scalar() or 0

            return ConversationResponse(
                id=db_conversation.id,
                title=db_conversation.title,
                created_at=db_conversation.created_at,
                updated_at=db_conversation.updated_at,
                status=db_conversation.status,
                message_count=message_count,
            )

    def get_conversation(self, conversation_id: str) -> ConversationResponse | None:
        """Get a conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation if found, None otherwise
        """
        with self.get_session() as session:
            db_conversation = session.query(ConversationDB).filter(
                ConversationDB.id == conversation_id
            ).first()

            if not db_conversation:
                return None

            # Count messages
            message_count = session.query(func.count(ChatInteractionDB.id)).filter(
                ChatInteractionDB.conversation_id == conversation_id
            ).scalar() or 0

            return ConversationResponse(
                id=db_conversation.id,
                title=db_conversation.title,
                created_at=db_conversation.created_at,
                updated_at=db_conversation.updated_at,
                status=db_conversation.status,
                message_count=message_count,
            )

    def list_conversations(
        self,
        status: ConversationStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ConversationResponse]:
        """List conversations with pagination and filtering.

        Args:
            status: Filter by status (None = all statuses)
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip

        Returns:
            List of conversations ordered by updated_at (most recent first)
        """
        with self.get_session() as session:
            query = session.query(ConversationDB)

            # Filter by status if provided
            if status:
                query = query.filter(ConversationDB.status == status)

            # Order by most recently updated
            query = query.order_by(ConversationDB.updated_at.desc())

            # Apply pagination
            conversations = query.limit(limit).offset(offset).all()

            # Build responses with message counts
            results = []
            for conv in conversations:
                message_count = session.query(func.count(ChatInteractionDB.id)).filter(
                    ChatInteractionDB.conversation_id == conv.id
                ).scalar() or 0

                results.append(ConversationResponse(
                    id=conv.id,
                    title=conv.title,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    status=conv.status,
                    message_count=message_count,
                ))

            return results

    def get_conversation_with_messages(self, conversation_id: str) -> ConversationWithMessages | None:
        """Get a conversation with all its messages.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation with messages ordered by turn_number, or None if not found
        """
        with self.get_session() as session:
            db_conversation = session.query(ConversationDB).filter(
                ConversationDB.id == conversation_id
            ).first()

            if not db_conversation:
                return None

            # Get messages ordered by turn number
            messages = session.query(ChatInteractionDB).filter(
                ChatInteractionDB.conversation_id == conversation_id
            ).order_by(ChatInteractionDB.turn_number).all()

            # Convert to Pydantic models
            message_responses = []
            for msg in messages:
                # Parse sources JSON
                import json
                sources = json.loads(msg.sources) if msg.sources else []

                message_responses.append(ChatInteractionResponse(
                    id=msg.id,
                    query=msg.query,
                    response=msg.response,
                    sources=sources,
                    processing_time_ms=msg.processing_time_ms,
                    created_at=msg.created_at,
                    conversation_id=msg.conversation_id,
                    turn_number=msg.turn_number,
                ))

            return ConversationWithMessages(
                id=db_conversation.id,
                title=db_conversation.title,
                created_at=db_conversation.created_at,
                updated_at=db_conversation.updated_at,
                status=db_conversation.status,
                messages=message_responses,
            )

    def update_conversation(
        self,
        conversation_id: str,
        update: ConversationUpdate,
    ) -> ConversationResponse | None:
        """Update a conversation.

        Args:
            conversation_id: Conversation ID
            update: Fields to update

        Returns:
            Updated conversation if found, None otherwise
        """
        with self.get_session() as session:
            db_conversation = session.query(ConversationDB).filter(
                ConversationDB.id == conversation_id
            ).first()

            if not db_conversation:
                return None

            # Update fields if provided
            if update.title is not None:
                db_conversation.title = update.title
            if update.status is not None:
                db_conversation.status = update.status

            # Update timestamp
            db_conversation.updated_at = datetime.utcnow()

            session.flush()

            # Count messages
            message_count = session.query(func.count(ChatInteractionDB.id)).filter(
                ChatInteractionDB.conversation_id == conversation_id
            ).scalar() or 0

            return ConversationResponse(
                id=db_conversation.id,
                title=db_conversation.title,
                created_at=db_conversation.created_at,
                updated_at=db_conversation.updated_at,
                status=db_conversation.status,
                message_count=message_count,
            )

    def archive_conversation(self, conversation_id: str) -> ConversationResponse | None:
        """Archive a conversation (soft delete).

        Args:
            conversation_id: Conversation ID

        Returns:
            Archived conversation if found, None otherwise
        """
        return self.update_conversation(
            conversation_id,
            ConversationUpdate(status=ConversationStatus.ARCHIVED),
        )

    def delete_conversation(self, conversation_id: str) -> ConversationResponse | None:
        """Soft delete a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Deleted conversation if found, None otherwise
        """
        return self.update_conversation(
            conversation_id,
            ConversationUpdate(status=ConversationStatus.DELETED),
        )

    def close(self) -> None:
        """Close database engine and dispose of connections."""
        self.engine.dispose()
        logger.info("Closed conversation repository")
