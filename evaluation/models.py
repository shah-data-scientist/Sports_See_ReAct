"""
FILE: models.py
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
import logging

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Test type classification."""
    SQL = "sql"
    VECTOR = "vector"
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

    BACKWARD COMPATIBILITY NOTE:
    - Accepts 'ground_truth' parameter (old name) and maps it to 'ground_truth_vector'
    - Accepts 'ground_truth_answer' parameter (ignored - will be generated dynamically)
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

    # ========================================================================
    # VECTOR EXPECTATIONS (Required for VECTOR and HYBRID, None for SQL)
    # ========================================================================
    ground_truth_vector: str | None = None
    """Expected contextual information from vector search.
    Describes what sources should be retrieved and what context should be found.
    Example: 'Should retrieve Reddit discussions about efficiency, specifically
    mentioning Reggie Miller with 115 TS%...'
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
    notes: str | None = None
    """Additional notes about edge cases, known issues, etc."""

    # ========================================================================
    # VALIDATION HELPERS
    # ========================================================================

    def is_valid(self) -> tuple[bool, list[str]]:
        """Validate test case has required fields.

        All test types have the same validation requirements.
        Fields that don't apply to a specific type should be None.

        NOTE: ground_truth_answer is NO LONGER required in test cases.
        It will be generated dynamically during evaluation by judge LLM.

        Returns:
            (is_valid, list of missing/invalid fields)
        """
        issues = []

        # Required fields for ALL test types
        if not self.question:
            issues.append("question is required")
        if not self.test_type:
            issues.append("test_type is required")

        return len(issues) == 0, issues

    def has_sql_expectations(self) -> bool:
        """Check if test case has SQL expectations."""
        return self.expected_sql is not None and self.ground_truth_data is not None

    def has_vector_expectations(self) -> bool:
        """Check if test case has Vector expectations."""
        return self.ground_truth_vector is not None

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

        # Check Vector fields
        if not self.ground_truth_vector:
            missing["vector_fields"].append("ground_truth_vector")

        # Check Optional fields
        if not self.category:
            missing["optional_fields"].append("category")

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
        conversation_thread=getattr(old_case, 'conversation_thread', None),
        # Vector fields will be None (SQL-only test)
        ground_truth_vector=None,
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
        ground_truth_vector=old_case.ground_truth,
        conversation_thread=getattr(old_case, 'conversation_thread', None),
        # SQL fields will be None (Vector-only test)
        expected_sql=None,
        ground_truth_data=None,
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
        conversation_thread=getattr(old_case, 'conversation_thread', None),
        # Hybrid has both SQL and Vector expectations
        # Note: ground_truth_vector might not be populated in all hybrid cases
        ground_truth_vector=None,  # TODO: Add contextual expectations for hybrid cases
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
    logger.info("=" * 80)
    logger.info("UNIFIED TEST CASE VALIDATION REPORT")
    logger.info("=" * 80)
    logger.info(f"Total Test Cases: {report['total']}")
    logger.info(f"Valid: {report['valid']} ({report['valid']/report['total']*100:.1f}%)")
    logger.info(f"Invalid: {report['invalid']} ({report['invalid']/report['total']*100:.1f}%)")
    logger.info("-" * 80)
    logger.info("By Type:")
    for test_type, stats in report["by_type"].items():
        logger.info(f"  {test_type.upper()}: {stats['count']} total, {stats['valid']} valid, {stats['invalid']} invalid")

    logger.info("-" * 80)
    logger.info("Missing Fields Summary:")
    logger.info(f"  Test cases missing SQL fields: {report['missing_fields_summary']['sql_fields']}")
    logger.info(f"  Test cases missing Vector fields: {report['missing_fields_summary']['vector_fields']}")
    logger.info(f"  Test cases missing Answer fields: {report['missing_fields_summary']['answer_fields']}")

    if report["issues"]:
        logger.info("-" * 80)
        logger.info(f"Validation Issues ({len(report['issues'])} test cases):")
        for issue in report["issues"][:10]:  # Show first 10
            logger.info(f"\n  [{issue['index']}] {issue['type'].upper()}: {issue['question']}")
            for issue_detail in issue['issues']:
                logger.info(f"    - {issue_detail}")
        if len(report["issues"]) > 10:
            logger.info(f"\n  ... and {len(report['issues']) - 10} more issues")

    logger.info("=" * 80)


# ============================================================================
# UNIFIED EVALUATION RESULT MODEL
# ============================================================================

@dataclass
class UnifiedEvaluationResult:
    """Unified evaluation result model for SQL, Vector, and Hybrid evaluations.

    This single model consolidates result fields from all three evaluation types,
    making analysis uniform across all test types.
    """

    # ========================================================================
    # COMMON FIELDS (Required for all result types)
    # ========================================================================
    question: str
    """The evaluated question/query."""

    test_type: str
    """Type of test: 'sql', 'vector', or 'hybrid'."""

    category: str
    """Test category for grouping."""

    success: bool
    """Whether the evaluation succeeded (no errors)."""

    response: str | None = None
    """The LLM's final answer/response."""

    processing_time_ms: float = 0.0
    """Total processing time in milliseconds."""

    # ========================================================================
    # ROUTING FIELDS (For all types)
    # ========================================================================
    expected_routing: str | None = None
    """Expected routing type (sql_only, vector_only, hybrid)."""

    actual_routing: str | None = None
    """Actual routing type determined by system."""

    is_misclassified: bool = False
    """Whether routing was incorrect."""

    # ========================================================================
    # SQL RESULT FIELDS (SQL and Hybrid)
    # ========================================================================
    generated_sql: str | None = None
    """SQL query generated by the system."""

    sql_results: list[dict] | dict | None = None
    """Actual results from SQL query execution."""

    visualization: dict | None = None
    """Visualization data if generated."""

    # ========================================================================
    # VECTOR RESULT FIELDS (Vector and Hybrid)
    # ========================================================================
    sources: list[dict] = field(default_factory=list)
    """Retrieved sources from vector search.
    Each source dict contains: text, score, source name.
    """

    sources_count: int = 0
    """Number of sources retrieved."""

    ragas_metrics: dict | None = None
    """ALL 7 RAGAS metrics calculated during evaluation.

    ANSWER QUALITY METRICS (use ground_truth_answer):
    - faithfulness: Does answer contradict sources? (0.0-1.0)
    - answer_relevancy: Does answer address question? (0.0-1.0)
    - answer_semantic_similarity: Semantic similarity to expected answer (0.0-1.0)
    - answer_correctness: Combined semantic + factual (0.0-1.0) ⭐ BEST OVERALL

    RETRIEVAL QUALITY METRICS (use ground_truth_vector):
    - context_precision: Relevant chunks ranked higher? (0.0-1.0 or None for SQL-only)
    - context_recall: All required chunks retrieved? (0.0-1.0 or None for SQL-only)
    - context_relevancy: Fraction of chunks relevant (0.0-1.0 or None for SQL-only)

    NOTE: Retrieval metrics (context_*) are None for SQL-only queries.
    """

    # ========================================================================
    # GROUND TRUTH FIELDS (For validation)
    # ========================================================================
    ground_truth_vector: str | None = None
    """Expected contextual information (Vector/Hybrid)."""

    ground_truth_answer: str | None = None
    """Expected final answer (dynamically generated by judge LLM during evaluation)."""

    ground_truth_data: dict | list | None = None
    """Expected SQL results data."""

    sql_validation: dict | None = None
    """SQL result validation comparing expected vs actual.

    Dict with:
    - match (bool): Do results match ground truth?
    - mismatches (list): List of mismatch descriptions
    - error (str|None): Validation error if any

    Only populated for SQL/Hybrid test cases with ground_truth_data.
    """

    retrieval_warnings: list[str] = field(default_factory=list)
    """Retrieval validation warnings.

    Examples:
    - "SQL-only query returned 5 vector sources (wasteful)"
    - "Vector query returned 0 sources (retrieval failed)"
    - "Hybrid query has no SQL results (SQL search failed)"
    """

    # ========================================================================
    # CONVERSATION FIELDS (Optional)
    # ========================================================================
    conversation_id: str | None = None
    """Conversation ID for multi-turn tests."""

    turn_number: int = 1
    """Turn number within conversation."""

    # ========================================================================
    # ERROR FIELDS (For failed evaluations)
    # ========================================================================
    error: str | None = None
    """Error message if evaluation failed."""

    # ========================================================================
    # METADATA
    # ========================================================================
    timestamp: str | None = None
    """ISO timestamp of evaluation."""

    notes: str | None = None
    """Additional notes or observations."""

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "question": self.question,
            "test_type": self.test_type,
            "category": self.category,
            "success": self.success,
            "response": self.response,
            "processing_time_ms": self.processing_time_ms,
            "expected_routing": self.expected_routing,
            "actual_routing": self.actual_routing,
            "routing": self.actual_routing,  # Backward compatibility for analysis module
            "is_misclassified": self.is_misclassified,
            "generated_sql": self.generated_sql,
            "sql_results": self.sql_results,
            "visualization": self.visualization,
            "sources": self.sources,
            "sources_count": self.sources_count,
            "ragas_metrics": self.ragas_metrics,
            "ground_truth_vector": self.ground_truth_vector,
            "ground_truth_answer": self.ground_truth_answer,
            "ground_truth_data": self.ground_truth_data,
            "sql_validation": self.sql_validation,
            "retrieval_warnings": self.retrieval_warnings,
            "conversation_id": self.conversation_id,
            "turn_number": self.turn_number,
            "error": self.error,
            "timestamp": self.timestamp,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UnifiedEvaluationResult":
        """Create result from dictionary."""
        return cls(
            question=data["question"],
            test_type=data["test_type"],
            category=data["category"],
            success=data["success"],
            response=data.get("response"),
            processing_time_ms=data.get("processing_time_ms", 0.0),
            expected_routing=data.get("expected_routing"),
            actual_routing=data.get("actual_routing"),
            is_misclassified=data.get("is_misclassified", False),
            generated_sql=data.get("generated_sql"),
            sql_results=data.get("sql_results"),
            visualization=data.get("visualization"),
            sources=data.get("sources", []),
            sources_count=data.get("sources_count", 0),
            ragas_metrics=data.get("ragas_metrics"),
            ground_truth_vector=data.get("ground_truth_vector"),
            ground_truth_answer=data.get("ground_truth_answer"),
            ground_truth_data=data.get("ground_truth_data"),
            conversation_id=data.get("conversation_id"),
            turn_number=data.get("turn_number", 1),
            error=data.get("error"),
            timestamp=data.get("timestamp"),
            notes=data.get("notes"),
        )
