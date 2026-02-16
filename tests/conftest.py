"""
FILE: conftest.py
STATUS: Active
RESPONSIBILITY: Shared pytest fixtures for all test modules
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu
"""

from unittest.mock import MagicMock

import pytest

from src.models.chat import ChatResponse, SearchResult


# ============================================================================
# CHAT SERVICE FIXTURES
# ============================================================================


@pytest.fixture
def mock_chat_response():
    """Mock basic ChatResponse for testing."""
    return ChatResponse(
        answer="This is a test response from the chat service.",
        sources=[],
        query="Test query",
        processing_time_ms=100,
        model="gemini-2.0-flash-exp",
    )


@pytest.fixture
def mock_chat_response_with_sql():
    """Mock ChatResponse with SQL data (no vector sources)."""
    return ChatResponse(
        answer="Shai Gilgeous-Alexander scored 2485 points with 129 assists this season.",
        sources=[],
        query="Who scored the most?",
        processing_time_ms=150,
        model="gemini-2.0-flash-exp",
    )


@pytest.fixture
def mock_chat_response_with_vector():
    """Mock ChatResponse with vector sources (no SQL data)."""
    return ChatResponse(
        answer="The NBA has evolved significantly with emphasis on three-point shooting and pace.",
        sources=[
            SearchResult(
                text="Evolution of NBA strategy and tactics over the decades...",
                source="nba_history.pdf",
                score=0.85,
            ),
            SearchResult(
                text="Modern basketball emphasizes spacing and efficiency...",
                source="modern_game.pdf",
                score=0.82,
            ),
        ],
        query="Explain NBA evolution",
        processing_time_ms=200,
        model="gemini-2.0-flash-exp",
    )


@pytest.fixture
def mock_chat_response_hybrid():
    """Mock ChatResponse with both SQL data and vector sources (hybrid)."""
    return ChatResponse(
        answer="Nikola Jokić averaged 26.4 PPG and 12.4 RPG. His unique playmaking style as a center revolutionized the position.",
        sources=[
            SearchResult(
                text="Jokić's playing style analysis and impact on modern centers...",
                source="player_analysis.pdf",
                score=0.90,
            )
        ],
        query="Jokić stats and style",
        processing_time_ms=300,
        model="gemini-2.0-flash-exp",
    )


# ============================================================================
# EVALUATION TEST CASE FIXTURES
# ============================================================================


@pytest.fixture
def sample_sql_test_cases():
    """Sample SQL test cases for testing (5 cases)."""
    from evaluation.models.sql_models import QueryType, SQLEvaluationTestCase

    return [
        SQLEvaluationTestCase(
            question="Who scored the most points this season?",
            query_type=QueryType.SQL_ONLY,
            expected_sql="SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.pts DESC LIMIT 1",
            ground_truth_answer="Shai Gilgeous-Alexander scored the most points with 2485 PTS.",
            ground_truth_data={"name": "Shai Gilgeous-Alexander", "pts": 2485},
            category="simple_sql_top_n",
        ),
        SQLEvaluationTestCase(
            question="Who are the top 3 rebounders?",
            query_type=QueryType.SQL_ONLY,
            expected_sql="SELECT p.name, ps.reb FROM players p JOIN player_stats ps ORDER BY ps.reb DESC LIMIT 3",
            ground_truth_answer="Top 3 rebounders: Ivica Zubac, Domantas Sabonis, Karl-Anthony Towns.",
            ground_truth_data=[
                {"name": "Ivica Zubac", "reb": 1008},
                {"name": "Domantas Sabonis", "reb": 973},
                {"name": "Karl-Anthony Towns", "reb": 922},
            ],
            category="simple_sql_top_n",
        ),
        SQLEvaluationTestCase(
            question="Compare Jokić vs Embiid in rebounds",
            query_type=QueryType.SQL_ONLY,
            expected_sql="SELECT p.name, ps.reb FROM players p JOIN player_stats ps WHERE p.name IN ('Nikola Jokić', 'Joel Embiid')",
            ground_truth_answer="Jokić: 973 REB, Embiid: 683 REB",
            category="complex_sql_comparison",
        ),
        SQLEvaluationTestCase(
            question="What is the average points per game for all players?",
            query_type=QueryType.SQL_ONLY,
            expected_sql="SELECT AVG(ps.ppg) FROM player_stats ps",
            ground_truth_answer="Average PPG across all players.",
            category="complex_sql_aggregation",
        ),
        SQLEvaluationTestCase(
            question="gimme top 5 steals plz",
            query_type=QueryType.SQL_ONLY,
            expected_sql="SELECT p.name, ps.stl FROM players p JOIN player_stats ps ORDER BY ps.stl DESC LIMIT 5",
            ground_truth_answer="Top 5 steals leaders.",
            category="noisy_sql",
        ),
    ]


