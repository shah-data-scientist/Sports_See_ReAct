"""
FILE: feedback.py
STATUS: Active
RESPONSIBILITY: Feedback API endpoints for submitting and querying feedback
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

import logging

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from src.models.feedback import (
    ChatInteractionResponse,
    FeedbackCreate,
    FeedbackRating,
    FeedbackResponse,
    FeedbackStats,
)
from src.services.feedback import get_feedback_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback")


class LogInteractionRequest(BaseModel):
    """Request model for logging a chat interaction."""

    query: str
    response: str
    sources: list[str]
    processing_time_ms: int


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback",
    description="Submit positive or negative feedback for a chat interaction. "
    "Comments are optional but encouraged for negative feedback.",
)
async def submit_feedback(feedback: FeedbackCreate) -> FeedbackResponse:
    """Submit feedback for a chat interaction."""
    service = get_feedback_service()
    try:
        return service.submit_feedback(
            interaction_id=feedback.interaction_id,
            rating=feedback.rating,
            comment=feedback.comment,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{interaction_id}",
    response_model=FeedbackResponse,
    summary="Update feedback",
    description="Update existing feedback for an interaction.",
)
async def update_feedback(
    interaction_id: str,
    rating: FeedbackRating,
    comment: str | None = None,
) -> FeedbackResponse:
    """Update feedback for a chat interaction."""
    service = get_feedback_service()
    result = service.update_feedback(interaction_id, rating, comment)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback for interaction {interaction_id} not found",
        )
    return result


@router.get(
    "/stats",
    response_model=FeedbackStats,
    summary="Get feedback statistics",
    description="Get aggregated statistics about feedback.",
)
async def get_stats() -> FeedbackStats:
    """Get feedback statistics."""
    service = get_feedback_service()
    return service.get_stats()


@router.get(
    "/negative",
    response_model=list[ChatInteractionResponse],
    summary="Get negative feedback with comments",
    description="Get all interactions that received negative feedback with comments.",
)
async def get_negative_feedback() -> list[ChatInteractionResponse]:
    """Get negative feedback with comments for review."""
    service = get_feedback_service()
    return service.get_negative_feedback_with_comments()


@router.get(
    "/interactions",
    response_model=list[ChatInteractionResponse],
    summary="Get recent interactions",
    description="Get recent chat interactions with optional pagination.",
)
async def get_interactions(
    limit: int = Query(default=50, ge=1, le=100, description="Max results"),
    offset: int = Query(default=0, ge=0, description="Results to skip"),
) -> list[ChatInteractionResponse]:
    """Get recent chat interactions."""
    service = get_feedback_service()
    return service.get_recent_interactions(limit=limit, offset=offset)


@router.get(
    "/interactions/{interaction_id}",
    response_model=ChatInteractionResponse,
    summary="Get interaction by ID",
    description="Get a specific chat interaction by its ID.",
)
async def get_interaction(interaction_id: str) -> ChatInteractionResponse:
    """Get a specific chat interaction."""
    service = get_feedback_service()
    result = service.get_interaction(interaction_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction {interaction_id} not found",
        )
    return result


@router.post(
    "/log-interaction",
    response_model=ChatInteractionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log chat interaction",
    description="Log a chat interaction to the database for tracking and feedback.",
)
async def log_interaction(request: LogInteractionRequest) -> ChatInteractionResponse:
    """Log a chat interaction to the database.

    Args:
        request: LogInteractionRequest with query, response, sources, processing_time_ms

    Returns:
        ChatInteractionResponse with the logged interaction
    """
    service = get_feedback_service()
    try:
        return service.log_interaction(
            query=request.query,
            response=request.response,
            sources=request.sources,
            processing_time_ms=request.processing_time_ms,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
