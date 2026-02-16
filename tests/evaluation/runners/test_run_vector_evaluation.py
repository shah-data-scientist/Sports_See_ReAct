"""
FILE: test_run_vector_evaluation.py
STATUS: Active
RESPONSIBILITY: Tests for vector evaluation runner with API-only processing and checkpointing
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu

Tests the main evaluation entry point, checkpointing, and report generation.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from evaluation.runners.run_vector_evaluation import (
    _cleanup_checkpoint,
    _load_checkpoint,
    _retry_api_call,
    _save_checkpoint,
    generate_comprehensive_report,
)


class TestCheckpointManagement:
    """Tests for checkpoint save/load/cleanup functions."""

    def test_save_and_load_checkpoint(self, tmp_path):
        """Test saving and loading checkpoint."""
        checkpoint_path = tmp_path / "test.checkpoint.json"
        results = [
            {"question": "Q1", "success": True},
            {"question": "Q2", "success": True}
        ]

        _save_checkpoint(checkpoint_path, results, next_index=2, total_cases=10)

        # Verify file exists
        assert checkpoint_path.exists()

        # Load and verify
        loaded = _load_checkpoint(checkpoint_path)
        assert loaded is not None
        assert loaded["evaluated_count"] == 2
        assert loaded["next_index"] == 2
        assert loaded["total_cases"] == 10
        assert len(loaded["results"]) == 2

    def test_load_checkpoint_nonexistent(self, tmp_path):
        """Test loading checkpoint that doesn't exist."""
        checkpoint_path = tmp_path / "nonexistent.checkpoint.json"

        loaded = _load_checkpoint(checkpoint_path)
        assert loaded is None

    def test_load_checkpoint_corrupted(self, tmp_path):
        """Test loading corrupted checkpoint file."""
        checkpoint_path = tmp_path / "corrupted.checkpoint.json"
        checkpoint_path.write_text("invalid json {{{", encoding="utf-8")

        loaded = _load_checkpoint(checkpoint_path)
        assert loaded is None

    def test_cleanup_checkpoint(self, tmp_path):
        """Test checkpoint cleanup."""
        checkpoint_path = tmp_path / "test.checkpoint.json"
        checkpoint_path.write_text("{}", encoding="utf-8")

        assert checkpoint_path.exists()

        _cleanup_checkpoint(checkpoint_path)

        assert not checkpoint_path.exists()

    def test_cleanup_checkpoint_nonexistent(self, tmp_path):
        """Test cleanup when checkpoint doesn't exist."""
        checkpoint_path = tmp_path / "nonexistent.checkpoint.json"

        # Should not raise error
        _cleanup_checkpoint(checkpoint_path)

    def test_checkpoint_atomic_write(self, tmp_path):
        """Test checkpoint uses atomic write (temp file + rename)."""
        checkpoint_path = tmp_path / "test.checkpoint.json"
        temp_path = checkpoint_path.with_suffix(".tmp")

        results = [{"question": "Q1", "success": True}]
        _save_checkpoint(checkpoint_path, results, next_index=1, total_cases=5)

        # Verify final file exists
        assert checkpoint_path.exists()

        # Verify temp file cleaned up
        assert not temp_path.exists()

    def test_checkpoint_preserves_encoding(self, tmp_path):
        """Test checkpoint preserves UTF-8 encoding (e.g., 'Jokić')."""
        checkpoint_path = tmp_path / "test.checkpoint.json"
        results = [{"question": "Who is Nikola Jokić?", "success": True}]

        _save_checkpoint(checkpoint_path, results, next_index=1, total_cases=1)

        loaded = _load_checkpoint(checkpoint_path)
        assert "Jokić" in loaded["results"][0]["question"]


