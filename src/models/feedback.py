"""
FILE: feedback.py
STATUS: Active
RESPONSIBILITY: SQLAlchemy ORM and Pydantic models for feedback and chat interactions
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class FeedbackRating(str, Enum):
    """Feedback rating enumeration."""

    POSITIVE = "positive"
    NEGATIVE = "negative"


# SQLAlchemy Models
class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


class ChatInteractionDB(Base):
    """SQLAlchemy model for chat interactions."""

    __tablename__ = "chat_interactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON-serialized list of sources
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Conversation fields (Phase 1: Conversation History)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True)
    turn_number = Column(Integer, nullable=True)

    # Relationships
    feedback = relationship("FeedbackDB", back_populates="interaction", uselist=False)
    conversation = relationship("ConversationDB", back_populates="messages")


class FeedbackDB(Base):
    """SQLAlchemy model for feedback."""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interaction_id = Column(String(36), ForeignKey("chat_interactions.id"), nullable=False)
    rating = Column(SQLEnum(FeedbackRating), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to interaction
    interaction = relationship("ChatInteractionDB", back_populates="feedback")


# Pydantic Models for API
class ChatInteractionCreate(BaseModel):
    """Schema for creating a chat interaction."""

    query: str = Field(..., min_length=1, max_length=10000)
    response: str = Field(..., min_length=1)
    sources: list[str] = Field(default_factory=list)
    processing_time_ms: int | None = None
    conversation_id: str | None = Field(default=None, description="Conversation ID (optional)")
    turn_number: int | None = Field(default=None, description="Turn number in conversation")


class ChatInteractionResponse(BaseModel):
    """Schema for chat interaction response."""

    id: str
    query: str
    response: str
    sources: list[str]
    processing_time_ms: int | None
    created_at: datetime
    conversation_id: str | None = None
    turn_number: int | None = None
    feedback: Optional["FeedbackResponse"] = None

    model_config = {"from_attributes": True}


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""

    interaction_id: str = Field(..., description="ID of the chat interaction")
    rating: FeedbackRating = Field(..., description="Positive or negative rating")
    comment: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional comment (encouraged for negative feedback)",
    )


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""

    id: int
    interaction_id: str
    rating: FeedbackRating
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackStats(BaseModel):
    """Schema for feedback statistics."""

    total_interactions: int
    total_feedback: int
    positive_count: int
    negative_count: int
    feedback_rate: float = Field(description="Percentage of interactions with feedback")
    positive_rate: float = Field(description="Percentage of positive feedback")


# Update forward reference
ChatInteractionResponse.model_rebuild()
