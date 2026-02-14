"""
FILE: conversation.py
STATUS: Active
RESPONSIBILITY: SQLAlchemy ORM and Pydantic models for conversations
LAST MAJOR UPDATE: 2026-02-09
MAINTAINER: Shahu
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Enum as SQLEnum, String
from sqlalchemy.orm import relationship

from src.models.feedback import Base, ChatInteractionResponse


class ConversationStatus(str, Enum):
    """Conversation status enumeration."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


# SQLAlchemy Model
class ConversationDB(Base):
    """SQLAlchemy model for conversations."""

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False, index=True)

    # Relationship to messages
    messages = relationship("ChatInteractionDB", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatInteractionDB.turn_number")


# Pydantic Models for API
class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""

    title: str | None = Field(default=None, max_length=200, description="Conversation title (auto-generated if not provided)")


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""

    title: str | None = Field(default=None, max_length=200, description="New conversation title")
    status: ConversationStatus | None = Field(default=None, description="New conversation status")


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    status: ConversationStatus
    message_count: int = Field(default=0, description="Number of messages in conversation")

    model_config = {"from_attributes": True}


class ConversationWithMessages(BaseModel):
    """Schema for conversation with full message history."""

    id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    status: ConversationStatus
    messages: list[ChatInteractionResponse] = Field(default_factory=list, description="All messages in conversation")

    model_config = {"from_attributes": True}
