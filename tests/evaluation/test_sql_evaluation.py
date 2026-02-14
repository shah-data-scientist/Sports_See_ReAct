"""
FILE: test_sql_evaluation.py
STATUS: Active
RESPONSIBILITY: Tests for SQL/Hybrid evaluation Pydantic models and computed properties
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import pytest

from src.evaluation.models.sql_models import (
    QueryType,
    SQLAccuracyMetrics,
    SQLEvaluationTestCase,
    SQLExecutionResult,
)
from src.evaluation.models.hybrid_models import (
    HybridEvaluationMetrics,
    HybridEvaluationReport,
    HybridEvaluationSample,
    HybridIntegrationMetrics,
    VectorRetrievalResult,
)


class TestQueryType:
    """Tests for QueryType enum."""

    def test_sql_only_value(self):
        """SQL_ONLY has correct string value."""
        assert QueryType.SQL_ONLY == "sql_only"

    def test_contextual_only_value(self):
        """CONTEXTUAL_ONLY has correct string value."""
        assert QueryType.CONTEXTUAL_ONLY == "contextual_only"

    def test_hybrid_value(self):
        """HYBRID has correct string value."""
        assert QueryType.HYBRID == "hybrid"

    def test_enum_count(self):
        """QueryType has exactly 3 members."""
        assert len(QueryType) == 3


class TestSQLEvaluationTestCase:
    """Tests for SQLEvaluationTestCase creation and validation."""

    def test_valid_test_case(self):
        """Valid test case creates successfully."""
        tc = SQLEvaluationTestCase(
            question="Who scored the most?",
            query_type=QueryType.SQL_ONLY,
            expected_sql="SELECT name FROM players ORDER BY pts DESC LIMIT 1",
            ground_truth_answer="SGA scored the most.",
            category="simple",
        )
        assert tc.question == "Who scored the most?"
        assert tc.query_type == QueryType.SQL_ONLY

    def test_ground_truth_data_dict(self):
        """ground_truth_data accepts a dict."""
        tc = SQLEvaluationTestCase(
            question="Top scorer?",
            query_type=QueryType.SQL_ONLY,
            ground_truth_answer="SGA",
            ground_truth_data={"name": "SGA", "pts": 2485},
            category="simple",
        )
        assert tc.ground_truth_data == {"name": "SGA", "pts": 2485}

    def test_ground_truth_data_list(self):
        """ground_truth_data accepts a list of dicts."""
        tc = SQLEvaluationTestCase(
            question="Top 3?",
            query_type=QueryType.SQL_ONLY,
            ground_truth_answer="Three players",
            ground_truth_data=[{"name": "A"}, {"name": "B"}, {"name": "C"}],
            category="simple",
        )
        assert len(tc.ground_truth_data) == 3

    def test_ground_truth_data_none(self):
        """ground_truth_data defaults to None."""
        tc = SQLEvaluationTestCase(
            question="Average?",
            query_type=QueryType.SQL_ONLY,
            ground_truth_answer="Average is X",
            category="aggregation",
        )
        assert tc.ground_truth_data is None


class TestSQLAccuracyMetrics:
    """Tests for SQLAccuracyMetrics overall_score property."""

    def test_all_true_score(self):
        """All True gives score of 1.0."""
        m = SQLAccuracyMetrics(
            sql_syntax_correct=True,
            sql_semantic_correct=True,
            results_accurate=True,
            execution_success=True,
        )
        assert m.overall_score == 1.0

    def test_all_false_score(self):
        """All False gives score of 0.0."""
        m = SQLAccuracyMetrics(
            sql_syntax_correct=False,
            sql_semantic_correct=False,
            results_accurate=False,
            execution_success=False,
        )
        assert m.overall_score == 0.0

    def test_partial_score(self):
        """Two True out of four gives 0.5."""
        m = SQLAccuracyMetrics(
            sql_syntax_correct=True,
            sql_semantic_correct=True,
            results_accurate=False,
            execution_success=False,
        )
        assert m.overall_score == 0.5


class TestHybridIntegrationMetrics:
    """Tests for HybridIntegrationMetrics integration_score property."""

    def test_full_integration_score(self):
        """All True gives integration_score of 1.0."""
        m = HybridIntegrationMetrics(
            sql_component_used=True,
            vector_component_used=True,
            components_blended=True,
            answer_complete=True,
        )
        assert m.integration_score == 1.0

    def test_partial_integration_score(self):
        """One True out of four gives 0.25."""
        m = HybridIntegrationMetrics(
            sql_component_used=True,
            vector_component_used=False,
            components_blended=False,
            answer_complete=False,
        )
        assert m.integration_score == 0.25


class TestHybridEvaluationMetrics:
    """Tests for HybridEvaluationMetrics overall_score property."""

    def test_answer_only_score(self):
        """With no SQL/vector/integration, full weight goes to answer quality."""
        m = HybridEvaluationMetrics(
            answer_relevancy=0.8,
            answer_correctness=0.6,
        )
        # answer_weight = 1.0, avg = (0.8 + 0.6)/2 = 0.7
        assert abs(m.overall_score - 0.7) < 0.01

    def test_sql_plus_answer_score(self):
        """With SQL component, score includes SQL weight."""
        sql = SQLAccuracyMetrics(
            sql_syntax_correct=True,
            sql_semantic_correct=True,
            results_accurate=True,
            execution_success=True,
        )
        m = HybridEvaluationMetrics(
            sql_accuracy=sql,
            answer_relevancy=1.0,
            answer_correctness=1.0,
        )
        # SQL: 1.0 * 0.4 = 0.4; answer: weight = 0.6, avg = 1.0 * 0.6 = 0.6
        assert abs(m.overall_score - 1.0) < 0.01
