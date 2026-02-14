"""
FILE: test_quality_agent.py
STATUS: Active
RESPONSIBILITY: Unit tests for quality agent LLM-powered quality validation
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

from unittest.mock import MagicMock, patch

import pytest

from src.pipeline.models import QualityCheckResult


class TestChunkQualityAssessment:
    def test_assessment_model_valid(self):
        from src.pipeline.quality_agent import ChunkQualityAssessment

        assessment = ChunkQualityAssessment(
            is_coherent=True,
            quality_score=0.85,
            issues=[],
        )
        assert assessment.is_coherent is True
        assert assessment.quality_score == 0.85

    def test_assessment_model_with_issues(self):
        from src.pipeline.quality_agent import ChunkQualityAssessment

        assessment = ChunkQualityAssessment(
            is_coherent=False,
            quality_score=0.3,
            issues=["Truncated text", "Missing context"],
        )
        assert len(assessment.issues) == 2

    def test_quality_score_range_validation(self):
        from src.pipeline.quality_agent import ChunkQualityAssessment

        with pytest.raises(Exception):
            ChunkQualityAssessment(is_coherent=True, quality_score=1.5, issues=[])


class TestCheckChunkQuality:
    @patch("src.pipeline.quality_agent._build_quality_agent")
    def test_returns_quality_check_result(self, mock_build_agent):
        from src.pipeline.quality_agent import ChunkQualityAssessment

        mock_agent = MagicMock()
        mock_result = MagicMock()
        mock_result.output = ChunkQualityAssessment(
            is_coherent=True,
            quality_score=0.9,
            issues=[],
        )
        mock_agent.run_sync.return_value = mock_result
        mock_build_agent.return_value = mock_agent

        from src.pipeline.quality_agent import check_chunk_quality

        result = check_chunk_quality("chunk_1", "Some valid text content here.")

        assert isinstance(result, QualityCheckResult)
        assert result.chunk_id == "chunk_1"
        assert result.is_coherent is True
        assert result.quality_score == 0.9

    @patch("src.pipeline.quality_agent._build_quality_agent")
    def test_low_quality_chunk(self, mock_build_agent):
        from src.pipeline.quality_agent import ChunkQualityAssessment

        mock_agent = MagicMock()
        mock_result = MagicMock()
        mock_result.output = ChunkQualityAssessment(
            is_coherent=False,
            quality_score=0.2,
            issues=["Garbled content", "Encoding artifacts"],
        )
        mock_agent.run_sync.return_value = mock_result
        mock_build_agent.return_value = mock_agent

        from src.pipeline.quality_agent import check_chunk_quality

        result = check_chunk_quality("chunk_bad", "asdf jkl; NaN NaN broken text")

        assert result.is_coherent is False
        assert result.quality_score == 0.2
        assert len(result.issues) == 2
