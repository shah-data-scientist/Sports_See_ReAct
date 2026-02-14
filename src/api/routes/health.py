"""
FILE: health.py
STATUS: Active
RESPONSIBILITY: Health check endpoints (health, readiness, liveness)
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_chat_service
from src.models.chat import HealthResponse
from src.services.chat import ChatService

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check the health status of the API and vector index.",
)
async def health_check() -> HealthResponse:
    """Check API health status.

    Returns:
        HealthResponse with service status and index information
    """
    try:
        service = get_chat_service()
        is_loaded = service.is_ready
        index_size = service.vector_store.index_size if is_loaded else 0

        if is_loaded:
            status = "healthy"
        else:
            status = "degraded"

    except Exception:
        status = "unhealthy"
        is_loaded = False
        index_size = 0

    return HealthResponse(
        status=status,
        index_loaded=is_loaded,
        index_size=index_size,
    )


@router.get(
    "/ready",
    summary="Readiness Check",
    description="Check if the API is ready to serve requests.",
)
async def readiness_check() -> dict:
    """Check if API is ready to serve requests.

    Returns:
        Simple ready status
    """
    try:
        service = get_chat_service()
        ready = service.is_ready
    except Exception:
        ready = False

    return {"ready": ready}


@router.get(
    "/live",
    summary="Liveness Check",
    description="Check if the API is alive.",
)
async def liveness_check() -> dict:
    """Check if API is alive.

    Returns:
        Simple alive status
    """
    return {"alive": True}
