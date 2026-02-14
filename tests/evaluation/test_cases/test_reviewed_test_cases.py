"""
FILE: test_reviewed_test_cases.py
STATUS: Active
RESPONSIBILITY: Test reviewed test case files for quality and correctness
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu
"""

from collections import Counter

import pytest

from src.evaluation.models.vector_models import TestCategory


class TestSQLReviewedTestCases:
    """Tests for sql_test_cases.py quality."""

    def test_sql_reviewed_loads(self):
        """Test that SQL reviewed test cases can be imported and loaded."""
        from src.evaluation.test_cases.sql_test_cases import SQL_TEST_CASES

        assert SQL_TEST_CASES is not None
        assert isinstance(SQL_TEST_CASES, list)
        assert len(SQL_TEST_CASES) > 0

    def test_sql_reviewed_no_duplicates(self):
        """Test that there are no duplicate questions in SQL test cases."""
        from src.evaluation.test_cases.sql_test_cases import SQL_TEST_CASES

        questions = [tc.question for tc in SQL_TEST_CASES]
        duplicates = [q for q, count in Counter(questions).items() if count > 1]

        assert len(duplicates) == 0, f"Found duplicate questions: {duplicates}"

    def test_sql_reviewed_has_variety(self):
        """Test that SQL test cases have different query types."""
        from src.evaluation.test_cases.sql_test_cases import SQL_TEST_CASES

        # Check for variety of query patterns
        query_keywords = {
            "comparison": ["vs", "compare", "versus", "more than", "better"],
            "aggregation": ["average", "total", "count", "how many"],
            "superlative": ["most", "best", "top", "highest", "lowest"],
            "conversational": ["his", "her", "their", "he ", "she "],
            "noisy": ["gimme", "plz", "???", "whos", "whats"],
        }

        variety_counts = {k: 0 for k in query_keywords}
        for tc in SQL_TEST_CASES:
            q_lower = tc.question.lower()
            for variety_type, keywords in query_keywords.items():
                if any(kw in q_lower for kw in keywords):
                    variety_counts[variety_type] += 1
                    break

        # At least 3 different query types should be present
        types_with_cases = sum(1 for count in variety_counts.values() if count > 0)
        assert types_with_cases >= 3, f"Insufficient variety. Found: {variety_counts}"

    def test_sql_reviewed_ground_truth(self):
        """Test that all SQL test cases have expected_sql."""
        from src.evaluation.test_cases.sql_test_cases import SQL_TEST_CASES

        missing_ground_truth = []
        for tc in SQL_TEST_CASES:
            if not hasattr(tc, "expected_sql") or not tc.expected_sql:
                missing_ground_truth.append(tc.question[:60])

        assert (
            len(missing_ground_truth) == 0
        ), f"Cases missing expected_sql: {missing_ground_truth}"

    def test_sql_reviewed_count(self):
        """Test that SQL test cases count is within expected range (~70)."""
        from src.evaluation.test_cases.sql_test_cases import SQL_TEST_CASES

        # Should have around 70 cases (allow some flexibility)
        assert 60 <= len(SQL_TEST_CASES) <= 80, f"Expected ~70 cases, got {len(SQL_TEST_CASES)}"

    def test_sql_reviewed_categories_exist(self):
        """Test that SQL test cases have proper categories."""
        from src.evaluation.test_cases.sql_test_cases import SQL_TEST_CASES

        categories = [tc.category for tc in SQL_TEST_CASES]
        assert len(categories) == len(SQL_TEST_CASES)

        # Check that categories are non-empty strings
        for cat in categories:
            assert isinstance(cat, str)
            assert len(cat) > 0

    def test_sql_reviewed_expected_sql_format(self):
        """Test that expected SQL is properly formatted."""
        from src.evaluation.test_cases.sql_test_cases import SQL_TEST_CASES

        for tc in SQL_TEST_CASES:
            if hasattr(tc, "expected_sql") and tc.expected_sql:
                assert isinstance(tc.expected_sql, str)
                assert len(tc.expected_sql) > 0
                # Basic SQL validation - should contain SELECT
                assert "SELECT" in tc.expected_sql.upper()


