"""
FILE: analyze_sql_accuracy.py
STATUS: Active
RESPONSIBILITY: Calculate SQL accuracy metrics from evaluation results
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu

Calculates exact match, partial match, and semantic accuracy for SQL evaluations.
"""

import io
import json
import sys
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.sql_test_cases import SQL_TEST_CASES


def calculate_sql_accuracy(results_file: str):
    """Calculate accuracy metrics from SQL evaluation results.

    Metrics:
    - Exact Match: Response contains exact ground truth data
    - Partial Match: Response contains key data points
    - Execution Success: SQL query executed successfully
    - Classification Accuracy: Correctly classified as SQL
    """
    results_path = Path(results_file)
    if not results_path.exists():
        print(f"Error: Results file not found: {results_file}")
        return

    with open(results_path, encoding="utf-8") as f:
        data = json.load(f)

    # Build ground truth lookup
    ground_truth_map = {}
    for tc in SQL_TEST_CASES:
        ground_truth_map[tc.question] = {
            "answer": tc.ground_truth_answer,
            "data": tc.ground_truth_data,
        }

    # Calculate metrics
    total = len(data["results"])
    exact_match = 0
    partial_match = 0
    execution_success = data["successful"]
    classification_accuracy = data["classification_accuracy"]

    mismatches = []

    for result in data["results"]:
        question = result["question"]
        response = result["response"].lower()

        # Get ground truth
        if question not in ground_truth_map:
            continue

        gt = ground_truth_map[question]
        gt_data = gt["data"]

        # Check for exact match
        if isinstance(gt_data, dict):
            # Single record
            matched = all(str(val).lower() in response for val in gt_data.values())
            if matched:
                exact_match += 1
            elif any(str(val).lower() in response for val in gt_data.values()):
                partial_match += 1
            else:
                mismatches.append({
                    "question": question,
                    "expected": gt_data,
                    "got": response[:200],
                })
        elif isinstance(gt_data, list):
            # Multiple records - check if at least first 2 are present
            if len(gt_data) >= 2:
                first_two_match = all(
                    any(str(val).lower() in response for val in record.values())
                    for record in gt_data[:2]
                )
                if first_two_match:
                    exact_match += 1
                elif any(any(str(val).lower() in response for val in record.values()) for record in gt_data):
                    partial_match += 1
                else:
                    mismatches.append({
                        "question": question,
                        "expected": gt_data[:2],
                        "got": response[:200],
                    })
            else:
                # Single record in list
                matched = all(str(val).lower() in response for val in gt_data[0].values())
                if matched:
                    exact_match += 1
                else:
                    partial_match += 1

    # Calculate percentages
    exact_match_pct = (exact_match / total * 100) if total > 0 else 0
    partial_match_pct = (partial_match / total * 100) if total > 0 else 0
    combined_accuracy = ((exact_match + partial_match) / total * 100) if total > 0 else 0
    execution_success_pct = (execution_success / total * 100) if total > 0 else 0

    # Print report
    print("\n" + "="*80)
    print("  SQL ACCURACY ANALYSIS")
    print("="*80)
    print(f"  Evaluation File: {results_path.name}")
    print(f"  Timestamp: {data['timestamp']}")
    print(f"  Total Cases: {total}")
    print("="*80)

    print("\n" + "─"*80)
    print("  EXECUTION METRICS")
    print("─"*80)
    print(f"  Successful Execution: {execution_success}/{total} ({execution_success_pct:.1f}%)")
    print(f"  Failed Execution:     {data['failed']}/{total} ({100-execution_success_pct:.1f}%)")

    print("\n" + "─"*80)
    print("  CLASSIFICATION METRICS")
    print("─"*80)
    print(f"  Classification Accuracy: {classification_accuracy:.1f}%")
    print(f"  Misclassifications:      {len(data['misclassifications'])}")

    print("\n" + "─"*80)
    print("  ANSWER ACCURACY METRICS")
    print("─"*80)
    print(f"  Exact Match:     {exact_match}/{total} ({exact_match_pct:.1f}%)")
    print(f"  Partial Match:   {partial_match}/{total} ({partial_match_pct:.1f}%)")
    print(f"  Combined:        {exact_match + partial_match}/{total} ({combined_accuracy:.1f}%)")
    print(f"  Mismatches:      {len(mismatches)}/{total} ({100-combined_accuracy:.1f}%)")

    print("\n" + "─"*80)
    print("  CATEGORY BREAKDOWN")
    print("─"*80)
    for category, count in sorted(data["category_counts"].items()):
        print(f"  {category:40} {count:>3} cases")

    if mismatches:
        print("\n" + "─"*80)
        print("  MISMATCHES (First 5)")
        print("─"*80)
        for i, m in enumerate(mismatches[:5], 1):
            print(f"\n  [{i}] {m['question']}")
            print(f"      Expected: {m['expected']}")
            print(f"      Got: {m['got']}...")

    print("\n" + "="*80)
    print("  SUMMARY")
    print("="*80)
    print(f"  Overall Accuracy:  {combined_accuracy:.1f}%")
    print(f"  Execution Success: {execution_success_pct:.1f}%")
    print(f"  Classification:    {classification_accuracy:.1f}%")
    print("="*80 + "\n")

    return {
        "total": total,
        "exact_match": exact_match,
        "partial_match": partial_match,
        "execution_success": execution_success,
        "classification_accuracy": classification_accuracy,
        "mismatches": len(mismatches),
    }


if __name__ == "__main__":
    # Use most recent SQL evaluation
    results_file = "evaluation_results/sql_evaluation_20260211_061045.json"
    calculate_sql_accuracy(results_file)
