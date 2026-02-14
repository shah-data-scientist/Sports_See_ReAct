"""
FILE: test_vector_test_cases.py
STATUS: Active
RESPONSIBILITY: Validates vector evaluation test case data structure and integrity
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import pytest

from src.evaluation.models.vector_models import EvaluationTestCase, TestCategory
from src.evaluation.test_cases.vector_test_cases import EVALUATION_TEST_CASES


class TestVectorTestCaseStructure:
    """Validate vector test case list integrity."""

    def test_list_not_empty(self):
        """EVALUATION_TEST_CASES is not empty."""
        assert len(EVALUATION_TEST_CASES) > 0

    def test_all_are_evaluation_test_case(self):
        """Every item is an EvaluationTestCase instance."""
        for tc in EVALUATION_TEST_CASES:
            assert isinstance(tc, EvaluationTestCase), f"Not EvaluationTestCase: {tc}"

    def test_all_have_question(self):
        """Every test case has a non-empty question."""
        for tc in EVALUATION_TEST_CASES:
            assert tc.question and len(tc.question.strip()) > 0

    def test_all_have_ground_truth(self):
        """Every test case has a non-empty ground_truth."""
        for tc in EVALUATION_TEST_CASES:
            assert tc.ground_truth and len(tc.ground_truth.strip()) > 0


class TestVectorTestCaseCategories:
    """Validate category distribution."""

    def test_all_categories_valid(self):
        """All categories are valid TestCategory enum values."""
        valid_categories = set(TestCategory)
        for tc in EVALUATION_TEST_CASES:
            assert tc.category in valid_categories, (
                f"Invalid category {tc.category} for: {tc.question}"
            )

    def test_has_simple_cases(self):
        """Suite includes SIMPLE category cases."""
        simple = [tc for tc in EVALUATION_TEST_CASES if tc.category == TestCategory.SIMPLE]
        assert len(simple) > 0

    def test_has_complex_cases(self):
        """Suite includes COMPLEX category cases."""
        complex_cases = [tc for tc in EVALUATION_TEST_CASES if tc.category == TestCategory.COMPLEX]
        assert len(complex_cases) > 0

    def test_has_noisy_cases(self):
        """Suite includes NOISY category cases."""
        noisy = [tc for tc in EVALUATION_TEST_CASES if tc.category == TestCategory.NOISY]
        assert len(noisy) > 0

    def test_has_conversational_cases(self):
        """Suite includes CONVERSATIONAL category cases."""
        conv = [tc for tc in EVALUATION_TEST_CASES if tc.category == TestCategory.CONVERSATIONAL]
        assert len(conv) > 0


class TestVectorTestCaseQuality:
    """Validate data quality constraints."""

    def test_no_duplicate_questions(self):
        """No two vector test cases share the same question."""
        questions = [tc.question for tc in EVALUATION_TEST_CASES]
        assert len(questions) == len(set(questions)), "Duplicate questions found"

    def test_ground_truth_minimum_length(self):
        """All ground_truth strings are at least 10 characters (substantive)."""
        for tc in EVALUATION_TEST_CASES:
            assert len(tc.ground_truth) >= 10, (
                f"Ground truth too short for: {tc.question}"
            )