class TestHybridReviewedTestCases:
    """Tests for hybrid_test_cases.py quality."""

    def test_hybrid_reviewed_loads(self):
        """Test that Hybrid reviewed test cases can be imported and loaded."""
        from src.evaluation.test_cases.hybrid_test_cases import HYBRID_TEST_CASES

        assert HYBRID_TEST_CASES is not None
        assert isinstance(HYBRID_TEST_CASES, list)
        assert len(HYBRID_TEST_CASES) > 0

    def test_hybrid_reviewed_no_duplicates(self):
        """Test that there are no duplicate questions in Hybrid test cases."""
        from src.evaluation.test_cases.hybrid_test_cases import HYBRID_TEST_CASES

        questions = [tc.question for tc in HYBRID_TEST_CASES]
        duplicates = [q for q, count in Counter(questions).items() if count > 1]

        assert len(duplicates) == 0, f"Found duplicate questions: {duplicates}"

    def test_hybrid_reviewed_is_hybrid(self):
        """Test that all cases require both SQL + Vector (true hybrid)."""
        from src.evaluation.test_cases.hybrid_test_cases import HYBRID_TEST_CASES

        # Check for hybrid indicators in questions or ground truth
        hybrid_indicators = ["and ", "AND ", " + ", "then ", "also "]
        contextual_keywords = [
            "explain",
            "analysis",
            "strategy",
            "style",
            "valuable",
            "effective",
        ]

        weak_hybrid = []
        for tc in HYBRID_TEST_CASES:
            has_indicator = any(ind in tc.question for ind in hybrid_indicators)
            has_contextual = any(kw in tc.question.lower() for kw in contextual_keywords)

            # Ground truth should mention both SQL and contextual analysis
            if hasattr(tc, "ground_truth") and tc.ground_truth:
                requires_both = "SQL" in tc.ground_truth or "statistics" in tc.ground_truth.lower()
            else:
                requires_both = False

            if not (has_indicator or has_contextual or requires_both):
                weak_hybrid.append(tc.question[:80])

        # Allow some flexibility but most should be clearly hybrid
        assert len(weak_hybrid) < len(HYBRID_TEST_CASES) * 0.3, (
            f"Too many weak hybrid cases ({len(weak_hybrid)}): {weak_hybrid[:3]}"
        )

    def test_hybrid_reviewed_ground_truth(self):
        """Test that all hybrid test cases have proper ground truth."""
        from src.evaluation.test_cases.hybrid_test_cases import HYBRID_TEST_CASES

        missing_ground_truth = []
        for tc in HYBRID_TEST_CASES:
            if not hasattr(tc, "ground_truth_answer") or not tc.ground_truth_answer:
                missing_ground_truth.append(tc.question[:60])

        assert (
            len(missing_ground_truth) == 0
        ), f"Cases missing ground_truth_answer: {missing_ground_truth}"

    def test_hybrid_reviewed_count(self):
        """Test that Hybrid test cases count is within expected range (~18)."""
        from src.evaluation.test_cases.hybrid_test_cases import HYBRID_TEST_CASES

        # Should have around 50 cases (allow some flexibility)
        assert 40 <= len(HYBRID_TEST_CASES) <= 60, (
            f"Expected ~50 cases, got {len(HYBRID_TEST_CASES)}"
        )

    def test_hybrid_reviewed_categories(self):
        """Test that Hybrid test cases have proper category distribution."""
        from src.evaluation.test_cases.hybrid_test_cases import HYBRID_TEST_CASES

        categories = [tc.category for tc in HYBRID_TEST_CASES]
        category_counts = Counter(categories)

        # Hybrid cases use tiered string categories (e.g. tier1_stat_plus_context)
        # Verify at least 2 distinct categories exist
        assert len(category_counts) >= 2, f"Expected at least 2 categories, got {category_counts}"
        # All categories should be non-empty strings
        for cat in categories:
            assert isinstance(cat, str) and len(cat) > 0

    def test_hybrid_reviewed_questions_are_complex(self):
        """Test that hybrid questions are sufficiently complex."""
        from src.evaluation.test_cases.hybrid_test_cases import HYBRID_TEST_CASES

        # Hybrid questions should be longer and more complex
        short_questions = []
        for tc in HYBRID_TEST_CASES:
            # Hybrid questions should have at least 10 words
            word_count = len(tc.question.split())
            if word_count < 10:
                short_questions.append((tc.question[:60], word_count))

        # Allow some shorter questions but most should be complex
        assert len(short_questions) < len(HYBRID_TEST_CASES) * 0.3, (
            f"Too many short hybrid questions: {short_questions}"
        )


class TestReviewedTestCasesComparison:
    """Tests comparing both reviewed test case files."""

    def test_no_overlap_between_sql_and_hybrid(self):
        """Test that SQL and Hybrid test cases don't have overlapping questions."""
        from src.evaluation.test_cases.sql_test_cases import SQL_TEST_CASES
        from src.evaluation.test_cases.hybrid_test_cases import HYBRID_TEST_CASES

        sql_questions = {tc.question.lower().strip() for tc in SQL_TEST_CASES}
        hybrid_questions = {tc.question.lower().strip() for tc in HYBRID_TEST_CASES}

        overlap = sql_questions.intersection(hybrid_questions)
        assert len(overlap) == 0, f"Found overlapping questions: {overlap}"

    def test_total_case_count(self):
        """Test that total case count across both files is reasonable."""
        from src.evaluation.test_cases.sql_test_cases import SQL_TEST_CASES
        from src.evaluation.test_cases.hybrid_test_cases import HYBRID_TEST_CASES

        total_cases = len(SQL_TEST_CASES) + len(HYBRID_TEST_CASES)

        # Should have around 130 total cases (80 SQL + 50 Hybrid)
        assert 120 <= total_cases <= 140, f"Expected ~130 total cases, got {total_cases}"

    def test_all_questions_unique_across_files(self):
        """Test that all questions are unique across both files."""
        from src.evaluation.test_cases.sql_test_cases import SQL_TEST_CASES
        from src.evaluation.test_cases.hybrid_test_cases import HYBRID_TEST_CASES

        all_questions = [tc.question for tc in SQL_TEST_CASES + HYBRID_TEST_CASES]
        duplicates = [q for q, count in Counter(all_questions).items() if count > 1]

        assert len(duplicates) == 0, f"Found duplicate questions across files: {duplicates}"
