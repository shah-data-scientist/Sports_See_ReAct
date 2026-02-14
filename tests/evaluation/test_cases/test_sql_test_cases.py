"""
FILE: test_sql_test_cases.py
STATUS: Active
RESPONSIBILITY: Validates SQL test case data structure and integrity
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import pytest

from src.evaluation.models.sql_models import QueryType, SQLEvaluationTestCase
from src.evaluation.test_cases.sql_test_cases import (
    AGGREGATION_SQL_CASES,
    COMPARISON_SQL_CASES,
    COMPLEX_SQL_CASES,
    CONVERSATIONAL_SQL_CASES,
    SIMPLE_SQL_CASES,
    SQL_TEST_CASES,
)


class TestSQLTestCaseStructure:
    """Validate that all SQL test cases have required fields."""

    def test_all_cases_have_required_fields(self):
        """Every test case must have question, query_type, ground_truth_answer, category."""
        for tc in SQL_TEST_CASES:
            assert tc.question, f"Missing question in {tc}"
            assert tc.query_type is not None, f"Missing query_type in {tc.question}"
            assert tc.ground_truth_answer, f"Missing ground_truth_answer in {tc.question}"
            assert tc.category, f"Missing category in {tc.question}"

    def test_all_are_sql_evaluation_test_case_instances(self):
        """Every item is an SQLEvaluationTestCase."""
        for tc in SQL_TEST_CASES:
            assert isinstance(tc, SQLEvaluationTestCase)

    def test_all_query_types_valid(self):
        """All query_types are valid QueryType enum values."""
        valid_types = set(QueryType)
        for tc in SQL_TEST_CASES:
            assert tc.query_type in valid_types, (
                f"Invalid query_type {tc.query_type} for: {tc.question}"
            )


class TestSQLTestCaseCounts:
    """Validate expected counts per category list."""

    def test_simple_count(self):
        """SIMPLE_SQL_CASES has 13 cases."""
        assert len(SIMPLE_SQL_CASES) == 13

    def test_comparison_count(self):
        """COMPARISON_SQL_CASES has 7 cases."""
        assert len(COMPARISON_SQL_CASES) == 7

    def test_aggregation_count(self):
        """AGGREGATION_SQL_CASES has 11 cases."""
        assert len(AGGREGATION_SQL_CASES) == 11

    def test_complex_count(self):
        """COMPLEX_SQL_CASES has 14 cases."""
        assert len(COMPLEX_SQL_CASES) == 14

    def test_conversational_count(self):
        """CONVERSATIONAL_SQL_CASES has 25 cases."""
        assert len(CONVERSATIONAL_SQL_CASES) == 25

    def test_total_sql_cases(self):
        """SQL_TEST_CASES totals 80."""
        assert len(SQL_TEST_CASES) == 80


class TestSQLTestCaseQuality:
    """Validate data quality constraints."""

    def test_no_duplicate_questions(self):
        """No two SQL test cases share the same question."""
        questions = [tc.question for tc in SQL_TEST_CASES]
        assert len(questions) == len(set(questions)), "Duplicate questions found"

    def test_ground_truth_data_types(self):
        """ground_truth_data is either None, dict, or list of dicts."""
        for tc in SQL_TEST_CASES:
            gtd = tc.ground_truth_data
            if gtd is None:
                continue
            if isinstance(gtd, dict):
                continue
            if isinstance(gtd, list):
                assert all(isinstance(item, dict) for item in gtd), (
                    f"List items must be dicts for: {tc.question}"
                )
                continue
            pytest.fail(f"Invalid ground_truth_data type for: {tc.question}")

    def test_categories_follow_naming_convention(self):
        """Category strings contain underscores and are lowercase-ish."""
        for tc in SQL_TEST_CASES:
            assert "_" in tc.category or tc.category.islower(), (
                f"Category '{tc.category}' doesn't follow convention for: {tc.question}"
            )
