"""
FILE: quality_agent.py
STATUS: Active
RESPONSIBILITY: Pydantic AI Agent for LLM-powered data quality validation of document chunks
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

import logging

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from src.core.config import settings
from src.pipeline.models import QualityCheckResult

logger = logging.getLogger(__name__)


class ChunkQualityAssessment(BaseModel):
    """Structured output for chunk quality assessment."""

    is_coherent: bool = Field(description="Whether the chunk is coherent and readable")
    quality_score: float = Field(ge=0.0, le=1.0, description="Quality score 0-1")
    issues: list[str] = Field(default_factory=list, description="Quality issues found")


def _build_quality_agent() -> Agent[None, ChunkQualityAssessment]:
    """Build the quality validation agent.

    Returns:
        Configured Pydantic AI Agent for chunk quality assessment.
    """
    return Agent(
        f"mistral:{settings.chat_model}",
        output_type=ChunkQualityAssessment,
        instructions=(
            "You are a data quality validator for a knowledge base. "
            "Assess whether the given text chunk is coherent, readable, "
            "and contains meaningful content. Check for: truncated sentences, "
            "encoding artifacts, empty/meaningless content, mixed languages "
            "without context, and garbled table formatting. "
            "Score from 0.0 (unusable) to 1.0 (perfect quality)."
        ),
    )


def check_chunk_quality(chunk_id: str, chunk_text: str) -> QualityCheckResult:
    """Check quality of a single chunk using Pydantic AI Agent.

    Args:
        chunk_id: Identifier for the chunk.
        chunk_text: The text content to validate.

    Returns:
        QualityCheckResult with coherence assessment.
    """
    agent = _build_quality_agent()
    result = agent.run_sync(f"Assess the quality of this text chunk:\n\n{chunk_text}")
    assessment = result.output
    return QualityCheckResult(
        chunk_id=chunk_id,
        is_coherent=assessment.is_coherent,
        quality_score=assessment.quality_score,
        issues=assessment.issues,
    )
