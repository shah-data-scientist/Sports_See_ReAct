"""
FILE: test_verify_ground_truth.py
STATUS: Active
RESPONSIBILITY: Unit tests for ground truth verification functions with mocked sqlite3
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu
"""

import pytest
from unittest.mock import MagicMock, patch
from src.evaluation.verify_ground_truth import (
    normalize_value,
    compare_results,
    query_db,
    verify_answer_mentions_data,
)


class TestNormalizeValue:
    """Tests for normalize_value() function."""

    def test_normalize_float_value(self):
        """Test normalize_value rounds floats to 1 decimal place."""
        assert normalize_value(3.14159) == 3.1
        assert normalize_value(2.95) == 3.0
        assert normalize_value(0.0) == 0.0

    def test_normalize_non_float_value(self):
        """Test normalize_value returns non-floats unchanged."""
        assert normalize_value("LeBron James") == "LeBron James"
        assert normalize_value(42) == 42
        assert normalize_value(None) is None
        assert normalize_value([1, 2, 3]) == [1, 2, 3]


class TestCompareResults:
    """Tests for compare_results() function."""

    def test_compare_results_no_ground_truth(self):
        """Test compare_results with None ground truth (analysis queries)."""
        is_match, message, details = compare_results(None, [{"some": "data"}])

        assert is_match is True
        assert message == "No ground truth data (analysis query)"
        assert details["type"] == "analysis_only"

    def test_compare_results_sql_error(self):
        """Test compare_results with SQL execution error."""
        actual = [{"__error__": "syntax error near SELECT"}]
        is_match, message, details = compare_results({"name": "LeBron"}, actual)

        assert is_match is False
        assert "SQL error" in message
        assert details["error"] == "syntax error near SELECT"

    def test_compare_results_count_mismatch(self):
        """Test compare_results with different result counts."""
        expected = [{"name": "LeBron"}, {"name": "Curry"}]
        actual = [{"name": "LeBron"}]
        is_match, message, details = compare_results(expected, actual)

        assert is_match is False
        assert "Count mismatch" in message
        assert details["expected_count"] == 2
        assert details["actual_count"] == 1

    def test_compare_results_exact_match(self):
        """Test compare_results with exact match."""
        expected = [{"name": "LeBron", "pts": 27.2}]
        actual = [{"name": "LeBron", "pts": 27.2}]
        is_match, message, details = compare_results(expected, actual)

        assert is_match is True
        assert message == "Match"
        assert details["expected"] == expected
        assert details["actual"] == actual

    def test_compare_results_float_normalization(self):
        """Test compare_results normalizes float precision."""
        expected = [{"name": "Durant", "avg": 28.5}]
        actual = [{"name": "Durant", "avg": 28.49999}]
        is_match, message, details = compare_results(expected, actual)

        # Both normalize to 28.5, should match
        assert is_match is True
        assert message == "Match"


class TestQueryDb:
    """Tests for query_db() function with mocked sqlite3."""

    @patch("src.evaluation.verify_ground_truth.sqlite3.connect")
    def test_query_db_success(self, mock_connect):
        """Test query_db with mocked successful query execution."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock rows with Row factory
        mock_row_1 = {"name": "LeBron James", "pts": 27.2}
        mock_row_2 = {"name": "Stephen Curry", "pts": 25.5}
        mock_cursor.fetchall.return_value = [mock_row_1, mock_row_2]

        # Act
        result = query_db("SELECT name, pts FROM player_stats LIMIT 2")

        # Assert
        assert len(result) == 2
        assert result[0]["name"] == "LeBron James"
        assert result[1]["pts"] == 25.5
        mock_cursor.execute.assert_called_once_with("SELECT name, pts FROM player_stats LIMIT 2")
        mock_conn.close.assert_called_once()

    @patch("src.evaluation.verify_ground_truth.sqlite3.connect")
    def test_query_db_sql_error(self, mock_connect):
        """Test query_db with SQL execution error."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("syntax error")

        # Act
        result = query_db("SELECT INVALID SQL")

        # Assert
        assert len(result) == 1
        assert "__error__" in result[0]
        assert "syntax error" in result[0]["__error__"]
        mock_conn.close.assert_called_once()


class TestVerifyAnswerMentionsData:
    """Tests for verify_answer_mentions_data() function."""

    def test_verify_answer_no_data(self):
        """Test verify_answer_mentions_data with None data (analysis query)."""
        is_ok, message = verify_answer_mentions_data("Some answer text", None)

        assert is_ok is True
        assert "No specific data" in message

    def test_verify_answer_mentions_player(self):
        """Test verify_answer_mentions_data when answer mentions player name."""
        data = [{"name": "LeBron James", "pts": 27.2}]
        answer = "LeBron James is the top scorer with 27.2 points."
        is_ok, message = verify_answer_mentions_data(answer, data)

        assert is_ok is True
        assert "appropriately mentions" in message

    def test_verify_answer_missing_player(self):
        """Test verify_answer_mentions_data when answer missing player name."""
        data = [{"name": "Stephen Curry", "pts": 25.5}]
        answer = "The top scorer has 25.5 points."
        is_ok, message = verify_answer_mentions_data(answer, data)

        assert is_ok is False
        assert "not mentioned" in message
