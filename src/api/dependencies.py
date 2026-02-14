"""
FILE: dependencies.py
STATUS: Active
RESPONSIBILITY: API dependency injection for service instances
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

from src.services.chat import ChatService

# Global service instance (initialized on startup)
_chat_service: ChatService | None = None


def set_chat_service(service: ChatService | None) -> None:
    """Set the chat service instance.

    Args:
        service: ChatService instance or None to clear
    """
    global _chat_service
    _chat_service = service


def get_chat_service() -> ChatService:
    """Get the chat service instance.

    Returns:
        Initialized ChatService

    Raises:
        RuntimeError: If service not initialized
    """
    if _chat_service is None:
        raise RuntimeError("Chat service not initialized")
    return _chat_service