class TestRetryLogic:
    """Tests for API retry logic."""

    def test_retry_api_call_success_first_attempt(self):
        """Test successful API call on first attempt."""
        mock_func = MagicMock(return_value={"answer": "Test"})

        result = _retry_api_call(mock_func, max_retries=3)

        assert result == {"answer": "Test"}
        assert mock_func.call_count == 1

    def test_retry_api_call_429_then_success(self):
        """Test retry after 429 rate limit error."""
        mock_func = MagicMock()
        mock_func.side_effect = [
            RuntimeError("429 RESOURCE_EXHAUSTED rate limit"),
            {"answer": "Success"}
        ]

        with patch("time.sleep"):  # Mock sleep to speed up test
            result = _retry_api_call(mock_func, max_retries=3)

        assert result == {"answer": "Success"}
        assert mock_func.call_count == 2

    def test_retry_api_call_exhausted_retries(self):
        """Test all retries exhausted."""
        mock_func = MagicMock(side_effect=RuntimeError("429 rate limit"))

        with patch("time.sleep"):
            with pytest.raises(RuntimeError, match="429 rate limit"):
                _retry_api_call(mock_func, max_retries=2)

        # Should try initial + 2 retries = 3 attempts
        assert mock_func.call_count == 3

    def test_retry_api_call_non_retryable_error(self):
        """Test non-retryable error (not 429) fails immediately."""
        mock_func = MagicMock(side_effect=RuntimeError("500 Internal Server Error"))

        with pytest.raises(RuntimeError, match="500"):
            _retry_api_call(mock_func, max_retries=3)

        # Should NOT retry
        assert mock_func.call_count == 1


