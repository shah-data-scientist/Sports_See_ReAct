"""
Regenerate consolidated_test_cases.py with renamed fields:
- ground_truth → ground_truth_vector
- Remove ground_truth_answer (will be generated dynamically by judge LLM)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.consolidated_test_cases import ALL_TEST_CASES
from src.evaluation.unified_model import TestType

def regenerate_test_cases():
    """Regenerate consolidated_test_cases.py with renamed fields."""

    output_file = Path("src/evaluation/consolidated_test_cases.py")

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
        f.write('CHANGES (2026-02-15):\n')
        f.write('- Renamed: ground_truth → ground_truth_vector\n')
        f.write('- Removed: ground_truth_answer (will be generated dynamically by judge LLM)\n')
        f.write('- Judge LLM generates expected answer from ground_truth_data and ground_truth_vector\n')
        f.write('"""\n\n')

        f.write('from src.evaluation.unified_model import UnifiedTestCase, TestType\n\n')

        f.write('# ============================================================================\n')
        f.write('# ALL TEST CASES (206 total)\n')
        f.write('# ============================================================================\n\n')

        f.write('ALL_TEST_CASES = [\n')

        for i, tc in enumerate(ALL_TEST_CASES, 1):
            f.write('    UnifiedTestCase(\n')
            f.write(f'        question={repr(tc.question)},\n')
            f.write(f'        test_type=TestType.{tc.test_type.name},\n')
            f.write(f'        category={repr(tc.category)},\n')
            f.write('\n')

            # SQL Expectations section
            f.write('        # SQL Expectations\n')
            f.write(f'        expected_sql={repr(tc.expected_sql)},\n')
            f.write(f'        ground_truth_data={repr(tc.ground_truth_data)},\n')
            f.write('\n')

            # Vector Expectations section
            f.write('        # Vector Expectations\n')

            # Use ground_truth_vector instead of ground_truth
            if hasattr(tc, 'ground_truth_vector'):
                ground_truth_vector = tc.ground_truth_vector
            elif hasattr(tc, 'ground_truth'):
                # For backward compatibility during migration
                ground_truth_vector = tc.ground_truth
            else:
                ground_truth_vector = None

            if ground_truth_vector:
                # Truncate very long ground truth for readability
                gt = ground_truth_vector if len(ground_truth_vector) < 300 else ground_truth_vector[:297] + "..."
                f.write(f'        ground_truth_vector={repr(gt)},\n')
            else:
                f.write(f'        ground_truth_vector=None,\n')

            f.write(f'        min_vector_sources={tc.min_vector_sources},\n')
            f.write(f'        expected_source_types={repr(tc.expected_source_types)},\n')
            f.write('\n')

            # Optional fields
            f.write('        # Optional: Conversation context\n')
            f.write(f'        conversation_thread={repr(tc.conversation_thread)},\n')

            # Notes (only if present)
            if hasattr(tc, 'notes') and tc.notes:
                f.write(f'        notes={repr(tc.notes)},\n')

            f.write('    ),\n')

            # Add separator every 10 test cases for readability
            if i % 10 == 0 and i < len(ALL_TEST_CASES):
                f.write('\n')

        f.write(']\n\n')

        # Statistics section
        f.write('# ============================================================================\n')
        f.write('# STATISTICS\n')
        f.write('# ============================================================================\n\n')

        sql_count = len([tc for tc in ALL_TEST_CASES if tc.test_type == TestType.SQL])
        vector_count = len([tc for tc in ALL_TEST_CASES if tc.test_type == TestType.VECTOR])
        hybrid_count = len([tc for tc in ALL_TEST_CASES if tc.test_type == TestType.HYBRID])

        f.write('def get_statistics():\n')
        f.write('    """Get test case statistics."""\n')
        f.write('    return {\n')
        f.write(f'        "total": {len(ALL_TEST_CASES)},\n')
        f.write(f'        "sql": {sql_count},\n')
        f.write(f'        "vector": {vector_count},\n')
        f.write(f'        "hybrid": {hybrid_count},\n')
        f.write('    }\n\n')

        f.write('if __name__ == "__main__":\n')
        f.write('    stats = get_statistics()\n')
        f.write('    print(f"Total test cases: {stats[\'total\']}")\n')
        f.write('    print(f"  SQL: {stats[\'sql\']}")\n')
        f.write('    print(f"  Vector: {stats[\'vector\']}")\n')
        f.write('    print(f"  Hybrid: {stats[\'hybrid\']}")\n')

    print(f"\n✅ Regenerated {output_file}")
    print(f"   Changes:")
    print(f"   - Renamed: ground_truth → ground_truth_vector")
    print(f"   - Removed: ground_truth_answer field")
    print(f"   Total test cases: {len(ALL_TEST_CASES)}")
    print(f"   - SQL: {sql_count}")
    print(f"   - Vector: {vector_count}")
    print(f"   - Hybrid: {hybrid_count}")

if __name__ == "__main__":
    regenerate_test_cases()
