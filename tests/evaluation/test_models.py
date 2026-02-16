"""
FILE: test_models.py
STATUS: Active
RESPONSIBILITY: Tests for RAGAS evaluation module with mocked API calls
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import pytest

from evaluation.models.vector_models import (
    CategoryResult,
    EvaluationReport,
    EvaluationSample,
    EvaluationTestCase,
    MetricScores,
    TestCategory,
)
from evaluation.test_cases.vector_test_cases import EVALUATION_TEST_CASES


class TestEvaluationModels:
    def test_test_category_enum(self):
        assert TestCategory.SIMPLE.value == "simple"
        assert TestCategory.COMPLEX.value == "complex"
        assert TestCategory.NOISY.value == "noisy"
        assert TestCategory.CONVERSATIONAL.value == "conversational"

    def test_evaluation_test_case_valid(self):
        tc = EvaluationTestCase(
            question="Who won the championship?",
            ground_truth="The Denver Nuggets won in 2023.",
            category=TestCategory.SIMPLE,
        )
        assert tc.category == TestCategory.SIMPLE

    def test_evaluation_test_case_empty_question_raises(self):
        with pytest.raises(ValueError):
            EvaluationTestCase(
                question="",
                ground_truth="Answer",
                category=TestCategory.SIMPLE,
            )

    def test_evaluation_sample_valid(self):
        sample = EvaluationSample(
            user_input="Who won?",
            response="The Nuggets won.",
            retrieved_contexts=["Context 1", "Context 2"],
            reference="The Nuggets won in 2023.",
            category=TestCategory.SIMPLE,
        )
        assert len(sample.retrieved_contexts) == 2

    def test_metric_scores_defaults(self):
        scores = MetricScores()
        assert scores.faithfulness is None
        assert scores.answer_relevancy is None

    def test_metric_scores_with_values(self):
        scores = MetricScores(
            faithfulness=0.85,
            answer_relevancy=0.90,
            context_precision=0.75,
            context_recall=0.80,
        )
        assert scores.faithfulness == 0.85

    def test_category_result(self):
        cr = CategoryResult(
            category=TestCategory.SIMPLE,
            count=4,
            avg_faithfulness=0.9,
        )
        assert cr.count == 4

    def test_evaluation_report(self):
        report = EvaluationReport(
            overall_scores=MetricScores(faithfulness=0.85),
            category_results=[
                CategoryResult(category=TestCategory.SIMPLE, count=4),
            ],
            sample_count=4,
            model_used="mistral-small-latest",
        )
        assert report.sample_count == 4


class TestTestCases:
    def test_test_cases_not_empty(self):
        assert len(EVALUATION_TEST_CASES) > 0

    def test_all_categories_represented(self):
        categories = {tc.category for tc in EVALUATION_TEST_CASES}
        assert TestCategory.SIMPLE in categories
        assert TestCategory.COMPLEX in categories
        assert TestCategory.NOISY in categories
        assert TestCategory.CONVERSATIONAL in categories

    def test_total_cases_at_least_40(self):
        assert len(EVALUATION_TEST_CASES) >= 40

    def test_simple_cases_exist(self):
        simple = [tc for tc in EVALUATION_TEST_CASES if tc.category == TestCategory.SIMPLE]
        assert len(simple) >= 10

    def test_complex_cases_exist(self):
        complex_cases = [tc for tc in EVALUATION_TEST_CASES if tc.category == TestCategory.COMPLEX]
        assert len(complex_cases) >= 10

    def test_noisy_cases_exist(self):
        noisy = [tc for tc in EVALUATION_TEST_CASES if tc.category == TestCategory.NOISY]
        assert len(noisy) >= 8

    def test_conversational_cases_exist(self):
        conv = [tc for tc in EVALUATION_TEST_CASES if tc.category == TestCategory.CONVERSATIONAL]
        assert len(conv) >= 10

    def test_statistics_function(self):
        from evaluation.test_cases.vector_test_cases import get_test_case_statistics

        stats = get_test_case_statistics()
        assert stats["total"] == len(EVALUATION_TEST_CASES)
        assert "by_category" in stats
        assert "distribution" in stats
        assert sum(stats["by_category"].values()) == stats["total"]


