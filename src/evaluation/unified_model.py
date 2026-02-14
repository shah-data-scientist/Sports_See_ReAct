"""
FILE: unified_model.py
STATUS: Active
RESPONSIBILITY: Unified evaluation model for all test case types (SQL, Vector, Hybrid)
LAST MAJOR UPDATE: 2026-02-15
MAINTAINER: Shahu

DESCRIPTION:
Single unified model that consolidates fields from:
- SQLEvaluationTestCase (SQL expectations)
- VectorEvaluationTestCase (Vector expectations)
- HybridEvaluationTestCase (Both expectations)

Empty fields are allowed for test cases that don't need certain expectations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TestType(Enum):
    """Test type classification."""
    SQL = "sql"
    VECTOR = "vector"
    HYBRID = "hybrid"


class QueryType(Enum):
    """Query type for routing expectations."""
    SQL_ONLY = "sql_only"
    CONTEXTUAL_ONLY = "contextual_only"
    HYBRID = "hybrid"


class TestCategory(Enum):
    """Test category for grouping and analysis."""
    # SQL categories
    SIMPLE = "simple"
    COMPARISON = "comparison"
    AGGREGATION = "aggregation"
    COMPLEX = "complex"
    CONVERSATIONAL = "conversational"
    NOISY = "noisy"
    ADVERSARIAL = "adversarial"

    # Add more as needed from original categorizations


@dataclass
class UnifiedTestCase:
    """Unified test case model for SQL, Vector, and Hybrid evaluations.

    This single model consolidates all fields from the three original models:
    - SQLEvaluationTestCase
    - VectorEvaluationTestCase
    - HybridEvaluationTestCase

    Fields that don't apply to a specific test type can be left as None.
    """

    # ========================================================================
    # COMMON FIELDS (Required for all test types)
    # ========================================================================
    question: str
    """The question/query to evaluate."""

    test_type: TestType
    """Type of test: SQL, VECTOR, or HYBRID."""

    category: str | None = None
    """Category for grouping (e.g., 'simple_sql_top_n', 'conversational', etc.)."""

    # ========================================================================
    # SQL EXPECTATIONS (Required for SQL and HYBRID, None for VECTOR)
    # ========================================================================
    expected_sql: str | None = None
    """Expected SQL query that should be generated."""

    ground_truth_data: dict | list | None = None
    """Expected data results from SQL query.
    Can be:
    - dict for single row (e.g., {"name": "LeBron James", "pts": 2485})
    - list[dict] for multiple rows
    """

    query_type: QueryType | None = None
    """Expected query routing type (SQL_ONLY, CONTEXTUAL_ONLY, HYBRID)."""

    # ========================================================================
    # VECTOR EXPECTATIONS (Required for VECTOR and HYBRID, None for SQL)
    # ========================================================================
    ground_truth: str | None = None
    """Expected contextual information from vector search.
    Describes what sources should be retrieved and what context should be found.
    Example: 'Should retrieve Reddit discussions about efficiency, specifically
    mentioning Reggie Miller with 115 TS%...'
    """

    min_vector_sources: int = 0
    """Minimum number of vector sources expected to be retrieved."""

    expected_source_types: list[str] | None = None
    """Expected source types (e.g., ['Reddit 1.pdf', 'Reddit 3.pdf', 'glossary'])."""

    min_similarity_score: float = 0.5
    """Minimum similarity score threshold for retrieved chunks."""

    # ========================================================================
    # ANSWER EXPECTATIONS (Required for all types)
    # ========================================================================
    ground_truth_answer: str | None = None
    """Expected final answer to the question.
    This is the gold standard for evaluating the final LLM response.
    """

    # ========================================================================
    # CONVERSATION CONTEXT (Optional)
    # ========================================================================
    conversation_thread: str | None = None
    """Thread ID for multi-turn conversational test cases.
    Test cases with the same thread ID should maintain conversation context.
    """

    turn_number: int = 1
    """Turn number within conversation thread (1 for standalone queries)."""

    # ========================================================================
    # METADATA (Optional)
    # ========================================================================
    description: str | None = None
    """Human-readable description of what this test case validates."""

    tags: list[str] = field(default_factory=list)
    """Tags for filtering (e.g., ['top_n', 'player_stats', 'biographical'])."""

    difficulty: str = "medium"
    """Difficulty level: 'easy', 'medium', 'hard'."""

    notes: str | None = None
    """Additional notes about edge cases, known issues, etc."""

    # ========================================================================
    # VALIDATION HELPERS
    # ========================================================================

    def is_valid(self) -> tuple[bool, list[str]]:
        """Validate test case has required fields for its type.

        Returns:
            (is_valid, list of missing/invalid fields)
        """
        issues = []

        # Common required fields
        if not self.question:
            issues.append("question is required")
        if not self.test_type:
            issues.append("test_type is required")

        # Type-specific validations
        if self.test_type == TestType.SQL:
            if not self.expected_sql:
                issues.append("SQL test missing expected_sql")
            if not self.ground_truth_data:
                issues.append("SQL test missing ground_truth_data")

        elif self.test_type == TestType.VECTOR:
            if not self.ground_truth:
                issues.append("Vector test missing ground_truth (contextual expectations)")

        elif self.test_type == TestType.HYBRID:
            if not self.expected_sql:
                issues.append("Hybrid test missing expected_sql")
            if not self.ground_truth:
                issues.append("Hybrid test missing ground_truth (contextual expectations)")

        return len(issues) == 0, issues

    def has_sql_expectations(self) -> bool:
        """Check if test case has SQL expectations."""
        return self.expected_sql is not None and self.ground_truth_data is not None

    def has_vector_expectations(self) -> bool:
        """Check if test case has Vector expectations."""
        return self.ground_truth is not None

    def get_missing_fields(self) -> dict[str, list[str]]:
        """Get report of missing/empty fields by category.

        Returns:
            Dict with categories of missing fields
        """
        missing = {
            "sql_fields": [],
            "vector_fields": [],
            "answer_fields": [],
            "optional_fields": []
        }

        # Check SQL fields
        if not self.expected_sql:
            missing["sql_fields"].append("expected_sql")
        if not self.ground_truth_data:
            missing["sql_fields"].append("ground_truth_data")
        if not self.query_type:
            missing["sql_fields"].append("query_type")

        # Check Vector fields
        if not self.ground_truth:
            missing["vector_fields"].append("ground_truth")
        if self.min_vector_sources == 0:
            missing["vector_fields"].append("min_vector_sources")
        if not self.expected_source_types:
            missing["vector_fields"].append("expected_source_types")

        # Check Answer fields
        if not self.ground_truth_answer:
            missing["answer_fields"].append("ground_truth_answer")

        # Check Optional fields
        if not self.category:
            missing["optional_fields"].append("category")
        if not self.description:
            missing["optional_fields"].append("description")

        # Remove empty categories
        return {k: v for k, v in missing.items() if v}


def migrate_from_sql_test_case(old_case) -> UnifiedTestCase:
    """Convert old SQLEvaluationTestCase to UnifiedTestCase.

    Args:
        old_case: Instance of SQLEvaluationTestCase

    Returns:
        Equivalent UnifiedTestCase
    """
    return UnifiedTestCase(
        question=old_case.question,
        test_type=TestType.SQL,
        category=getattr(old_case, 'category', None),
        expected_sql=old_case.expected_sql,
        ground_truth_data=old_case.ground_truth_data,
        query_type=old_case.query_type,
        ground_truth_answer=old_case.ground_truth_answer,
        conversation_thread=getattr(old_case, 'conversation_thread', None),
        # Vector fields will be None (SQL-only test)
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,
    )


def migrate_from_vector_test_case(old_case) -> UnifiedTestCase:
    """Convert old VectorEvaluationTestCase to UnifiedTestCase.

    Args:
        old_case: Instance of VectorEvaluationTestCase

    Returns:
        Equivalent UnifiedTestCase
    """
    return UnifiedTestCase(
        question=old_case.question,
        test_type=TestType.VECTOR,
        category=old_case.category.value if hasattr(old_case.category, 'value') else str(old_case.category),
        ground_truth=old_case.ground_truth,
        ground_truth_answer=None,  # Vector tests use ground_truth instead
        conversation_thread=getattr(old_case, 'conversation_thread', None),
        # SQL fields will be None (Vector-only test)
        expected_sql=None,
        ground_truth_data=None,
        query_type=None,
    )


def migrate_from_hybrid_test_case(old_case) -> UnifiedTestCase:
    """Convert old HybridEvaluationTestCase to UnifiedTestCase.

    Args:
        old_case: Instance of HybridEvaluationTestCase

    Returns:
        Equivalent UnifiedTestCase
    """
    return UnifiedTestCase(
        question=old_case.question,
        test_type=TestType.HYBRID,
        category=getattr(old_case, 'category', None),
        expected_sql=old_case.expected_sql,
        ground_truth_data=old_case.ground_truth_data,
        query_type=old_case.query_type,
        ground_truth_answer=old_case.ground_truth_answer,
        conversation_thread=getattr(old_case, 'conversation_thread', None),
        # Hybrid has both SQL and Vector expectations
        # Note: ground_truth might not be populated in all hybrid cases
        ground_truth=None,  # TODO: Add contextual expectations for hybrid cases
        min_vector_sources=0,
        expected_source_types=None,
    )


# ============================================================================
# VALIDATION AND REPORTING
# ============================================================================

def validate_test_cases(test_cases: list[UnifiedTestCase]) -> dict[str, Any]:
    """Validate all test cases and generate report.

    Args:
        test_cases: List of UnifiedTestCase instances

    Returns:
        Validation report with statistics and issues
    """
    report = {
        "total": len(test_cases),
        "valid": 0,
        "invalid": 0,
        "issues": [],
        "missing_fields_summary": {
            "sql_fields": 0,
            "vector_fields": 0,
            "answer_fields": 0,
        },
        "by_type": {
            "sql": {"count": 0, "valid": 0, "invalid": 0},
            "vector": {"count": 0, "valid": 0, "invalid": 0},
            "hybrid": {"count": 0, "valid": 0, "invalid": 0},
        }
    }

    for i, test_case in enumerate(test_cases):
        is_valid, issues_list = test_case.is_valid()
        test_type = test_case.test_type.value

        report["by_type"][test_type]["count"] += 1

        if is_valid:
            report["valid"] += 1
            report["by_type"][test_type]["valid"] += 1
        else:
            report["invalid"] += 1
            report["by_type"][test_type]["invalid"] += 1
            report["issues"].append({
                "index": i,
                "question": test_case.question[:80],
                "type": test_type,
                "issues": issues_list
            })

        # Count missing fields
        missing = test_case.get_missing_fields()
        if "sql_fields" in missing:
            report["missing_fields_summary"]["sql_fields"] += 1
        if "vector_fields" in missing:
            report["missing_fields_summary"]["vector_fields"] += 1
        if "answer_fields" in missing:
            report["missing_fields_summary"]["answer_fields"] += 1

    return report


def print_validation_report(report: dict[str, Any]) -> None:
    """Print formatted validation report."""
    print("\n" + "=" * 80)
    print("UNIFIED TEST CASE VALIDATION REPORT")
    print("=" * 80)
    print(f"Total Test Cases: {report['total']}")
    print(f"Valid: {report['valid']} ({report['valid']/report['total']*100:.1f}%)")
    print(f"Invalid: {report['invalid']} ({report['invalid']/report['total']*100:.1f}%)")
    print("\n" + "-" * 80)
    print("By Type:")
    for test_type, stats in report["by_type"].items():
        print(f"  {test_type.upper()}: {stats['count']} total, {stats['valid']} valid, {stats['invalid']} invalid")

    print("\n" + "-" * 80)
    print("Missing Fields Summary:")
    print(f"  Test cases missing SQL fields: {report['missing_fields_summary']['sql_fields']}")
    print(f"  Test cases missing Vector fields: {report['missing_fields_summary']['vector_fields']}")
    print(f"  Test cases missing Answer fields: {report['missing_fields_summary']['answer_fields']}")

    if report["issues"]:
        print("\n" + "-" * 80)
        print(f"Validation Issues ({len(report['issues'])} test cases):")
        for issue in report["issues"][:10]:  # Show first 10
            print(f"\n  [{issue['index']}] {issue['type'].upper()}: {issue['question']}")
            for issue_detail in issue['issues']:
                print(f"    - {issue_detail}")
        if len(report["issues"]) > 10:
            print(f"\n  ... and {len(report['issues']) - 10} more issues")

    print("=" * 80 + "\n")
