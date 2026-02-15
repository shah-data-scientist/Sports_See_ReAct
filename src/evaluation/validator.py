"""
FILE: validator.py
STATUS: Active
RESPONSIBILITY: Ground truth validation and data generation helper
LAST MAJOR UPDATE: 2026-02-15
MAINTAINER: Shahu

RESPONSIBILITIES:
1. Validate that test cases have required ground truth fields filled
2. Generate missing ground_truth_data where possible (by executing queries)
3. Report "no result" for fields that cannot be auto-generated

Usage:
    poetry run python src/evaluation/validator.py              # Verify all test cases
"""
import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.evaluation.test_data import ALL_TEST_CASES

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
        return True, "No ground truth data", {"type": "no_data"}

    if actual and "__error__" in actual[0]:
        return False, f"Query error: {actual[0]['__error__']}", {"error": actual[0]["__error__"]}

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


def verify_all_test_cases() -> dict:
    """Verify all test cases and generate missing ground truth where possible."""
    print(f"\n{'=' * 80}")
    print(f"GROUND TRUTH VERIFICATION ({len(ALL_TEST_CASES)} test cases)")
    print(f"{'=' * 80}")

    results = {"passed": [], "failed": []}

    for i, test_case in enumerate(ALL_TEST_CASES, 1):
        question = test_case.question
        category = test_case.category

        print(f"\n[{i}/{len(ALL_TEST_CASES)}] {category}")
        print(f"Q: {question[:80]}...")

        # Check if test case has query and data fields
        has_query = test_case.expected_sql is not None and test_case.expected_sql.strip() != ""
        has_data = test_case.ground_truth_data is not None

        # Try to validate/generate expected_sql and ground_truth_data
        if not has_query:
            # Missing expected_sql - cannot auto-generate SQL from question
            print(f"  ⚠️  Missing expected_sql")
            print(f"  💡 RESULT: expected_sql = \"no result\"")
            print(f"  💡 RESULT: ground_truth_data = \"no result\"")
            results["failed"].append({
                "test_case": test_case,
                "message": "Missing expected_sql",
                "details": {
                    "expected_sql": "no result",
                    "ground_truth_data": "no result"
                }
            })

        elif has_query and has_data:
            # Has both query and data - verify they match
            actual_data = query_db(test_case.expected_sql)
            is_match, message, details = compare_results(test_case.ground_truth_data, actual_data)

            if not is_match:
                print(f"  ❌ DATA MISMATCH: {message}")
                if "mismatches" in details:
                    for mm in details["mismatches"][:3]:
                        print(f"     Row {mm['row']}, {mm['key']}: expected {mm['expected']}, got {mm['actual']}")
                results["failed"].append({"test_case": test_case, "message": message, "details": details})
            else:
                print(f"  ✅ PASS: {message}")
                results["passed"].append(test_case)

        elif has_query and not has_data:
            # Has query but missing data - try to generate it
            print(f"  ⚠️  Missing ground_truth_data - Attempting to generate...")
            actual_data = query_db(test_case.expected_sql)

            if actual_data and "__error__" not in actual_data[0]:
                import json
                suggested_value = actual_data[0] if len(actual_data) == 1 else actual_data
                print(f"  💡 GENERATED ground_truth_data:")
                print(f"     {json.dumps(suggested_value, indent=2)[:200]}...")
                results["failed"].append({
                    "test_case": test_case,
                    "message": "Missing ground_truth_data (but generated successfully)",
                    "details": {"generated": True, "suggested_value": suggested_value}
                })
            else:
                # Cannot execute query - set to "no result"
                print(f"  ❌ Cannot generate - Query error: {actual_data[0].get('__error__', 'Unknown')}")
                print(f"  💡 RESULT: ground_truth_data = \"no result\"")
                results["failed"].append({
                    "test_case": test_case,
                    "message": "Cannot generate ground_truth_data",
                    "details": {"ground_truth_data": "no result"}
                })


    # Summary
    print(f"\n{'=' * 80}")
    print(f"SUMMARY")
    print(f"{'=' * 80}")
    print(f"✅ Passed:  {len(results['passed'])}/{len(ALL_TEST_CASES)}")
    print(f"❌ Failed:  {len(results['failed'])}/{len(ALL_TEST_CASES)}")

    if results["failed"]:
        print(f"\n❌ FAILED TEST CASES:")
        for item in results["failed"]:
            tc = item["test_case"]
            print(f"\n  [{tc.category}] {tc.question[:70]}...")
            print(f"  Issue: {item['message']}")
            if "no_answer" in item["details"]:
                print(f"    ⚠️  No answer available - {item['details'].get('reason', 'Cannot generate data')}")
            elif "generated" in item["details"]:
                print(f"    💡 Generated value has been displayed above")
            elif "mismatches" in item["details"]:
                for mm in item["details"]["mismatches"][:5]:
                    print(f"    - {mm['key']}: expected {mm['expected']}, got {mm['actual']}")

    if len(ALL_TEST_CASES) > 0:
        success_rate = len(results['passed']) / len(ALL_TEST_CASES) * 100
        print(f"\n📊 Success Rate: {success_rate:.1f}%")

    if len(results['failed']) == 0:
        print(f"\n✅ ALL GROUND TRUTH IS CORRECT!")
    else:
        print(f"\n⚠️  {len(results['failed'])} test cases need correction")

    print("=" * 80)

    return results


if __name__ == "__main__":
    verify_all_test_cases()