class TestReportGeneration:
    """Tests for comprehensive report generation."""

    def test_generate_comprehensive_report_basic(self, tmp_path):
        """Test report generation with basic results."""
        results = [
            {
                "question": "Test question",
                "category": "simple",
                "response": "Test response",
                "sources": [{"text": "source text", "score": 85, "source": "doc.pdf"}],
                "sources_count": 1,
                "processing_time_ms": 1000,
                "ground_truth": "Test ground truth",
                "success": True,
                "ragas_metrics": {
                    "faithfulness": 0.9,
                    "answer_relevancy": 0.85,
                    "context_precision": 0.8,
                    "context_recall": 0.75
                }
            }
        ]

        json_path = str(tmp_path / "results.json")
        timestamp = "20260211_120000"

        # Temporarily change output dir to tmp_path
        with patch("src.evaluation.runners.run_vector_evaluation.Path") as mock_path:
            mock_path.return_value = tmp_path
            report_path = generate_comprehensive_report(results, json_path, timestamp)

        # Verify report file created
        assert Path(report_path).exists()

        # Verify report content
        report_content = Path(report_path).read_text(encoding="utf-8")
        assert "Vector Evaluation Report" in report_content
        assert "Executive Summary" in report_content
        assert "RAGAS Metrics Analysis" in report_content

    def test_generate_comprehensive_report_with_failures(self, tmp_path):
        """Test report generation includes failure analysis."""
        results = [
            {
                "question": "Success query",
                "category": "simple",
                "success": True,
                "response": "Answer",
                "sources": [],
                "sources_count": 0,
                "processing_time_ms": 1000
            },
            {
                "question": "Failed query",
                "category": "complex",
                "success": False,
                "error": "API timeout"
            }
        ]

        json_path = str(tmp_path / "results.json")
        timestamp = "20260211_120000"

        with patch("src.evaluation.runners.run_vector_evaluation.Path") as mock_path:
            mock_path.return_value = tmp_path
            report_path = generate_comprehensive_report(results, json_path, timestamp)

        report_content = Path(report_path).read_text(encoding="utf-8")
        assert "Failure Analysis" in report_content
        assert "Failed query" in report_content

    def test_generate_comprehensive_report_all_sections_present(self, tmp_path):
        """Test report includes all analysis sections."""
        results = [
            {
                "question": "Q",
                "category": "simple",
                "success": True,
                "response": "A",
                "sources": [{"text": "T", "score": 80, "source": "doc.pdf"}],
                "sources_count": 1,
                "processing_time_ms": 1000,
                "ragas_metrics": {
                    "faithfulness": 0.8,
                    "answer_relevancy": 0.75,
                    "context_precision": 0.7,
                    "context_recall": 0.65
                }
            }
        ]

        json_path = str(tmp_path / "results.json")
        timestamp = "20260211_120000"

        with patch("src.evaluation.runners.run_vector_evaluation.Path") as mock_path:
            mock_path.return_value = tmp_path
            report_path = generate_comprehensive_report(results, json_path, timestamp)

        report_content = Path(report_path).read_text(encoding="utf-8")

        # Verify all major sections
        assert "Executive Summary" in report_content
        assert "RAGAS Metrics Analysis" in report_content
        assert "Source Quality Analysis" in report_content
        assert "Response Quality Analysis" in report_content
        assert "Retrieval Performance Analysis" in report_content
        assert "Category Performance Analysis" in report_content
        assert "Key Findings" in report_content

    def test_generate_comprehensive_report_handles_no_ragas(self, tmp_path):
        """Test report generation when no RAGAS metrics available."""
        results = [
            {
                "question": "Q",
                "category": "simple",
                "success": True,
                "response": "A",
                "sources": [],
                "sources_count": 0,
                "processing_time_ms": 1000
                # No ragas_metrics
            }
        ]

        json_path = str(tmp_path / "results.json")
        timestamp = "20260211_120000"

        with patch("src.evaluation.runners.run_vector_evaluation.Path") as mock_path:
            mock_path.return_value = tmp_path
            # Should not raise error
            report_path = generate_comprehensive_report(results, json_path, timestamp)

        assert Path(report_path).exists()

    def test_generate_comprehensive_report_category_breakdown(self, tmp_path):
        """Test report includes category performance breakdown."""
        results = [
            {
                "question": "Q1",
                "category": "simple",
                "success": True,
                "response": "A",
                "sources": [],
                "sources_count": 0,
                "processing_time_ms": 1000,
                "ragas_metrics": {"faithfulness": 0.9, "answer_relevancy": 0.85, "context_precision": 0.8, "context_recall": 0.75}
            },
            {
                "question": "Q2",
                "category": "complex",
                "success": True,
                "response": "A",
                "sources": [],
                "sources_count": 0,
                "processing_time_ms": 1500,
                "ragas_metrics": {"faithfulness": 0.7, "answer_relevancy": 0.65, "context_precision": 0.6, "context_recall": 0.55}
            }
        ]

        json_path = str(tmp_path / "results.json")
        timestamp = "20260211_120000"

        with patch("src.evaluation.runners.run_vector_evaluation.Path") as mock_path:
            mock_path.return_value = tmp_path
            report_path = generate_comprehensive_report(results, json_path, timestamp)

        report_content = Path(report_path).read_text(encoding="utf-8")
        assert "simple" in report_content
        assert "complex" in report_content

    def test_generate_comprehensive_report_markdown_format(self, tmp_path):
        """Test report uses valid markdown format."""
        results = [
            {
                "question": "Q",
                "category": "simple",
                "success": True,
                "response": "A",
                "sources": [],
                "sources_count": 0,
                "processing_time_ms": 1000
            }
        ]

        json_path = str(tmp_path / "results.json")
        timestamp = "20260211_120000"

        with patch("src.evaluation.runners.run_vector_evaluation.Path") as mock_path:
            mock_path.return_value = tmp_path
            report_path = generate_comprehensive_report(results, json_path, timestamp)

        report_content = Path(report_path).read_text(encoding="utf-8")

        # Check markdown structure
        assert report_content.startswith("# Vector Evaluation Report")
        assert "##" in report_content  # Has headers
        assert "|" in report_content   # Has tables
        assert "**" in report_content  # Has bold text
        assert "---" in report_content # Has dividers
