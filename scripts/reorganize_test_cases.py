"""
FILE: reorganize_test_cases.py
STATUS: Active
RESPONSIBILITY: Reorganize test cases - move pure SQL/Vector queries out of hybrid dataset
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu
"""

from evaluation.hybrid_test_cases import HYBRID_TEST_CASES
from evaluation.models.vector_models import TestCategory, EvaluationTestCase


def categorize_hybrid_queries():
    """Manually categorize HYBRID_TEST_CASES based on careful review."""

    # Pure SQL queries - only need statistics, no contextual analysis
    pure_sql_questions = {
        "Who is the league's leading scorer?",
        "What are his advanced stats?",
        "How does his efficiency compare to other top scorers?",
        "Show me the best rebounders.",
        "Which team has the best record?",
        "Who is their star player?",
        "Compare his stats to last year's MVP.",
        "whos got most asists???",
        "steph curry stats plz",
        "best defenders who r they",
        "how many ppg does the greek freak average",
    }

    # Pure Vector queries - only need contextual analysis, no statistics
    pure_vector_questions = {
        "Explain the evolution of the point guard position in the modern NBA.",
        "What strategies do successful playoff teams employ according to coaches?",
        "Describe the impact of load management on player performance and team success over a full season.",
        "What impact do they have beyond the stats?",
        "What is their offensive strategy?",
    }

    sql_cases = []
    vector_cases = []
    hybrid_cases = []

    for tc in HYBRID_TEST_CASES:
        # Check if it's a pure SQL query
        if tc.question in pure_sql_questions:
            sql_cases.append(tc)
        # Check if it's a pure Vector query
        elif tc.question in pure_vector_questions:
            vector_cases.append(tc)
        # Everything else is hybrid
        else:
            hybrid_cases.append(tc)

    return sql_cases, vector_cases, hybrid_cases


def print_reorganization_plan():
    """Show what will be moved."""

    sql_cases, vector_cases, hybrid_cases = categorize_hybrid_queries()

    print("="*100)
    print("  TEST CASE REORGANIZATION PLAN")
    print("="*100)

    print(f"\nCurrent HYBRID_TEST_CASES: {len(HYBRID_TEST_CASES)}")
    print(f"  > Pure SQL (move to SQL_TEST_CASES): {len(sql_cases)}")
    print(f"  > Pure Vector (move to vector selection): {len(vector_cases)}")
    print(f"  > True Hybrid (keep in HYBRID_TEST_CASES): {len(hybrid_cases)}")

    print(f"\n{'='*100}")
    print(f"  PURE SQL QUERIES TO MOVE ({len(sql_cases)})")
    print(f"{'='*100}")
    for i, tc in enumerate(sql_cases, 1):
        print(f"\n[{i}] {tc.category.value}")
        print(f"    Question: {tc.question}")

    print(f"\n{'='*100}")
    print(f"  PURE VECTOR QUERIES TO MOVE ({len(vector_cases)})")
    print(f"{'='*100}")
    for i, tc in enumerate(vector_cases, 1):
        print(f"\n[{i}] {tc.category.value}")
        print(f"    Question: {tc.question}")

    print(f"\n{'='*100}")
    print(f"  TRUE HYBRID QUERIES TO KEEP ({len(hybrid_cases)})")
    print(f"{'='*100}")
    print("Sample (first 5):")
    for i, tc in enumerate(hybrid_cases[:5], 1):
        print(f"\n[{i}] {tc.category.value}")
        print(f"    Question: {tc.question[:100]}...")

    return sql_cases, vector_cases, hybrid_cases


