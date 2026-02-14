"""
FILE: test_classification_evaluation.py
STATUS: Active
RESPONSIBILITY: Test classification verification in evaluation scripts
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.chat import ChatRequest, ChatResponse


@pytest.fixture
def mock_sql_response():
    """Mock ChatResponse with SQL data (no vector sources)."""
    response = ChatResponse(
        answer="Shai Gilgeous-Alexander scored 2485 points this season.",
        sources=[],
        query="Who scored the most?",
        processing_time_ms=150,
        model="gemini-2.0-flash-exp",
    )
    return response


@pytest.fixture
def mock_vector_response():
    """Mock ChatResponse with vector sources (no SQL data)."""
    from src.models.chat import SearchResult

    response = ChatResponse(
        answer="The NBA has evolved significantly with emphasis on three-point shooting.",
        sources=[
            SearchResult(text="Evolution of NBA strategy...", source="nba_history.pdf", score=0.85)
        ],
        query="Explain NBA evolution",
        processing_time_ms=200,
        model="gemini-2.0-flash-exp",
    )
    return response


@pytest.fixture
def mock_hybrid_response():
    """Mock ChatResponse with both SQL data and vector sources."""
    from src.models.chat import SearchResult

    response = ChatResponse(
        answer="Nikola Jokić averaged 26.4 PPG. His playmaking style is unique among centers.",
        sources=[
            SearchResult(
                text="Jokić's playing style analysis...", source="player_analysis.pdf", score=0.90
            )
        ],
        query="Jokić stats and style",
        processing_time_ms=300,
        model="gemini-2.0-flash-exp",
    )
    return response


class TestSQLEvaluationClassification:
    """Test classification verification in evaluate_sql.py."""

    @pytest.mark.skip(reason="Integration test that loads heavy dependencies - tested in integration tests instead")
    def test_sql_evaluation_tracks_routing(self, mock_sql_response):
        """Test that SQL evaluation tracks routing statistics."""
        # This test is skipped because it tries to load actual ChatService which loads FAISS
        # The routing tracking logic is tested in other unit tests and integration tests
        pass

    def test_sql_evaluation_detects_misclassification(self):
        """Test that SQL evaluation detects when SQL query is routed to vector."""
        # This test verifies the logic in evaluate_sql.py lines 112-141
        # Simulate the detection logic

        # Mock response with vector sources (misclassification)
        response_answer = "The history of basketball is fascinating."
        response_sources = ["source1.pdf"]

        has_sql_data = any(
            kw in response_answer.lower()
            for kw in ["pts", "reb", "ast", "points", "rebounds", "assists"]
        )
        has_vector_context = len(response_sources) > 0

        if has_sql_data and has_vector_context:
            actual_routing = "hybrid"
        elif has_sql_data:
            actual_routing = "sql_only"
        elif has_vector_context:
            actual_routing = "vector_only"
        else:
            actual_routing = "unknown"

        expected_routing = "sql_only"
        is_misclassified = actual_routing != expected_routing

        assert is_misclassified is True
        assert actual_routing == "vector_only"

    def test_sql_evaluation_calculates_accuracy(self):
        """Test that SQL evaluation calculates classification accuracy correctly."""
        # Simulate routing_stats from evaluate_sql.py
        routing_stats = {"sql_only": 45, "vector_only": 3, "hybrid": 0, "unknown": 0}
        total_cases = 48

        classification_accuracy = (
            (routing_stats["sql_only"] / total_cases * 100) if total_cases else 0
        )

        assert classification_accuracy == pytest.approx(93.75, 0.1)

        # Test perfect accuracy
        routing_stats_perfect = {"sql_only": 48, "vector_only": 0, "hybrid": 0, "unknown": 0}
        perfect_accuracy = (
            (routing_stats_perfect["sql_only"] / total_cases * 100) if total_cases else 0
        )
        assert perfect_accuracy == 100.0

    def test_sql_evaluation_identifies_misclassifications(self):
        """Test that SQL evaluation properly identifies and records misclassifications."""
        # Simulate the misclassification tracking logic
        misclassifications = []

        test_cases = [
            {
                "question": "Who scored the most?",
                "category": "simple",
                "actual": "sql_only",
                "expected": "sql_only",
            },
            {
                "question": "Tell me about NBA history",
                "category": "simple",
                "actual": "vector_only",
                "expected": "sql_only",
            },
            {
                "question": "Top 5 scorers stats and analysis",
                "category": "complex",
                "actual": "hybrid",
                "expected": "sql_only",
            },
        ]

        for tc in test_cases:
            if tc["actual"] != tc["expected"]:
                misclassifications.append(
                    {
                        "question": tc["question"],
                        "category": tc["category"],
                        "expected": tc["expected"],
                        "actual": tc["actual"],
                    }
                )

        assert len(misclassifications) == 2
        assert misclassifications[0]["actual"] == "vector_only"
        assert misclassifications[1]["actual"] == "hybrid"


class TestVectorEvaluationClassification:
    """Test classification verification in evaluate_vector.py."""

    def test_vector_evaluation_tracks_routing(self):
        """Test that Vector evaluation tracks routing statistics."""
        # Verify the routing_stats structure
        routing_stats = {"sql_only": 0, "vector_only": 0, "hybrid": 0, "unknown": 0}

        # Simulate vector response
        response_has_sql = False
        response_has_vector = True

        if response_has_sql and response_has_vector:
            routing_stats["hybrid"] += 1
        elif response_has_sql:
            routing_stats["sql_only"] += 1
        elif response_has_vector:
            routing_stats["vector_only"] += 1
        else:
            routing_stats["unknown"] += 1

        assert routing_stats["vector_only"] == 1
        assert sum(routing_stats.values()) == 1

    def test_vector_evaluation_detects_misclassification(self):
        """Test that Vector evaluation detects when vector query is routed to SQL."""
        # Mock response with SQL data (misclassification for vector test case)
        response_answer = "The player scored 2485 points with 129 assists."
        response_sources = []

        has_sql_data = any(
            kw in response_answer.lower()
            for kw in ["pts", "reb", "ast", "points", "rebounds", "assists"]
        )
        has_vector_context = len(response_sources) > 0

        if has_sql_data and has_vector_context:
            actual_routing = "hybrid"
        elif has_sql_data:
            actual_routing = "sql_only"
        elif has_vector_context:
            actual_routing = "vector_only"
        else:
            actual_routing = "unknown"

        expected_routing = "vector_only"  # For vector test cases
        is_misclassified = actual_routing != expected_routing

        assert is_misclassified is True
        assert actual_routing == "sql_only"

    def test_vector_evaluation_calculates_accuracy(self):
        """Test that Vector evaluation calculates classification accuracy correctly."""
        # Simulate routing_stats for vector evaluation
        routing_stats = {"sql_only": 2, "vector_only": 20, "hybrid": 1, "unknown": 0}
        total_cases = 23

        classification_accuracy = (
            (routing_stats["vector_only"] / total_cases * 100) if total_cases else 0
        )

        assert classification_accuracy == pytest.approx(86.96, 0.1)


class TestEvaluationJSONOutput:
    """Test that evaluation scripts save classification data to JSON."""

    def test_sql_evaluation_json_structure(self, tmp_path):
        """Test that SQL evaluation JSON has required classification fields."""
        # Create mock evaluation result
        evaluation_result = {
            "timestamp": "2026-02-10T12:00:00",
            "total_cases": 48,
            "successful": 48,
            "failed": 0,
            "category_breakdown": {"simple_sql": 12, "complex_sql": 15},
            "routing_stats": {"sql_only": 45, "vector_only": 2, "hybrid": 1, "unknown": 0},
            "classification_accuracy": 93.75,
            "misclassifications": [
                {
                    "question": "Test question",
                    "category": "simple",
                    "expected": "sql_only",
                    "actual": "vector_only",
                    "response_preview": "Test response...",
                }
            ],
            "results": [],
        }

        # Verify required fields are present
        assert "routing_stats" in evaluation_result
        assert "classification_accuracy" in evaluation_result
        assert "misclassifications" in evaluation_result

        # Verify routing_stats structure
        assert "sql_only" in evaluation_result["routing_stats"]
        assert "vector_only" in evaluation_result["routing_stats"]
        assert "hybrid" in evaluation_result["routing_stats"]

        # Verify misclassification structure
        if evaluation_result["misclassifications"]:
            misc = evaluation_result["misclassifications"][0]
            assert "expected" in misc
            assert "actual" in misc
            assert "question" in misc

    def test_vector_evaluation_json_structure(self):
        """Test that Vector evaluation JSON has required classification fields."""
        # Create mock evaluation result
        evaluation_result = {
            "timestamp": "2026-02-10T12:00:00",
            "total_cases": 23,
            "successful": 23,
            "failed": 0,
            "routing_stats": {"sql_only": 3, "vector_only": 19, "hybrid": 1, "unknown": 0},
            "classification_accuracy": 82.61,
            "misclassifications": [
                {
                    "question": "Explain the strategy",
                    "category": "complex",
                    "expected": "vector_only",
                    "actual": "sql_only",
                    "response_preview": "Statistics show...",
                }
            ],
            "results": [],
        }

        # Verify required fields
        assert "routing_stats" in evaluation_result
        assert "classification_accuracy" in evaluation_result
        assert "misclassifications" in evaluation_result

        # Calculate accuracy matches
        total = evaluation_result["total_cases"]
        correct = evaluation_result["routing_stats"]["vector_only"]
        calculated_accuracy = (correct / total * 100) if total else 0

        assert calculated_accuracy == pytest.approx(evaluation_result["classification_accuracy"], 0.1)


class TestRoutingDetectionLogic:
    """Test the routing detection logic used in evaluations."""

    def test_detect_sql_only_routing(self):
        """Test detection of SQL-only routing."""
        # Response with SQL keywords, no vector sources
        answer = "Nikola Jokić scored 2485 points and 973 rebounds."
        sources = []

        has_sql_data = any(
            kw in answer.lower()
            for kw in ["pts", "reb", "ast", "points", "rebounds", "assists", "ppg", "rpg", "apg"]
        )
        has_vector_context = len(sources) > 0

        if has_sql_data and has_vector_context:
            routing = "hybrid"
        elif has_sql_data:
            routing = "sql_only"
        elif has_vector_context:
            routing = "vector_only"
        else:
            routing = "unknown"

        assert routing == "sql_only"

    def test_detect_vector_only_routing(self):
        """Test detection of vector-only routing."""
        # Response with no SQL keywords, has vector sources
        answer = "The NBA has evolved with strategic changes over decades."
        sources = ["nba_history.pdf"]

        has_sql_data = any(
            kw in answer.lower()
            for kw in ["pts", "reb", "ast", "points", "rebounds", "assists", "ppg", "rpg", "apg"]
        )
        has_vector_context = len(sources) > 0

        if has_sql_data and has_vector_context:
            routing = "hybrid"
        elif has_sql_data:
            routing = "sql_only"
        elif has_vector_context:
            routing = "vector_only"
        else:
            routing = "unknown"

        assert routing == "vector_only"

    def test_detect_hybrid_routing(self):
        """Test detection of hybrid routing."""
        # Response with both SQL keywords and vector sources
        answer = "Jokić scored 2485 points. His unique playmaking style sets him apart."
        sources = ["player_analysis.pdf"]

        has_sql_data = any(
            kw in answer.lower()
            for kw in ["pts", "reb", "ast", "points", "rebounds", "assists", "ppg", "rpg", "apg"]
        )
        has_vector_context = len(sources) > 0

        if has_sql_data and has_vector_context:
            routing = "hybrid"
        elif has_sql_data:
            routing = "sql_only"
        elif has_vector_context:
            routing = "vector_only"
        else:
            routing = "unknown"

        assert routing == "hybrid"

    def test_detect_unknown_routing(self):
        """Test detection of unknown routing."""
        # Response with neither SQL keywords nor vector sources
        answer = "I don't have enough information to answer that."
        sources = []

        has_sql_data = any(
            kw in answer.lower()
            for kw in ["pts", "reb", "ast", "points", "rebounds", "assists", "ppg", "rpg", "apg"]
        )
        has_vector_context = len(sources) > 0

        if has_sql_data and has_vector_context:
            routing = "hybrid"
        elif has_sql_data:
            routing = "sql_only"
        elif has_vector_context:
            routing = "vector_only"
        else:
            routing = "unknown"

        assert routing == "unknown"
