"""
FILE: verify_ground_truth.py
STATUS: Active
RESPONSIBILITY: Unified ground truth verification for SQL and Hybrid test cases against actual database
LAST MAJOR UPDATE: 2026-02-13
MAINTAINER: Shahu

Usage:
    poetry run python src/evaluation/verify_ground_truth.py          # Verify all (SQL + Hybrid)
    poetry run python src/evaluation/verify_ground_truth.py sql      # SQL only (80 cases)
    poetry run python src/evaluation/verify_ground_truth.py hybrid   # Hybrid only (50 cases)
"""
import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.evaluation.consolidated_test_cases import ALL_TEST_CASES
from src.evaluation.unified_model import TestType

DB_PATH = Path(__file__).parent.parent.parent / "data" / "sql" / "nba_stats.db"


def query_db(sql: str) -> list[dict]:
    """Execute SQL and return results as list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except Exception as e:
        return [{"__error__": str(e)}]
    finally:
        conn.close()


def normalize_value(val: Any) -> Any:
    """Normalize values for comparison (handle float precision)."""
    if isinstance(val, float):
        return round(val, 1)
    return val


def compare_results(expected: Any, actual: list[dict]) -> tuple[bool, str, dict]:
    """Compare expected ground truth with actual results."""
    if expected is None:
        return True, "No ground truth data (analysis query)", {"type": "analysis_only"}

    if actual and "__error__" in actual[0]:
        return False, f"SQL error: {actual[0]['__error__']}", {"error": actual[0]["__error__"]}

    if isinstance(expected, dict):
        expected = [expected]

    if len(actual) != len(expected):
        return False, f"Count mismatch: expected {len(expected)}, got {len(actual)}", {
            "expected_count": len(expected),
            "actual_count": len(actual),
            "expected": expected,
            "actual": actual[:10],
        }

    if actual and expected:
        first_key = list(expected[0].keys())[0]
        try:
            actual_sorted = sorted(actual, key=lambda x: (x.get(first_key) is None, x.get(first_key)))
            expected_sorted = sorted(expected, key=lambda x: (x.get(first_key) is None, x.get(first_key)))
        except (TypeError, KeyError):
            actual_sorted = actual
            expected_sorted = expected

        mismatches = []
        for idx, (exp_row, act_row) in enumerate(zip(expected_sorted, actual_sorted)):
            for key in exp_row:
                if key not in act_row:
                    return False, f"Missing key '{key}' in actual results", {
                        "row": idx,
                        "expected_keys": list(exp_row.keys()),
                        "actual_keys": list(act_row.keys()),
                    }

                exp_val = normalize_value(exp_row[key])
                act_val = normalize_value(act_row[key])

                if exp_val != act_val:
                    mismatches.append({
                        "row": idx,
                        "key": key,
                        "expected": exp_val,
                        "actual": act_val,
                    })

        if mismatches:
            return False, "Value mismatches found", {"mismatches": mismatches, "expected": expected, "actual": actual}

    return True, "Match", {"expected": expected, "actual": actual}


def verify_answer_mentions_data(answer: str, data: Any) -> tuple[bool, str]:
    """Verify that ground_truth_answer mentions key values from ground_truth_data."""
    if data is None:
        return True, "No specific data to verify (analysis question)"

    if isinstance(data, dict):
        data = [data]

    missing_mentions = []
    for row in data:
        if "name" in row:
            name = row["name"]
            name_parts = name.split()
            if not any(part in answer for part in name_parts):
                missing_mentions.append(f"Player '{name}' not mentioned")

    if missing_mentions:
        return False, "; ".join(missing_mentions[:3])

    return True, "Answer appropriately mentions data"


def verify_dataset(test_cases: list, dataset_name: str) -> dict:
    """Verify a dataset of test cases against the database."""
    print(f"\n{'=' * 80}")
    print(f"{dataset_name.upper()} GROUND TRUTH VERIFICATION ({len(test_cases)} test cases)")
    print(f"{'=' * 80}")

    results = {"passed": [], "failed": [], "warnings": []}

    for i, test_case in enumerate(test_cases, 1):
        question = test_case.question
        expected_data = test_case.ground_truth_data
        expected_answer = test_case.ground_truth_answer
        sql = test_case.expected_sql
        category = test_case.category

        print(f"\n[{i}/{len(test_cases)}] {category}")
        print(f"Q: {question[:80]}...")

        actual_data = query_db(sql)
        is_match, message, details = compare_results(expected_data, actual_data)

        if not is_match:
            print(f"  \u274c SQL DATA MISMATCH: {message}")
            if "mismatches" in details:
                for mm in details["mismatches"][:3]:
                    print(f"     Row {mm['row']}, {mm['key']}: expected {mm['expected']}, got {mm['actual']}")
            results["failed"].append({"test_case": test_case, "message": message, "details": details})
            continue

        answer_ok, answer_msg = verify_answer_mentions_data(expected_answer, expected_data)

        if not answer_ok:
            print(f"  \u26a0\ufe0f  ANSWER WARNING: {answer_msg}")
            results["warnings"].append({"test_case": test_case, "message": answer_msg})

        print(f"  \u2705 PASS: {message}")
        results["passed"].append(test_case)

    # Summary
    print(f"\n{'=' * 80}")
    print(f"{dataset_name.upper()} SUMMARY")
    print(f"{'=' * 80}")
    print(f"\u2705 Passed:  {len(results['passed'])}/{len(test_cases)}")
    print(f"\u274c Failed:  {len(results['failed'])}/{len(test_cases)}")
    print(f"\u26a0\ufe0f  Warnings: {len(results['warnings'])}/{len(test_cases)}")

    if results["failed"]:
        print(f"\n\u274c FAILED TEST CASES:")
        for item in results["failed"]:
            tc = item["test_case"]
            print(f"\n  [{tc.category}] {tc.question[:70]}...")
            print(f"  Issue: {item['message']}")
            if "mismatches" in item["details"]:
                for mm in item["details"]["mismatches"][:5]:
                    print(f"    - {mm['key']}: expected {mm['expected']}, got {mm['actual']}")

    if results["warnings"]:
        print(f"\n\u26a0\ufe0f  WARNINGS:")
        for item in results["warnings"]:
            tc = item["test_case"]
            print(f"  - {tc.question[:60]}... | {item['message']}")

    success_rate = len(results['passed']) / len(test_cases) * 100
    print(f"\n\U0001f4ca Success Rate: {success_rate:.1f}%")

    if len(results['failed']) == 0:
        print(f"\n\u2705 ALL {dataset_name.upper()} GROUND TRUTH IS CORRECT!")
    else:
        print(f"\n\u26a0\ufe0f  {len(results['failed'])} test cases need correction")

    print("=" * 80)

    return results


if __name__ == "__main__":
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "all"

    # Filter test cases by type
    sql_cases = [tc for tc in ALL_TEST_CASES if tc.test_type == TestType.SQL]
    hybrid_cases = [tc for tc in ALL_TEST_CASES if tc.test_type == TestType.HYBRID]

    all_results = {}

    if mode in ("sql", "all"):
        all_results["sql"] = verify_dataset(sql_cases, "SQL")

    if mode in ("hybrid", "all"):
        all_results["hybrid"] = verify_dataset(hybrid_cases, "Hybrid")

    if mode == "all" and len(all_results) == 2:
        total_passed = sum(len(r["passed"]) for r in all_results.values())
        total_failed = sum(len(r["failed"]) for r in all_results.values())
        total_cases = len(sql_cases) + len(hybrid_cases)

        print(f"\n{'=' * 80}")
        print("OVERALL SUMMARY")
        print(f"{'=' * 80}")
        print(f"\u2705 Passed:  {total_passed}/{total_cases}")
        print(f"\u274c Failed:  {total_failed}/{total_cases}")
        print(f"\U0001f4ca Overall Success Rate: {total_passed / total_cases * 100:.1f}%")
        print("=" * 80)