def generate_new_hybrid_file(hybrid_cases):
    """Generate new hybrid_test_cases.py file with only true hybrid queries."""

    content = '''"""
FILE: hybrid_test_cases.py
STATUS: Active
RESPONSIBILITY: TRUE hybrid test cases requiring both SQL and Vector search
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu

NOTE: This file now contains ONLY true hybrid queries that require both:
  1. SQL statistics (PTS, REB, AST, TS%, etc.)
  2. Contextual analysis (strategies, styles, explanations)

Pure SQL queries → moved to SQL_TEST_CASES
Pure Vector queries → moved to vector test selection
"""

from evaluation.models.vector_models import EvaluationTestCase, TestCategory

# ========================================================================
# TRUE HYBRID TEST CASES
# These queries require BOTH SQL statistics AND contextual analysis
# ========================================================================

HYBRID_TEST_CASES: list[EvaluationTestCase] = [
'''

    for tc in hybrid_cases:
        # Format the test case
        content += f'''    EvaluationTestCase(
        question=(
            "{tc.question}"
        ),
        ground_truth=(
            "{tc.ground_truth}"
        ),
        category=TestCategory.{tc.category.name},
    ),
'''

    content += ''']


def get_hybrid_test_statistics() -> dict:
    """Get statistics about hybrid test cases.

    Returns:
        Dictionary with counts and distribution.
    """
    from collections import Counter

    counts = Counter(tc.category for tc in HYBRID_TEST_CASES)
    total = len(HYBRID_TEST_CASES)

    return {
        "total": total,
        "by_category": {cat.value: counts.get(cat, 0) for cat in TestCategory},
        "distribution": {
            cat.value: round(counts.get(cat, 0) / total * 100, 1) if total else 0
            for cat in TestCategory
        },
    }


def print_hybrid_test_statistics() -> None:
    """Print hybrid test case statistics."""
    stats = get_hybrid_test_statistics()

    print("\\n" + "=" * 50)
    print(f"  HYBRID TEST CASES: {stats['total']} total")
    print("=" * 50)
    print(f"  {'Category':<20} {'Count':>6} {'Distribution':>14}")
    print("  " + "-" * 44)
    for cat in TestCategory:
        count = stats["by_category"][cat.value]
        pct = stats["distribution"][cat.value]
        print(f"  {cat.value:<20} {count:>6} {pct:>12.1f}%")
    print("=" * 50 + "\\n")


if __name__ == "__main__":
    print_hybrid_test_statistics()
'''

    return content


def generate_sql_additions(sql_cases):
    """Generate code to add to SQL_TEST_CASES."""

    content = '''
# ========================================================================
# CONVERSATIONAL SQL QUERIES
# Moved from hybrid_test_cases.py (these are pure SQL queries)
# ========================================================================

'''

    for tc in sql_cases:
        if tc.category == TestCategory.CONVERSATIONAL:
            content += f'''SQLTestCase(
    question="{tc.question}",
    category="conversational_followup",
    expected_sql_patterns=["SELECT", "FROM player_stats"],
),
'''

    content += '''
# ========================================================================
# NOISY SQL QUERIES
# Moved from hybrid_test_cases.py (informal pure SQL queries)
# ========================================================================

'''

    for tc in sql_cases:
        if tc.category == TestCategory.NOISY:
            content += f'''SQLTestCase(
    question="{tc.question}",
    category="noisy_sql_query",
    expected_sql_patterns=["SELECT", "FROM player_stats"],
),
'''

    return content


def main():
    """Show reorganization plan and generate new files."""

    # Show what will change
    sql_cases, vector_cases, hybrid_cases = print_reorganization_plan()

    # Generate new hybrid file
    print(f"\n{'='*100}")
    print("  GENERATING NEW FILES")
    print(f"{'='*100}")

    new_hybrid_content = generate_new_hybrid_file(hybrid_cases)
    with open("src/evaluation/hybrid_test_cases_NEW.py", "w", encoding="utf-8") as f:
        f.write(new_hybrid_content)
    print(f"\n✓ Generated: src/evaluation/hybrid_test_cases_NEW.py ({len(hybrid_cases)} cases)")

    sql_additions = generate_sql_additions(sql_cases)
    with open("sql_additions.txt", "w", encoding="utf-8") as f:
        f.write(sql_additions)
    print(f"✓ Generated: sql_additions.txt ({len(sql_cases)} cases to add)")

    print(f"\n{'='*100}")
    print("  NEXT STEPS")
    print(f"{'='*100}")
    print("\n1. Review generated files:")
    print("   - src/evaluation/hybrid_test_cases_NEW.py")
    print("   - sql_additions.txt")

    print("\n2. Back up original:")
    print("   mv src/evaluation/hybrid_test_cases.py src/evaluation/hybrid_test_cases_OLD.py")

    print("\n3. Replace hybrid file:")
    print("   mv src/evaluation/hybrid_test_cases_NEW.py src/evaluation/hybrid_test_cases.py")

    print("\n4. Add SQL cases to SQL_TEST_CASES in src/evaluation/sql_test_cases.py")

    print("\n5. Update evaluate_hybrid.py to remove SIMPLE from get_hybrid_test_cases():")
    print("   Change: if tc.category in [TestCategory.COMPLEX, TestCategory.SIMPLE, TestCategory.CONVERSATIONAL]")
    print("   To:     if tc.category in [TestCategory.COMPLEX, TestCategory.CONVERSATIONAL]")

    print("\n6. Re-run all evaluations to verify:")
    print("   poetry run python scripts/evaluate_sql.py")
    print("   poetry run python scripts/evaluate_vector.py")
    print("   poetry run python scripts/evaluate_hybrid.py")


if __name__ == "__main__":
    main()
