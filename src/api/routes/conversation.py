"""
FILE: conversation.py
STATUS: Active
RESPONSIBILITY: Conversation API endpoints for managing chat conversations
LAST MAJOR UPDATE: 2026-02-09
MAINTAINER: Shahu
"""

import logging

from fastapi import APIRouter, HTTPException, Query, status

from src.models.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationStatus,
    ConversationUpdate,
    ConversationWithMessages,
)
from src.repositories.conversation import ConversationRepository
from src.services.conversation import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_conversation_service() -> ConversationService:
    """Get conversation service instance."""
    repository = ConversationRepository()
    return ConversationService(repository=repository)


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create conversation",
    description="Create a new conversation. Title is optional and can be auto-generated from first message.",
)
async def create_conversation(conversation: ConversationCreate) -> ConversationResponse:
    """Create a new conversation."""
    service = get_conversation_service()
    return service.start_conversation(title=conversation.title)


@router.get(
    "",
    response_model=list[ConversationResponse],
    summary="List conversations",
    description="List conversations with pagination and optional status filtering. "
    "Returns conversations ordered by updated_at (most recent first).",
)
async def list_conversations(
    status_filter: ConversationStatus | None = Query(
        None,
        alias="status",
        description="Filter by conversation status",
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Maximum number of conversations to return",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of conversations to skip",
    ),
) -> list[ConversationResponse]:
    """List conversations with pagination."""
    service = get_conversation_service()
    return service.list_conversations(status=status_filter, limit=limit, offset=offset)


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation",
    description="Get a conversation by ID (metadata only, without messages).",
)
async def get_conversation(conversation_id: str) -> ConversationResponse:
    """Get a conversation by ID."""
    service = get_conversation_service()
    conversation = service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    return conversation


@router.get(
    "/{conversation_id}/messages",
    response_model=ConversationWithMessages,
    summary="Get conversation with messages",
    description="Get a conversation with all its messages ordered by turn number.",
)
async def get_conversation_messages(conversation_id: str) -> ConversationWithMessages:
    """Get conversation with all messages."""
    service = get_conversation_service()
    conversation = service.get_conversation_history(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    return conversation


@router.put(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Update conversation",
    description="Update conversation metadata (title and/or status).",
)
async def update_conversation(
    conversation_id: str,
    update: ConversationUpdate,
) -> ConversationResponse:
    """Update a conversation."""
    service = get_conversation_service()

    # Validate that at least one field is being updated
    if update.title is None and update.status is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field (title or status) must be provided",
        )

    conversation = service.repository.update_conversation(conversation_id, update)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    return conversation


@router.delete(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Delete conversation",
    description="Soft delete a conversation by setting status to 'deleted'. "
    "This operation does not permanently delete data.",
)
async def delete_conversation(conversation_id: str) -> ConversationResponse:
    """Delete a conversation (soft delete)."""
    service = get_conversation_service()
    conversation = service.delete(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    return conversation
