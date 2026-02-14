"""
FILE: main.py
STATUS: Active
RESPONSIBILITY: FastAPI application factory with middleware, CORS, and exception handlers
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

# CRITICAL: Set before any imports to prevent FAISS + torch OpenMP conflict
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.dependencies import get_chat_service, set_chat_service
from src.api.routes import chat, conversation, feedback, health
from src.core.config import settings
from src.core.exceptions import (
    AppException,
    IndexNotFoundError,
    RateLimitError,
    ValidationError,
)
from src.services.chat import ChatService

logger = logging.getLogger(__name__)

# Configure logging to ensure application logs are visible
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s',
    force=True  # Override any existing configuration
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Initializes services on startup and cleans up on shutdown.
    """
    logger.info("Starting up application...")

    # Initialize chat service (enable_vector_fallback defaults to True)
    service = ChatService()
    set_chat_service(service)

    # Try to load index
    try:
        service.ensure_ready()
        logger.info("Vector index loaded successfully")
    except IndexNotFoundError:
        logger.warning("Vector index not found - run indexer first")

    yield

    # Cleanup
    logger.info("Shutting down application...")
    set_chat_service(None)


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=settings.app_title,
        description="NBA RAG Assistant API - Get answers about NBA using AI",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request timing middleware
    @app.middleware("http")
    async def add_timing_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        return response

    # Exception handlers
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=exc.to_dict(),
        )

    @app.exception_handler(IndexNotFoundError)
    async def index_not_found_handler(request: Request, exc: IndexNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=exc.to_dict(),
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_handler(request: Request, exc: RateLimitError):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=exc.to_dict(),
            headers={"Retry-After": str(exc.retry_after)},
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=exc.to_dict(),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                }
            },
        )

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
    app.include_router(conversation.router, prefix="/api/v1", tags=["Conversations"])
    app.include_router(feedback.router, prefix="/api/v1", tags=["Feedback"])

    return app


# Create default app instance
app = create_app()
