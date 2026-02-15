"""
Script to add explicit None values to consolidated_test_cases.py for easier manual filling.
"""

from pathlib import Path

def add_explicit_none_values():
    """Add explicit None values to all test cases."""

    # Load existing test cases
    from src.evaluation.test_data import ALL_TEST_CASES
    from src.evaluation.models import TestType, QueryType

    output_file = Path("src/evaluation/test_data.py")

    with open(output_file, "w", encoding="utf-8") as f:
        # Write header
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
        f.write('- All fields are explicitly listed (including None values)\n')
        f.write('- Fields marked with "TODO: Fill" need to be populated\n')
        f.write('- See missing_fields_report.txt for details on what to fill\n')
        f.write('"""\n\n')

        f.write('from src.evaluation.models import UnifiedTestCase, TestType, QueryType\n\n')

        f.write('# ============================================================================\n')
        f.write('# ALL TEST CASES (206 total)\n')
        f.write('# ============================================================================\n\n')

        f.write('ALL_TEST_CASES = [\n')

        for i, tc in enumerate(ALL_TEST_CASES, 1):
            f.write('    UnifiedTestCase(\n')
            f.write(f'        question="{tc.question}",\n')
            f.write(f'        test_type=TestType.{tc.test_type.name},\n')
            f.write(f'        category={repr(tc.category)},\n')
            f.write('\n')

            # SQL Expectations section
            f.write('        # SQL Expectations\n')

            if tc.expected_sql:
                f.write(f'        expected_sql={repr(tc.expected_sql)},\n')
            else:
                if tc.test_type == TestType.SQL:
                    f.write('        expected_sql=None,  # TODO: Should have SQL for SQL test!\n')
                else:
                    f.write('        expected_sql=None,  # N/A for Vector-only\n')

            if tc.ground_truth_data is not None:
                f.write(f'        ground_truth_data={repr(tc.ground_truth_data)},\n')
            else:
                if tc.test_type == TestType.SQL:
                    f.write('        ground_truth_data=None,  # TODO: Should have data for SQL test!\n')
                else:
                    f.write('        ground_truth_data=None,  # N/A for Vector-only\n')

            if tc.query_type:
                f.write(f'        query_type=QueryType.{tc.query_type.name},\n')
            else:
                if tc.test_type == TestType.SQL:
                    f.write('        query_type=None,  # TODO: Should have query_type for SQL test!\n')
                else:
                    f.write('        query_type=None,  # N/A for Vector-only\n')

            f.write('\n')

            # Vector Expectations section
            f.write('        # Vector Expectations\n')

            if tc.ground_truth:
                # Truncate very long ground truth for readability
                gt = tc.ground_truth if len(tc.ground_truth) < 200 else tc.ground_truth[:197] + "..."
                f.write(f'        ground_truth={repr(gt)},\n')
            else:
                if tc.test_type == TestType.VECTOR:
                    f.write('        ground_truth=None,  # TODO: Should have ground_truth for Vector test!\n')
                elif tc.test_type == TestType.HYBRID:
                    f.write('        ground_truth=None,  # TODO: Fill contextual expectations for Hybrid\n')
                else:
                    f.write('        ground_truth=None,  # N/A for SQL-only\n')

            f.write(f'        min_vector_sources={tc.min_vector_sources},')
            if tc.min_vector_sources == 0 and tc.test_type in [TestType.VECTOR, TestType.HYBRID]:
                f.write('  # TODO: Set minimum expected sources\n')
            else:
                f.write('\n')

            if tc.expected_source_types:
                f.write(f'        expected_source_types={repr(tc.expected_source_types)},\n')
            else:
                if tc.test_type in [TestType.VECTOR, TestType.HYBRID]:
                    f.write('        expected_source_types=None,  # TODO: Specify expected sources\n')
                else:
                    f.write('        expected_source_types=None,  # N/A for SQL-only\n')

            f.write('\n')

            # Answer Expectations section
            f.write('        # Answer Expectations\n')

            if tc.ground_truth_answer:
                f.write(f'        ground_truth_answer={repr(tc.ground_truth_answer)},\n')
            else:
                f.write('        ground_truth_answer=None,  # TODO: Fill expected final answer\n')

            f.write('\n')

            # Optional fields
            f.write('        # Optional: Conversation context\n')

            if tc.conversation_thread:
                f.write(f'        conversation_thread={repr(tc.conversation_thread)},\n')
            else:
                f.write('        conversation_thread=None,\n')

            f.write('    ),\n')

            # Add separator every 10 test cases for readability
            if i % 10 == 0 and i < len(ALL_TEST_CASES):
                f.write('\n')

        f.write(']\n\n')

        # Statistics section
        f.write('# ============================================================================\n')
        f.write('# STATISTICS\n')
        f.write('# ============================================================================\n\n')

        f.write('def get_statistics():\n')
        f.write('    """Get test case statistics."""\n')
        f.write('    return {\n')
        f.write(f'        "total": {len(ALL_TEST_CASES)},\n')
        f.write(f'        "sql": {len([tc for tc in ALL_TEST_CASES if tc.test_type.value == "sql"])},\n')
        f.write(f'        "vector": {len([tc for tc in ALL_TEST_CASES if tc.test_type.value == "vector"])},\n')
        f.write(f'        "hybrid": {len([tc for tc in ALL_TEST_CASES if tc.test_type.value == "hybrid"])},\n')
        f.write('    }\n\n')

        f.write('if __name__ == "__main__":\n')
        f.write('    stats = get_statistics()\n')
        f.write('    print(f"Total test cases: {stats[\'total\']}")\n')
        f.write('    print(f"  SQL: {stats[\'sql\']}")\n')
        f.write('    print(f"  Vector: {stats[\'vector\']}")\n')
        f.write('    print(f"  Hybrid: {stats[\'hybrid\']}")\n')

    print(f"\n✅ Updated {output_file} with explicit None values")
    print(f"   All 206 test cases now show ALL fields explicitly")
    print(f"   Fields marked with 'TODO' need to be filled")


if __name__ == "__main__":
    add_explicit_none_values()
