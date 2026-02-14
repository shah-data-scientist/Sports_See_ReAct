"""
FILE: test_evaluation_integration.py
STATUS: Active
RESPONSIBILITY: Integration tests for complete evaluation system flow
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.chat import ChatRequest, ChatResponse, SearchResult


@pytest.fixture
def mock_chat_service():
    """Mock ChatService for integration tests."""
    service = MagicMock()
    service.ensure_ready = MagicMock()
    return service


@pytest.fixture
def mock_conversation_service():
    """Mock ConversationService for integration tests."""
    service = MagicMock()
    mock_conversation = MagicMock()
    mock_conversation.id = "test-conversation-id"
    service.start_conversation.return_value = mock_conversation
    return service


@pytest.fixture
def sample_sql_test_cases():
    """Sample SQL test cases for integration testing."""
    from src.evaluation.models.sql_models import QueryType, SQLEvaluationTestCase

    return [
        SQLEvaluationTestCase(
            question="Who scored the most points?",
            query_type=QueryType.SQL_ONLY,
            expected_sql="SELECT p.name, ps.pts FROM players p JOIN player_stats ps",
            ground_truth_answer="Shai Gilgeous-Alexander scored 2485 points.",
            ground_truth_data={"name": "Shai Gilgeous-Alexander", "pts": 2485},
            category="simple_sql",
        ),
        SQLEvaluationTestCase(
            question="Top 3 rebounders?",
            query_type=QueryType.SQL_ONLY,
            expected_sql="SELECT p.name, ps.reb FROM players p JOIN player_stats ps ORDER BY ps.reb DESC LIMIT 3",
            ground_truth_answer="Top rebounders: Zubac, Sabonis, Towns.",
            ground_truth_data=[
                {"name": "Ivica Zubac", "reb": 1008},
                {"name": "Domantas Sabonis", "reb": 973},
            ],
            category="simple_sql",
        ),
        SQLEvaluationTestCase(
            question="gimme top assists plz",
            query_type=QueryType.SQL_ONLY,
            expected_sql="SELECT p.name, ps.ast FROM players p JOIN player_stats ps ORDER BY ps.ast DESC",
            ground_truth_answer="Top assists leaders.",
            category="noisy_sql",
        ),
    ]


@pytest.fixture
def sample_vector_test_cases():
    """Sample Vector test cases for integration testing."""
    from src.evaluation.models.vector_models import EvaluationTestCase, TestCategory

    return [
        EvaluationTestCase(
            question="Why is three-point shooting important in modern NBA?",
            ground_truth="Three-point shooting has become crucial due to strategic evolution.",
            category=TestCategory.COMPLEX,
        ),
        EvaluationTestCase(
            question="Explain the evolution of defensive strategies.",
            ground_truth="Defensive strategies have evolved with emphasis on switching.",
            category=TestCategory.COMPLEX,
        ),
        EvaluationTestCase(
            question="gimme some nba history plz",
            ground_truth="NBA history spans decades of evolution.",
            category=TestCategory.NOISY,
        ),
    ]


@pytest.fixture
def sample_hybrid_test_cases():
    """Sample Hybrid test cases for integration testing."""
    from src.evaluation.models.vector_models import EvaluationTestCase, TestCategory

    return [
        EvaluationTestCase(
            question="Compare Jokić and Embiid statistics and explain their playing styles.",
            ground_truth="Requires both statistics from DB and contextual analysis of styles.",
            category=TestCategory.COMPLEX,
        ),
        EvaluationTestCase(
            question="Who are the most efficient scorers and why are they effective?",
            ground_truth="Requires efficiency stats and strategic explanation.",
            category=TestCategory.COMPLEX,
        ),
    ]


class TestSQLEvaluationIntegration:
    """Integration tests for SQL evaluation flow."""

    def test_sql_evaluation_end_to_end_small_set(
        self, mock_chat_service, mock_conversation_service, sample_sql_test_cases
    ):
        """Test complete SQL evaluation flow with small test set."""
        # Mock responses for each test case
        mock_responses = [
            ChatResponse(
                answer="Shai Gilgeous-Alexander scored 2485 points.",
                sources=[],
                query="Who scored the most points?",
                processing_time_ms=150,
                model="gemini-2.0-flash-exp",
            ),
            ChatResponse(
                answer="Top rebounders: Zubac with 1008, Sabonis with 973.",
                sources=[],
                query="Top 3 rebounders?",
                processing_time_ms=160,
                model="gemini-2.0-flash-exp",
            ),
            ChatResponse(
                answer="Top assist leaders: Chris Paul with 702 assists.",
                sources=[],
                query="gimme top assists plz",
                processing_time_ms=140,
                model="gemini-2.0-flash-exp",
            ),
        ]

        mock_chat_service.chat.side_effect = mock_responses

        # Run evaluation logic
        results = []
        routing_stats = {"sql_only": 0, "vector_only": 0, "hybrid": 0, "unknown": 0}

        for test_case in sample_sql_test_cases:
            request = ChatRequest(
                query=test_case.question,
                k=5,
                include_sources=True,
                conversation_id=None,
                turn_number=1,
            )

            response = mock_chat_service.chat(request)

            # Detect routing
            has_sql_data = any(
                kw in response.answer.lower()
                for kw in ["pts", "reb", "ast", "points", "rebounds", "assists"]
            )
            has_vector_context = len(response.sources) > 0

            if has_sql_data and has_vector_context:
                actual_routing = "hybrid"
            elif has_sql_data:
                actual_routing = "sql_only"
            elif has_vector_context:
                actual_routing = "vector_only"
            else:
                actual_routing = "unknown"

            routing_stats[actual_routing] += 1

            results.append(
                {
                    "question": test_case.question,
                    "category": test_case.category,
                    "actual_routing": actual_routing,
                    "success": True,
                }
            )

        # Verify results
        assert len(results) == 3
        assert all(r["success"] for r in results)
        assert routing_stats["sql_only"] == 3  # All should be SQL-only
        assert mock_chat_service.chat.call_count == 3

    def test_sql_evaluation_handles_errors(self, mock_chat_service, sample_sql_test_cases):
        """Test SQL evaluation handles errors gracefully."""
        # Mock one success and one error
        mock_chat_service.chat.side_effect = [
            ChatResponse(
                answer="Success response",
                sources=[],
                query="Test query",
                processing_time_ms=150,
                model="gemini-2.0-flash-exp",
            ),
            Exception("API Error"),
            ChatResponse(
                answer="Another success",
                sources=[],
                query="Test query 2",
                processing_time_ms=160,
                model="gemini-2.0-flash-exp",
            ),
        ]

        results = []
        for test_case in sample_sql_test_cases:
            try:
                request = ChatRequest(query=test_case.question, k=5, include_sources=True)
                response = mock_chat_service.chat(request)
                results.append({"question": test_case.question, "success": True})
            except Exception as e:
                results.append({"question": test_case.question, "success": False, "error": str(e)})

        # Verify error handling
        assert len(results) == 3
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert "error" in results[1]

    def test_sql_evaluation_tracks_conversational_cases(
        self, mock_chat_service, mock_conversation_service
    ):
        """Test SQL evaluation properly handles conversational test cases."""
        from src.evaluation.models.sql_models import QueryType, SQLEvaluationTestCase

        conversational_cases = [
            SQLEvaluationTestCase(
                question="Who leads in assists?",
                query_type=QueryType.SQL_ONLY,
                expected_sql="SELECT p.name, ps.ast",
                ground_truth_answer="Nikola Jokić leads.",
                category="conversational_sql",
            ),
            SQLEvaluationTestCase(
                question="What about his rebounds?",  # Follow-up
                query_type=QueryType.SQL_ONLY,
                expected_sql="SELECT ps.reb",
                ground_truth_answer="He has 973 rebounds.",
                category="conversational_sql",
            ),
        ]

        mock_chat_service.chat.return_value = ChatResponse(
            answer="Stats response",
            sources=[],
            query="Test query",
            processing_time_ms=150,
            model="gemini-2.0-flash-exp",
        )

        conversation_id = None
        turn_number = 0

        for test_case in conversational_cases:
            # Check if follow-up
            is_followup = any(
                ind in test_case.question.lower()
                for ind in ["his ", "her ", "their ", "what about"]
            )

            if is_followup:
                if conversation_id is None:
                    conversation = mock_conversation_service.start_conversation()
                    conversation_id = conversation.id
                    turn_number = 1
                else:
                    turn_number += 1
            else:
                conversation = mock_conversation_service.start_conversation()
                conversation_id = conversation.id
                turn_number = 1

            request = ChatRequest(
                query=test_case.question,
                k=5,
                include_sources=True,
                conversation_id=conversation_id,
                turn_number=turn_number,
            )

            mock_chat_service.chat(request)

        # Verify conversation tracking
        assert conversation_id is not None
        assert turn_number == 2  # Two turns in conversation


class TestVectorEvaluationIntegration:
    """Integration tests for Vector evaluation flow."""

    def test_vector_evaluation_end_to_end_small_set(
        self, mock_chat_service, sample_vector_test_cases
    ):
        """Test complete Vector evaluation flow with small test set."""
        # Mock responses with vector sources
        mock_responses = [
            ChatResponse(
                answer="Three-point shooting is crucial for spacing.",
                sources=[
                    SearchResult(
                        text="Modern NBA strategy...", source="strategy.pdf", score=0.90
                    )
                ],
                query="Why is three-point shooting important in modern NBA?",
                processing_time_ms=200,
                model="gemini-2.0-flash-exp",
            ),
            ChatResponse(
                answer="Defensive strategies have evolved significantly.",
                sources=[
                    SearchResult(text="Evolution of defense...", source="defense.pdf", score=0.85)
                ],
                query="Explain the evolution of defensive strategies.",
                processing_time_ms=210,
                model="gemini-2.0-flash-exp",
            ),
            ChatResponse(
                answer="NBA history spans decades.",
                sources=[SearchResult(text="NBA history...", source="history.pdf", score=0.80)],
                query="gimme some nba history plz",
                processing_time_ms=190,
                model="gemini-2.0-flash-exp",
            ),
        ]

        mock_chat_service.chat.side_effect = mock_responses

        results = []
        routing_stats = {"sql_only": 0, "vector_only": 0, "hybrid": 0, "unknown": 0}

        for test_case in sample_vector_test_cases:
            request = ChatRequest(query=test_case.question, k=5, include_sources=True)
            response = mock_chat_service.chat(request)

            # Detect routing
            has_sql_data = any(
                kw in response.answer.lower()
                for kw in ["pts", "reb", "ast", "points", "rebounds", "assists"]
            )
            has_vector_context = len(response.sources) > 0

            if has_sql_data and has_vector_context:
                actual_routing = "hybrid"
            elif has_sql_data:
                actual_routing = "sql_only"
            elif has_vector_context:
                actual_routing = "vector_only"
            else:
                actual_routing = "unknown"

            routing_stats[actual_routing] += 1

            results.append({"question": test_case.question, "actual_routing": actual_routing})

        # Verify results
        assert len(results) == 3
        assert routing_stats["vector_only"] == 3  # All should be vector-only


class TestHybridEvaluationIntegration:
    """Integration tests for Hybrid evaluation flow."""

    def test_hybrid_evaluation_end_to_end_small_set(
        self, mock_chat_service, sample_hybrid_test_cases
    ):
        """Test complete Hybrid evaluation flow with small test set."""
        # Mock responses with both SQL data and vector sources
        mock_responses = [
            ChatResponse(
                answer="Jokić averaged 26.4 PPG while Embiid had 28.5 PPG. Their styles differ.",
                sources=[
                    SearchResult(
                        text="Playing style analysis...", source="analysis.pdf", score=0.92
                    )
                ],
                query="Compare Jokić and Embiid statistics and explain their playing styles.",
                processing_time_ms=300,
                model="gemini-2.0-flash-exp",
            ),
            ChatResponse(
                answer="Efficient scorers with 60%+ TS are effective due to shot selection.",
                sources=[
                    SearchResult(text="Efficiency analysis...", source="stats.pdf", score=0.88)
                ],
                query="Who are the most efficient scorers and why are they effective?",
                processing_time_ms=310,
                model="gemini-2.0-flash-exp",
            ),
        ]

        mock_chat_service.chat.side_effect = mock_responses

        results = []
        routing_stats = {"sql_only": 0, "vector_only": 0, "hybrid": 0, "unknown": 0}

        for test_case in sample_hybrid_test_cases:
            request = ChatRequest(query=test_case.question, k=5, include_sources=True)
            response = mock_chat_service.chat(request)

            # Detect routing
            has_sql_data = any(
                kw in response.answer.lower()
                for kw in ["pts", "reb", "ast", "points", "rebounds", "assists", "ppg", "ts"]
            )
            has_vector_context = len(response.sources) > 0

            if has_sql_data and has_vector_context:
                actual_routing = "hybrid"
            elif has_sql_data:
                actual_routing = "sql_only"
            elif has_vector_context:
                actual_routing = "vector_only"
            else:
                actual_routing = "unknown"

            routing_stats[actual_routing] += 1

            results.append({"question": test_case.question, "actual_routing": actual_routing})

        # Verify results
        assert len(results) == 2
        assert routing_stats["hybrid"] == 2  # Both should be hybrid


class TestComparisonIntegration:
    """Integration tests for classification comparison."""

    def test_classification_comparison_complete_flow(self, tmp_path):
        """Test complete comparison flow from evaluation results to report."""
        # Create mock evaluation result files
        results_dir = tmp_path / "evaluation_results"
        results_dir.mkdir()

        sql_data = {
            "timestamp": "2026-02-10T12:00:00",
            "total_cases": 48,
            "successful": 48,
            "routing_stats": {"sql_only": 45, "vector_only": 2, "hybrid": 1, "unknown": 0},
            "classification_accuracy": 93.75,
            "misclassifications": [
                {
                    "question": "Test question",
                    "category": "simple",
                    "expected": "sql_only",
                    "actual": "vector_only",
                    "response_preview": "Test response",
                }
            ],
        }

        vector_data = {
            "timestamp": "2026-02-10T12:00:00",
            "total_cases": 23,
            "successful": 23,
            "routing_stats": {"sql_only": 3, "vector_only": 19, "hybrid": 1, "unknown": 0},
            "classification_accuracy": 82.61,
            "misclassifications": [
                {
                    "question": "Vector test",
                    "category": "complex",
                    "expected": "vector_only",
                    "actual": "sql_only",
                    "response_preview": "Stats response",
                }
            ],
        }

        # Write files
        sql_file = results_dir / "sql_evaluation_20260210.json"
        vector_file = results_dir / "vector_evaluation_20260210.json"

        sql_file.write_text(json.dumps(sql_data), encoding="utf-8")
        vector_file.write_text(json.dumps(vector_data), encoding="utf-8")

        # Load and analyze
        with open(sql_file, encoding="utf-8") as f:
            sql_loaded = json.load(f)
        with open(vector_file, encoding="utf-8") as f:
            vector_loaded = json.load(f)

        # Calculate overall accuracy
        total_cases = sql_loaded["total_cases"] + vector_loaded["total_cases"]
        sql_correct = sql_loaded["routing_stats"]["sql_only"]
        vector_correct = vector_loaded["routing_stats"]["vector_only"]
        total_correct = sql_correct + vector_correct
        overall_accuracy = (total_correct / total_cases * 100) if total_cases else 0

        # Verify
        assert overall_accuracy == pytest.approx(90.14, 0.1)
        assert len(sql_loaded["misclassifications"]) == 1
        assert len(vector_loaded["misclassifications"]) == 1