@pytest.fixture
def sample_vector_test_cases():
    """Sample Vector test cases for testing (5 cases)."""
    from evaluation.models.vector_models import EvaluationTestCase, TestCategory

    return [
        EvaluationTestCase(
            question="Why is three-point shooting so important in modern NBA?",
            ground_truth="Three-point shooting has become crucial due to strategic evolution emphasizing efficiency and spacing.",
            category=TestCategory.COMPLEX,
        ),
        EvaluationTestCase(
            question="Explain how defensive strategies have evolved in the NBA.",
            ground_truth="Defensive strategies have evolved with emphasis on switching, help defense, and perimeter containment.",
            category=TestCategory.COMPLEX,
        ),
        EvaluationTestCase(
            question="What makes a great point guard in today's game?",
            ground_truth="Great point guards combine playmaking, scoring, and decision-making skills.",
            category=TestCategory.COMPLEX,
        ),
        EvaluationTestCase(
            question="gimme some nba history plz",
            ground_truth="NBA history spans decades of evolution and memorable moments.",
            category=TestCategory.NOISY,
        ),
        EvaluationTestCase(
            question="whats the deal with small ball???",
            ground_truth="Small ball is a strategic approach emphasizing speed and shooting over size.",
            category=TestCategory.NOISY,
        ),
    ]


@pytest.fixture
def sample_hybrid_test_cases():
    """Sample Hybrid test cases for testing (5 cases)."""
    from evaluation.models.vector_models import EvaluationTestCase, TestCategory

    return [
        EvaluationTestCase(
            question="Compare Nikola Jokić and Joel Embiid's statistics this season and explain which one is more valuable to their team.",
            ground_truth="Requires both players' statistics (PTS, REB, AST) and contextual analysis of their playing styles.",
            category=TestCategory.COMPLEX,
        ),
        EvaluationTestCase(
            question="Who are the most efficient scorers this season and why are they so effective?",
            ground_truth="Requires efficiency statistics (TS%, PER) combined with strategic analysis of their scoring methods.",
            category=TestCategory.COMPLEX,
        ),
        EvaluationTestCase(
            question="Compare Giannis and Durant's scoring and explain how their playing styles differ.",
            ground_truth="Requires scoring statistics and analysis of paint dominance vs perimeter versatility.",
            category=TestCategory.COMPLEX,
        ),
        EvaluationTestCase(
            question="gimme curry stats and tell me why hes so good plz",
            ground_truth="Requires Curry's statistics and explanation of his shooting prowess and impact.",
            category=TestCategory.NOISY,
        ),
        EvaluationTestCase(
            question="whos better lebron or jordan??? show me stats and explain",
            ground_truth="Requires career statistics comparison and contextual analysis of different eras.",
            category=TestCategory.NOISY,
        ),
    ]


# ============================================================================
# EVALUATION RESULT FIXTURES
# ============================================================================


