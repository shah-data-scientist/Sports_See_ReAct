"""
FILE: chat.py
STATUS: Active
RESPONSIBILITY: Pydantic models for chat requests, responses, and search results
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    """A single chat message.

    Attributes:
        role: Message author role (user or assistant)
        content: Message content
        timestamp: When the message was created
    """

    role: Literal["user", "assistant"] = Field(
        description="Role of the message author"
    )
    content: str = Field(
        min_length=1,
        max_length=50000,
        description="Message content",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp (UTC)",
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate and clean message content."""
        return v.strip()


class SearchResult(BaseModel):
    """A single search result from vector search.

    Attributes:
        text: The document chunk text
        score: Similarity score (0-100 percentage)
        source: Source document identifier
        metadata: Additional metadata
    """

    text: str = Field(description="Document chunk text")
    score: float = Field(ge=0, le=100, description="Similarity score (0-100%)")
    source: str = Field(description="Source document")
    metadata: dict[str, str | int | float] = Field(
        default_factory=dict,
        description="Additional metadata",
    )


class ChatRequest(BaseModel):
    """Request to the chat endpoint.

    Attributes:
        query: User's question
        k: Number of context documents to retrieve
        min_score: Minimum similarity score for context
        include_sources: Whether to include source references
        conversation_id: Optional conversation ID for context
        turn_number: Turn number in conversation
    """

    query: str = Field(
        min_length=1,
        max_length=2000,
        description="User's question",
        examples=["Who won the NBA championship in 2023?"],
    )
    k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of context documents to retrieve",
    )
    min_score: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Minimum similarity score (0-1) for context documents",
    )
    include_sources: bool = Field(
        default=True,
        description="Include source references in response",
    )
    conversation_id: str | None = Field(
        default=None,
        description="Conversation ID for context retrieval (optional)",
    )
    turn_number: int = Field(
        default=1,
        ge=1,
        description="Turn number in conversation",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and clean query."""
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty")
        return v


class Visualization(BaseModel):
    """Visualization data for statistical queries.

    Attributes:
        pattern: Detected visualization pattern (top_n, comparison, etc.)
        viz_type: Type of visualization (horizontal_bar, radar, scatter, etc.)
        plot_json: Plotly figure as JSON string (for programmatic use)
        plot_html: Plotly figure as HTML (for direct embedding)
    """

    pattern: str = Field(description="Detected query pattern")
    viz_type: str = Field(description="Type of visualization")
    plot_json: str = Field(description="Plotly figure as JSON")
    plot_html: str = Field(description="Plotly figure as HTML")


class ChatResponse(BaseModel):
    """Response from the chat endpoint.

    Attributes:
        answer: AI-generated response
        sources: List of source documents used
        query: Original query (for reference)
        processing_time_ms: Processing time in milliseconds
        conversation_id: Conversation ID
        turn_number: Turn number in conversation
        generated_sql: Generated SQL query (if applicable)
        visualization: Optional visualization for statistical queries
        reasoning_trace: ReAct agent reasoning steps (Thought/Action/Observation)
        tools_used: List of tools invoked by the agent
    """

    answer: str = Field(description="AI-generated response")
    sources: list[SearchResult] = Field(
        default_factory=list,
        description="Source documents used for context",
    )
    query: str = Field(description="Original query")
    processing_time_ms: float = Field(
        ge=0,
        description="Processing time in milliseconds",
    )
    model: str = Field(description="Model used for generation")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp (UTC)",
    )
    conversation_id: str | None = Field(
        default=None,
        description="Conversation ID",
    )
    turn_number: int = Field(
        default=1,
        description="Turn number in conversation",
    )
    generated_sql: str | None = Field(
        default=None,
        description="Generated SQL query (if SQL tool was used)",
    )
    visualization: Visualization | None = Field(
        default=None,
        description="Visualization data for statistical queries",
    )
    query_type: str | None = Field(
        default=None,
        description="Query routing type: statistical/contextual/hybrid/greeting/agent",
    )
    reasoning_trace: list[dict[str, Any]] = Field(
        default_factory=list,
        description="ReAct agent reasoning steps (Thought/Action/Observation)",
    )
    tools_used: list[str] = Field(
        default_factory=list,
        description="List of tools invoked by the agent",
    )

    model_config = {"json_schema_extra": {"example": {
        "answer": "The Denver Nuggets won the 2023 NBA Championship.",
        "sources": [
            {
                "text": "The Denver Nuggets defeated the Miami Heat...",
                "score": 92.5,
                "source": "nba_history.pdf",
                "metadata": {"page": 12},
            }
        ],
        "query": "Who won the NBA championship in 2023?",
        "processing_time_ms": 1250.5,
        "model": "mistral-small-latest",
        "timestamp": "2024-01-15T10:30:00Z",
    }}}


class HealthResponse(BaseModel):
    """Health check response.

    Attributes:
        status: Service status
        index_loaded: Whether vector index is loaded
        index_size: Number of vectors in index
        version: API version
    """

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        description="Service health status"
    )
    index_loaded: bool = Field(description="Whether vector index is loaded")
    index_size: int = Field(ge=0, description="Number of vectors in index")
    version: str = Field(default="1.0.0", description="API version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp (UTC)",
    )
