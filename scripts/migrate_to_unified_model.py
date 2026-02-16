"""
Script to migrate all test cases to unified model and generate missing fields report.

This script:
1. Loads all test cases from the 3 original files
2. Converts them to UnifiedTestCase format
3. Validates all test cases
4. Generates report on missing fields
5. Saves consolidated test cases to new file
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.test_cases.sql_test_cases import SQL_TEST_CASES
from evaluation.test_cases.vector_test_cases import EVALUATION_TEST_CASES as VECTOR_TEST_CASES
from evaluation.test_cases.hybrid_test_cases import HYBRID_TEST_CASES
from evaluation.models import (
    UnifiedTestCase,
    migrate_from_sql_test_case,
    migrate_from_vector_test_case,
    migrate_from_hybrid_test_case,
    validate_test_cases,
    print_validation_report,
)


def main():
    """Migrate all test cases and generate report."""
    print("\n" + "="*80)
    print("MIGRATING TEST CASES TO UNIFIED MODEL")
    print("="*80)

    # Migrate SQL test cases
    print(f"\nMigrating {len(SQL_TEST_CASES)} SQL test cases...")
    unified_sql = [migrate_from_sql_test_case(tc) for tc in SQL_TEST_CASES]

    # Migrate Vector test cases
    print(f"Migrating {len(VECTOR_TEST_CASES)} Vector test cases...")
    unified_vector = [migrate_from_vector_test_case(tc) for tc in VECTOR_TEST_CASES]

    # Migrate Hybrid test cases
    print(f"Migrating {len(HYBRID_TEST_CASES)} Hybrid test cases...")
    unified_hybrid = [migrate_from_hybrid_test_case(tc) for tc in HYBRID_TEST_CASES]

    # Combine all test cases
    all_unified = unified_sql + unified_vector + unified_hybrid

    print(f"\nTotal migrated: {len(all_unified)} test cases")
    print(f"  - SQL: {len(unified_sql)}")
    print(f"  - Vector: {len(unified_vector)}")
    print(f"  - Hybrid: {len(unified_hybrid)}")

    # Validate all test cases
    print("\nValidating test cases...")
    report = validate_test_cases(all_unified)

    # Print validation report
    print_validation_report(report)

    # Generate detailed missing fields report
    generate_missing_fields_report(all_unified)

    # Save Python file with all unified test cases
    save_unified_test_cases(all_unified)

    print("\n" + "="*80)
    print("MIGRATION COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Review missing_fields_report.txt for fields that need to be filled")
    print("2. Update test cases in src/evaluation/test_data.py")
    print("3. Run validation again to verify completeness")
    print("="*80 + "\n")


def generate_missing_fields_report(test_cases: list[UnifiedTestCase]):
    """Generate detailed report of missing fields by test case."""
    output_file = Path("evaluation_results") / "missing_fields_report.txt"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("="*80 + "\n")
        f.write("MISSING FIELDS REPORT - UNIFIED TEST CASES\n")
        f.write("="*80 + "\n\n")

        f.write("SUMMARY:\n")
        f.write(f"Total test cases: {len(test_cases)}\n\n")

        # Count missing fields
        sql_missing = sum(1 for tc in test_cases if not tc.has_sql_expectations() and tc.test_type.value in ['sql', 'hybrid'])
        vector_missing = sum(1 for tc in test_cases if not tc.has_vector_expectations() and tc.test_type.value in ['vector', 'hybrid'])
        answer_missing = sum(1 for tc in test_cases if not tc.ground_truth_answer)

        f.write(f"Test cases missing SQL expectations: {sql_missing}\n")
        f.write(f"Test cases missing Vector expectations: {vector_missing}\n")
        f.write(f"Test cases missing ground truth answer: {answer_missing}\n\n")

        f.write("="*80 + "\n")
        f.write("DETAILED BREAKDOWN BY TEST TYPE\n")
        f.write("="*80 + "\n\n")

        # SQL Test Cases
        f.write("SQL TEST CASES (80 total):\n")
        f.write("-" * 80 + "\n")
        sql_cases = [tc for tc in test_cases if tc.test_type.value == 'sql']
        for i, tc in enumerate(sql_cases, 1):
            missing = tc.get_missing_fields()
            if missing:
                f.write(f"\n[{i}] {tc.question[:80]}\n")
                for category, fields in missing.items():
                    f.write(f"  Missing {category}: {', '.join(fields)}\n")

        # Vector Test Cases
        f.write("\n\nVECTOR TEST CASES (75 total):\n")
        f.write("-" * 80 + "\n")
        vector_cases = [tc for tc in test_cases if tc.test_type.value == 'vector']
        for i, tc in enumerate(vector_cases, 1):
            missing = tc.get_missing_fields()
            if missing:
                f.write(f"\n[{i}] {tc.question[:80]}\n")
                for category, fields in missing.items():
                    f.write(f"  Missing {category}: {', '.join(fields)}\n")

        # Hybrid Test Cases
        f.write("\n\nHYBRID TEST CASES (51 total):\n")
        f.write("-" * 80 + "\n")
        hybrid_cases = [tc for tc in test_cases if tc.test_type.value == 'hybrid']
        for i, tc in enumerate(hybrid_cases, 1):
            missing = tc.get_missing_fields()
            if missing:
                f.write(f"\n[{i}] {tc.question[:80]}\n")
                for category, fields in missing.items():
                    f.write(f"  Missing {category}: {', '.join(fields)}\n")

        f.write("\n" + "="*80 + "\n")
        f.write("END OF REPORT\n")
        f.write("="*80 + "\n")

    print(f"\n✅ Detailed missing fields report saved to: {output_file}")


def save_unified_test_cases(test_cases: list[UnifiedTestCase]):
    """Save all unified test cases to a Python file."""
    output_file = Path("src/evaluation/test_data.py")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write('"""\n')
        f.write('FILE: consolidated_test_cases.py\n')
        f.write('STATUS: Active\n')
        f.write('RESPONSIBILITY: All evaluation test cases in unified format (206 total)\n')
        f.write('LAST MAJOR UPDATE: 2026-02-15\n')
        f.write('MAINTAINER: Shahu\n')
        f.write('\n')
        f.write('STRUCTURE:\n')
        f.write('- ALL_TEST_CASES: List of 206 UnifiedTestCase instances\n')
        f.write('  - 80 SQL test cases\n')
        f.write('  - 75 Vector test cases\n')
        f.write('  - 51 Hybrid test cases\n')
        f.write('\n')
        f.write('NOTES:\n')
        f.write('- Some fields may be None/empty (see missing_fields_report.txt)\n')
        f.write('- Fill missing fields as needed for comprehensive evaluation\n')
        f.write('"""\n\n')

        f.write('from evaluation.models import UnifiedTestCase, TestType, QueryType\n\n')

        f.write('# ============================================================================\n')
        f.write('# ALL TEST CASES (206 total)\n')
        f.write('# ============================================================================\n\n')

        f.write('ALL_TEST_CASES = [\n')

        for tc in test_cases:
            f.write('    UnifiedTestCase(\n')
            f.write(f'        question="{tc.question}",\n')
            f.write(f'        test_type=TestType.{tc.test_type.name},\n')
            f.write(f'        category={repr(tc.category)},\n')
            f.write('\n')
            f.write('        # SQL Expectations\n')

            # SQL fields - always write them (None if not applicable)
            if tc.expected_sql:
                f.write(f'        expected_sql={repr(tc.expected_sql)},\n')
            else:
                f.write('        expected_sql=None,  # TODO: Fill for Vector/Hybrid\n')

            if tc.ground_truth_data:
                f.write(f'        ground_truth_data={repr(tc.ground_truth_data)},\n')
            else:
                f.write('        ground_truth_data=None,  # TODO: Fill for Vector/Hybrid\n')

            if tc.query_type:
                f.write(f'        query_type=QueryType.{tc.query_type.name},\n')
            else:
                f.write('        query_type=None,  # TODO: Fill for Vector/Hybrid\n')

            f.write('\n')
            f.write('        # Vector Expectations\n')

            # Vector fields - always write them
            if tc.ground_truth:
                # Truncate long ground truth
                gt = tc.ground_truth if len(tc.ground_truth) < 200 else tc.ground_truth[:200] + "..."
                f.write(f'        ground_truth={repr(gt)},\n')
            else:
                f.write('        ground_truth=None,  # TODO: Fill for SQL/Hybrid\n')

            f.write(f'        min_vector_sources={tc.min_vector_sources},  # TODO: Fill if needed\n')

            if tc.expected_source_types:
                f.write(f'        expected_source_types={repr(tc.expected_source_types)},\n')
            else:
                f.write('        expected_source_types=None,  # TODO: Fill if needed\n')

            f.write('\n')
            f.write('        # Answer Expectations\n')

            # Answer
            if tc.ground_truth_answer:
                f.write(f'        ground_truth_answer={repr(tc.ground_truth_answer)},\n')
            else:
                f.write('        ground_truth_answer=None,  # TODO: Fill for all test types\n')

            f.write('\n')
            f.write('        # Optional: Conversation context\n')

            # Conversation
            if tc.conversation_thread:
                f.write(f'        conversation_thread={repr(tc.conversation_thread)},\n')
            else:
                f.write('        conversation_thread=None,\n')

            f.write('    ),\n')

        f.write(']\n\n')

        f.write('# ============================================================================\n')
        f.write('# STATISTICS\n')
        f.write('# ============================================================================\n\n')

        f.write('def get_statistics():\n')
        f.write('    """Get test case statistics."""\n')
        f.write('    return {\n')
        f.write(f'        "total": {len(test_cases)},\n')
        f.write(f'        "sql": {len([tc for tc in test_cases if tc.test_type.value == "sql"])},\n')
        f.write(f'        "vector": {len([tc for tc in test_cases if tc.test_type.value == "vector"])},\n')
        f.write(f'        "hybrid": {len([tc for tc in test_cases if tc.test_type.value == "hybrid"])},\n')
        f.write('    }\n\n')

        f.write('if __name__ == "__main__":\n')
        f.write('    stats = get_statistics()\n')
        f.write('    print(f"Total test cases: {stats[\'total\']}")\n')
        f.write('    print(f"  SQL: {stats[\'sql\']}")\n')
        f.write('    print(f"  Vector: {stats[\'vector\']}")\n')
        f.write('    print(f"  Hybrid: {stats[\'hybrid\']}")\n')

    print(f"\n✅ Consolidated test cases saved to: {output_file}")
    print(f"   Contains {len(test_cases)} test cases in UnifiedTestCase format")


if __name__ == "__main__":
    main()
