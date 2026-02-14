"""
FILE: test_run_sql_evaluation.py
STATUS: Active
RESPONSIBILITY: Tests for consolidated SQL evaluation runner
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.evaluation.runners.run_sql_evaluation import (
    generate_comprehensive_report,
    run_sql_evaluation,
)


class TestRunSQLEvaluation:
    """Tests for SQL evaluation runner."""

    @patch("src.evaluation.runners.run_sql_evaluation.TestClient")
    def test_run_sql_evaluation_basic(self, mock_test_client):
        """Test basic evaluation run."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "Test answer",
            "sources": [],
            "processing_time_ms": 100.0,
            "generated_sql": "SELECT * FROM test"
        }

        # Configure client instance
        mock_client_instance = mock_test_client.return_value
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.post.return_value = mock_response

        # Mock SQL_TEST_CASES to have just 1 test
        with patch("src.evaluation.runners.run_sql_evaluation.SQL_TEST_CASES", [
            MagicMock(
                question="Test question?",
                category="test",
                query_type=MagicMock(value="sql_only")
            )
        ]):
            with patch("src.evaluation.runners.run_sql_evaluation.time.sleep"):
                results, json_path = run_sql_evaluation()

        assert len(results) == 1
        assert results[0]["question"] == "Test question?"
        assert results[0]["success"] is True
        assert Path(json_path).exists()

        # Cleanup
        Path(json_path).unlink()

    def test_generate_comprehensive_report(self, tmp_path):
        """Test report generation."""
        results = [
            {
                "question": "Test question 1?",
                "category": "test",
                "response": "Test answer 1",
                "expected_routing": "sql_only",
                "actual_routing": "sql_only",
                "is_misclassified": False,
                "sources_count": 0,
                "processing_time_ms": 100.0,
                "generated_sql": "SELECT * FROM test",
                "success": True
            },
            {
                "question": "Test question 2?",
                "category": "test",
                "response": "Test answer 2",
                "expected_routing": "sql_only",
                "actual_routing": "fallback_to_vector",
                "is_misclassified": True,
                "sources_count": 3,
                "processing_time_ms": 150.0,
                "generated_sql": None,
                "success": True
            }
        ]

        json_path = "test.json"

        with patch("src.evaluation.runners.run_sql_evaluation.Path") as mock_path:
            mock_report_path = tmp_path / "report.md"
            mock_path.return_value = tmp_path
            mock_path.__truediv__ = lambda self, other: tmp_path / other

            # Mock open to write to tmp_path
            with patch("builtins.open", create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file

                report_path = generate_comprehensive_report(results, json_path)

                # Verify write was called
                assert mock_file.write.called
                # Check that key sections are present in report
                written_content = "".join([call[0][0] for call in mock_file.write.call_args_list])
                assert "SQL Evaluation Report" in written_content
                assert "Executive Summary" in written_content
                assert "Response Quality Analysis" in written_content
                assert "Query Quality Analysis" in written_content
                assert "Key Findings" in written_content
                assert "Detailed Test Results" in written_content

    def test_generate_report_handles_failures(self):
        """Test report handles execution failures."""
        results = [
            {
                "question": "Failed question?",
                "category": "test",
                "response": "",
                "expected_routing": "sql_only",
                "actual_routing": "error",
                "is_misclassified": True,
                "sources_count": 0,
                "processing_time_ms": 0.0,
                "generated_sql": None,
                "success": False,
                "error": "Test error message"
            }
        ]

        json_path = "test.json"

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            with patch("src.evaluation.runners.run_sql_evaluation.Path"):
                report_path = generate_comprehensive_report(results, json_path)

                written_content = "".join([call[0][0] for call in mock_file.write.call_args_list])
                assert "Execution Failures" in written_content
                assert "Test error message" in written_content

    def test_generate_report_handles_misclassifications(self):
        """Test report handles routing misclassifications."""
        results = [
            {
                "question": "Misclassified question?",
                "category": "test",
                "response": "Some answer",
                "expected_routing": "sql_only",
                "actual_routing": "fallback_to_vector",
                "is_misclassified": True,
                "sources_count": 2,
                "processing_time_ms": 120.0,
                "generated_sql": None,
                "success": True
            }
        ]

        json_path = "test.json"

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            with patch("src.evaluation.runners.run_sql_evaluation.Path"):
                report_path = generate_comprehensive_report(results, json_path)

                written_content = "".join([call[0][0] for call in mock_file.write.call_args_list])
                assert "Routing Misclassifications" in written_content
                assert "fallback_to_vector" in written_content

    def test_report_includes_all_quality_metrics(self):
        """Test report includes all quality analysis sections."""
        results = [
            {
                "question": "Test question?",
                "category": "test",
                "response": "Test answer",
                "expected_routing": "sql_only",
                "actual_routing": "sql_only",
                "is_misclassified": False,
                "sources_count": 0,
                "processing_time_ms": 100.0,
                "generated_sql": "SELECT name FROM players LIMIT 10",
                "success": True
            }
        ]

        json_path = "test.json"

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            with patch("src.evaluation.runners.run_sql_evaluation.Path"):
                report_path = generate_comprehensive_report(results, json_path)

                written_content = "".join([call[0][0] for call in mock_file.write.call_args_list])

                # Check all analysis sections are present
                assert "Error Taxonomy" in written_content
                assert "Fallback Patterns" in written_content
                assert "Response Quality Metrics" in written_content
                assert "Query Structure" in written_content
                assert "Query Complexity" in written_content
                assert "Column Selection" in written_content

    def test_report_has_no_phase_terminology(self):
        """Test report does not use Phase 1 or Phase 2 terminology."""
        results = [
            {
                "question": "Test?",
                "category": "test",
                "response": "Answer",
                "expected_routing": "sql_only",
                "actual_routing": "sql_only",
                "is_misclassified": False,
                "sources_count": 0,
                "processing_time_ms": 100.0,
                "generated_sql": "SELECT * FROM test",
                "success": True
            }
        ]

        json_path = "test.json"

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            with patch("src.evaluation.runners.run_sql_evaluation.Path"):
                report_path = generate_comprehensive_report(results, json_path)

                written_content = "".join([call[0][0] for call in mock_file.write.call_args_list])

                # Verify no phase terminology
                assert "Phase 1" not in written_content
                assert "Phase 2" not in written_content
                assert "phase 1" not in written_content
                assert "phase 2" not in written_content

    def test_report_lists_output_files(self):
        """Test report clearly states it produces 2 files."""
        results = [
            {
                "question": "Test?",
                "category": "test",
                "response": "Answer",
                "expected_routing": "sql_only",
                "actual_routing": "sql_only",
                "is_misclassified": False,
                "sources_count": 0,
                "processing_time_ms": 100.0,
                "generated_sql": None,
                "success": True
            }
        ]

        json_path = "evaluation_results/sql_evaluation_20260211_123456.json"

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            with patch("src.evaluation.runners.run_sql_evaluation.Path"):
                report_path = generate_comprehensive_report(results, json_path)

                written_content = "".join([call[0][0] for call in mock_file.write.call_args_list])

                # Report should reference the JSON file
                assert json_path in written_content or "sql_evaluation_" in written_content