@pytest.fixture
def sample_sql_evaluation_results():
    """Sample SQL evaluation results JSON for testing."""
    return {
        "timestamp": "2026-02-10T12:00:00",
        "total_cases": 48,
        "successful": 48,
        "failed": 0,
        "category_breakdown": {
            "simple_sql_top_n": 12,
            "complex_sql_comparison": 15,
            "complex_sql_aggregation": 8,
            "conversational_sql": 8,
            "noisy_sql": 5,
        },
        "routing_stats": {"sql_only": 45, "vector_only": 2, "hybrid": 1, "unknown": 0},
        "classification_accuracy": 93.75,
        "misclassifications": [
            {
                "question": "Explain the importance of rebounds",
                "category": "simple_sql",
                "expected": "sql_only",
                "actual": "vector_only",
                "response_preview": "Rebounds are crucial for possession control...",
            },
            {
                "question": "Compare stats and analyze playing styles",
                "category": "complex_sql",
                "expected": "sql_only",
                "actual": "hybrid",
                "response_preview": "Player A scored 2000 points. Their style differs...",
            },
        ],
        "results": [],
    }


@pytest.fixture
def sample_vector_evaluation_results():
    """Sample Vector evaluation results JSON for testing."""
    return {
        "timestamp": "2026-02-10T12:00:00",
        "total_cases": 23,
        "successful": 23,
        "failed": 0,
        "category_breakdown": {"complex": 14, "noisy": 9},
        "routing_stats": {"sql_only": 3, "vector_only": 19, "hybrid": 1, "unknown": 0},
        "classification_accuracy": 82.61,
        "misclassifications": [
            {
                "question": "Who scored the most points?",
                "category": "complex",
                "expected": "vector_only",
                "actual": "sql_only",
                "response_preview": "Shai Gilgeous-Alexander scored 2485 points...",
            },
            {
                "question": "Top scorers and their impact on the game",
                "category": "complex",
                "expected": "vector_only",
                "actual": "hybrid",
                "response_preview": "Top scorers include players with 2000+ points...",
            },
        ],
        "results": [],
    }


@pytest.fixture
def sample_hybrid_evaluation_results():
    """Sample Hybrid evaluation results JSON for testing."""
    return {
        "timestamp": "2026-02-10T12:00:00",
        "total_cases": 18,
        "successful": 18,
        "failed": 0,
        "category_breakdown": {"complex": 14, "noisy": 4},
        "routing_stats": {"sql_only": 2, "vector_only": 1, "hybrid": 15, "unknown": 0},
        "classification_accuracy": 83.33,
        "misclassifications": [
            {
                "question": "Compare Jokić and Embiid stats",
                "category": "complex",
                "expected": "hybrid",
                "actual": "sql_only",
                "response_preview": "Jokić: 2485 PTS, Embiid: 2200 PTS",
            },
            {
                "question": "Explain defensive evolution in NBA",
                "category": "complex",
                "expected": "hybrid",
                "actual": "vector_only",
                "response_preview": "Defensive strategies have evolved significantly...",
            },
        ],
        "results": [],
    }


# ============================================================================
# MOCK SERVICE FIXTURES
# ============================================================================


@pytest.fixture
def mock_chat_service():
    """Mock ChatService for testing."""
    service = MagicMock()
    service.ensure_ready = MagicMock()
    service.is_ready = True
    service.chat.return_value = ChatResponse(
        answer="Mock response",
        sources=[],
        query="Mock query",
        processing_time_ms=100,
        model="gemini-2.0-flash-exp",
    )
    return service


@pytest.fixture
def mock_conversation_service():
    """Mock ConversationService for testing."""
    service = MagicMock()
    mock_conversation = MagicMock()
    mock_conversation.id = "test-conversation-123"
    service.start_conversation.return_value = mock_conversation
    return service


@pytest.fixture
def mock_conversation_repository():
    """Mock ConversationRepository for testing."""
    repository = MagicMock()
    return repository


# ============================================================================
# UTILITY FIXTURES
# ============================================================================


@pytest.fixture
def temp_evaluation_results_dir(tmp_path):
    """Create temporary evaluation results directory."""
    results_dir = tmp_path / "evaluation_results"
    results_dir.mkdir()
    return results_dir
