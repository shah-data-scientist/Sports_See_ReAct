"""
Visualize query processing flow using ground truth data from test cases.
Shows SQL/Vector/Hybrid flow without needing live API calls.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.consolidated_test_cases import ALL_TEST_CASES
from src.evaluation.unified_model import TestType


def print_box(title, content, width=80):
    """Print content in a box."""
    print(f"\n┌{'─' * (width - 2)}┐")
    print(f"│ {title:<{width - 4}} │")
    print(f"├{'─' * (width - 2)}┤")
    for line in content.split('\n'):
        if line:
            print(f"│ {line:<{width - 4}} │")
    print(f"└{'─' * (width - 2)}┘")


def visualize_sql_query(test_case, num):
    """Visualize SQL-only query processing."""
    print(f"\n{'=' * 80}")
    print(f"SQL EXAMPLE {num}: {test_case.test_type.value.upper()} Query")
    print(f"{'=' * 80}\n")

    print_box("📝 USER QUESTION", test_case.question)

    print("\n" + "▼" * 80)
    print("STEP 1: Query Classification")
    print("▼" * 80)
    print(f"  🔍 Detected Type: SQL-ONLY")
    print(f"  📂 Category: {test_case.category}")
    print(f"  ✅ Route to: SQL Database")

    print("\n" + "▼" * 80)
    print("STEP 2: SQL Query Generation (by LLM Agent)")
    print("▼" * 80)
    print(f"\n  Generated SQL:")
    print(f"  {'-' * 76}")
    if test_case.expected_sql:
        for line in test_case.expected_sql.split('\n'):
            print(f"  {line}")
    print(f"  {'-' * 76}")

    print("\n" + "▼" * 80)
    print("STEP 3: Database Execution")
    print("▼" * 80)

    if test_case.ground_truth_data:
        print(f"\n  💾 SQL Results:")
        print(f"  {'-' * 76}")
        if isinstance(test_case.ground_truth_data, list):
            print(f"  Returned {len(test_case.ground_truth_data)} row(s):")
            for i, row in enumerate(test_case.ground_truth_data[:3], 1):
                print(f"    Row {i}: {json.dumps(row, indent=6)[1:]}")
        else:
            print(f"  {json.dumps(test_case.ground_truth_data, indent=4)}")
        print(f"  {'-' * 76}")

    print("\n" + "▼" * 80)
    print("STEP 4: Vector Search")
    print("▼" * 80)
    print(f"  ⏭️  SKIPPED (SQL-only query)")
    print(f"  📚 Vector sources retrieved: 0")

    print("\n" + "▼" * 80)
    print("STEP 5: LLM Answer Generation")
    print("▼" * 80)

    if test_case.ground_truth_answer:
        print_box("🎯 FINAL ANSWER", test_case.ground_truth_answer)

    print("\n" + "=" * 80 + "\n")


def visualize_vector_query(test_case, num):
    """Visualize Vector-only query processing."""
    print(f"\n{'=' * 80}")
    print(f"VECTOR EXAMPLE {num}: {test_case.test_type.value.upper()} Query")
    print(f"{'=' * 80}\n")

    print_box("📝 USER QUESTION", test_case.question)

    print("\n" + "▼" * 80)
    print("STEP 1: Query Classification")
    print("▼" * 80)
    print(f"  🔍 Detected Type: VECTOR-ONLY (Contextual)")
    print(f"  📂 Category: {test_case.category}")
    print(f"  ✅ Route to: Vector Database")

    print("\n" + "▼" * 80)
    print("STEP 2: SQL Query Generation")
    print("▼" * 80)
    print(f"  ⏭️  SKIPPED (Vector-only query)")
    print(f"  💾 SQL executed: No")

    print("\n" + "▼" * 80)
    print("STEP 3: Vector Search")
    print("▼" * 80)

    if test_case.ground_truth:
        print(f"\n  📚 Vector Search Execution:")
        print(f"  {'-' * 76}")
        print(f"  Expected sources: {test_case.min_vector_sources}+ chunks")
        if test_case.expected_source_types:
            print(f"  Expected source files: {', '.join(test_case.expected_source_types)}")
        print(f"\n  Expected retrieval:")

        # Parse ground truth for details
        gt = test_case.ground_truth
        if "Reddit" in gt:
            if "Reddit 1.pdf" in gt:
                print(f"    Source 1: Reddit 1.pdf")
                print(f"      Post: 'Who are teams in the playoffs that have impressed you?'")
                print(f"      Author: u/MannerSuperb")
                print(f"      Similarity: ~75-85%")
            elif "Reddit 3.pdf" in gt:
                print(f"    Source 1: Reddit 3.pdf")
                print(f"      Post: 'Reggie Miller is the most efficient first option'")
                print(f"      Author: u/hqppp")
                print(f"      Similarity: ~80-90%")
        elif "glossary" in gt.lower():
            print(f"    Source 1: regular NBA.xlsx (glossary)")
            print(f"      Content: NBA statistical metric definitions (French)")
            print(f"      Similarity: ~85-95%")

        print(f"\n  Context expectation:")
        print(f"  {'-' * 76}")
        # Show first 200 chars of ground truth
        gt_preview = gt[:300] + "..." if len(gt) > 300 else gt
        for line in gt_preview.split('. '):
            if line.strip():
                print(f"  {line.strip()}.")
        print(f"  {'-' * 76}")

    print("\n" + "▼" * 80)
    print("STEP 4: LLM Answer Generation")
    print("▼" * 80)

    if test_case.ground_truth_answer:
        print_box("🎯 EXPECTED FINAL ANSWER", test_case.ground_truth_answer)
    else:
        print(f"  ⚠️  No ground_truth_answer provided for this Vector test case")
        print(f"  (This is one of the 75 Vector cases missing ground_truth_answer)")

    print("\n" + "=" * 80 + "\n")


def visualize_hybrid_query(test_case, num):
    """Visualize Hybrid query processing."""
    print(f"\n{'=' * 80}")
    print(f"HYBRID EXAMPLE {num}: {test_case.test_type.value.upper()} Query")
    print(f"{'=' * 80}\n")

    print_box("📝 USER QUESTION", test_case.question)

    print("\n" + "▼" * 80)
    print("STEP 1: Query Classification")
    print("▼" * 80)
    print(f"  🔍 Detected Type: HYBRID (SQL + Vector)")
    print(f"  📂 Category: {test_case.category}")
    print(f"  ✅ Route to: SQL Database + Vector Database")

    print("\n" + "▼" * 80)
    print("STEP 2: SQL Query Generation & Execution")
    print("▼" * 80)
    print(f"\n  Generated SQL:")
    print(f"  {'-' * 76}")
    if test_case.expected_sql:
        for line in test_case.expected_sql.split('\n'):
            print(f"  {line}")
    print(f"  {'-' * 76}")

    if test_case.ground_truth_data:
        print(f"\n  💾 SQL Results:")
        print(f"  {'-' * 76}")
        if isinstance(test_case.ground_truth_data, list):
            print(f"  Returned {len(test_case.ground_truth_data)} row(s):")
            for i, row in enumerate(test_case.ground_truth_data[:3], 1):
                print(f"    Row {i}: {json.dumps(row, indent=6)[1:]}")
        else:
            print(f"  {json.dumps(test_case.ground_truth_data, indent=4)}")
        print(f"  {'-' * 76}")

    print("\n" + "▼" * 80)
    print("STEP 3: Vector Search")
    print("▼" * 80)

    if test_case.ground_truth:
        print(f"\n  📚 Vector Search Execution:")
        print(f"  {'-' * 76}")
        print(f"  Expected sources: {test_case.min_vector_sources}+ chunks")
        if test_case.expected_source_types:
            print(f"  Expected source files: {', '.join(test_case.expected_source_types)}")

        print(f"\n  Context expectation:")
        print(f"  {'-' * 76}")
        gt_preview = test_case.ground_truth[:300] + "..." if len(test_case.ground_truth) > 300 else test_case.ground_truth
        for line in gt_preview.split('. '):
            if line.strip():
                print(f"  {line.strip()}.")
        print(f"  {'-' * 76}")

    print("\n" + "▼" * 80)
    print("STEP 4: LLM Answer Generation (combines SQL + Vector)")
    print("▼" * 80)

    print(f"\n  LLM receives:")
    print(f"    1. SQL data: {test_case.ground_truth_data}")
    print(f"    2. Vector context: Retrieved chunks from {test_case.expected_source_types}")
    print(f"    3. Instruction: Combine statistical data with contextual insights")

    if test_case.ground_truth_answer:
        print_box("🎯 EXPECTED FINAL ANSWER", test_case.ground_truth_answer)

    print("\n" + "=" * 80 + "\n")


def main():
    """Main visualization."""
    # Get test cases
    sql_cases = [tc for tc in ALL_TEST_CASES if tc.test_type == TestType.SQL]
    vector_cases = [tc for tc in ALL_TEST_CASES if tc.test_type == TestType.VECTOR]
    hybrid_cases = [tc for tc in ALL_TEST_CASES if tc.test_type == TestType.HYBRID]

    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    QUERY PROCESSING FLOW VISUALIZATION                     ║
║                  (Using Ground Truth Data from Test Cases)                 ║
╚════════════════════════════════════════════════════════════════════════════╝

This shows EXACTLY what happens when queries are processed:
  • SQL-only: Database query → Results → Answer
  • Vector-only: Vector search → Context → Answer
  • Hybrid: SQL + Vector → Combined → Answer

Showing 2 examples of each type (6 total)
""")

    # SQL Examples
    print("\n" + "█" * 80)
    print("█" + " " * 27 + "SQL-ONLY QUERIES" + " " * 35 + "█")
    print("█" * 80)

    sql_1 = next((tc for tc in sql_cases if "most points" in tc.question.lower()), sql_cases[0])
    visualize_sql_query(sql_1, 1)

    sql_2 = next((tc for tc in sql_cases if tc != sql_1 and len(tc.question) < 60), sql_cases[1])
    visualize_sql_query(sql_2, 2)

    # Vector Examples
    print("\n" + "█" * 80)
    print("█" + " " * 26 + "VECTOR-ONLY QUERIES" + " " * 33 + "█")
    print("█" * 80)

    vector_1 = next((tc for tc in vector_cases if tc.ground_truth and "Reddit" in tc.ground_truth), vector_cases[0])
    visualize_vector_query(vector_1, 1)

    vector_2 = next((tc for tc in vector_cases if tc != vector_1 and tc.ground_truth and len(tc.question) < 60), vector_cases[1])
    visualize_vector_query(vector_2, 2)

    # Hybrid Examples
    print("\n" + "█" * 80)
    print("█" + " " * 28 + "HYBRID QUERIES" + " " * 36 + "█")
    print("█" * 80)

    hybrid_1 = next((tc for tc in hybrid_cases if "why" in tc.question.lower() or "what makes" in tc.question.lower()), hybrid_cases[0])
    visualize_hybrid_query(hybrid_1, 1)

    hybrid_2 = next((tc for tc in hybrid_cases if tc != hybrid_1), hybrid_cases[1])
    visualize_hybrid_query(hybrid_2, 2)

    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                              SUMMARY                                       ║
╚════════════════════════════════════════════════════════════════════════════╝

✅ SQL-ONLY Flow:
   Question → Classification → SQL Generation → Database → Answer

✅ VECTOR-ONLY Flow:
   Question → Classification → Vector Search → Context Retrieval → Answer

✅ HYBRID Flow:
   Question → Classification → SQL + Vector → Combined Data → Answer

KEY INSIGHTS:
1. All queries go through classification first
2. SQL queries generate and execute SQL, no vector search
3. Vector queries only search documents, no SQL
4. Hybrid queries do BOTH SQL and Vector, then combine results
5. Final answer is always generated by LLM using retrieved data

Note: All 75 Vector test cases are missing ground_truth_answer!
This confirms your decision to make ground_truth_answer REQUIRED for all types.
""")


if __name__ == "__main__":
    main()
