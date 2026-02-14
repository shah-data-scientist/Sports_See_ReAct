"""
FILE: compare_classifications.py
STATUS: Active
RESPONSIBILITY: Compare SQL and Vector evaluation results to analyze classification accuracy
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu
"""

import json
import sys
from pathlib import Path
from collections import Counter


def load_latest_evaluation(eval_type: str) -> dict | None:
    """Load the most recent evaluation result file.

    Args:
        eval_type: Either 'sql' or 'vector'

    Returns:
        Evaluation data dict or None if not found
    """
    results_dir = Path("evaluation_results")
    if not results_dir.exists():
        return None

    # Find latest file matching pattern
    pattern = f"{eval_type}_evaluation_*.json"
    files = sorted(results_dir.glob(pattern), reverse=True)

    if not files:
        return None

    latest_file = files[0]
    print(f"Loading {eval_type} evaluation from: {latest_file.name}")

    with open(latest_file, encoding="utf-8") as f:
        return json.load(f)


def analyze_misclassifications(sql_data: dict, vector_data: dict):
    """Analyze and compare misclassifications from both evaluations."""

    print("\n" + "="*100)
    print("  CLASSIFICATION COMPARISON REPORT")
    print("="*100)

    # SQL Evaluation Analysis
    print("\n[1] SQL EVALUATION")
    print("-" * 100)
    print(f"Total Test Cases: {sql_data['total_cases']}")
    print(f"Routing Distribution:")
    for route, count in sql_data['routing_stats'].items():
        print(f"  {route:15}: {count:3} ({count/sql_data['total_cases']*100:5.1f}%)")
    print(f"\nClassification Accuracy: {sql_data['classification_accuracy']:.1f}%")
    print(f"Misclassifications: {len(sql_data['misclassifications'])}")

    # Analyze SQL misclassification patterns
    if sql_data['misclassifications']:
        sql_misc_types = Counter(m['actual'] for m in sql_data['misclassifications'])
        print(f"\nMisclassification Breakdown:")
        for misc_type, count in sql_misc_types.most_common():
            print(f"  SQL queries wrongly routed to {misc_type:15}: {count}")

    # Vector Evaluation Analysis
    print("\n[2] VECTOR EVALUATION")
    print("-" * 100)
    print(f"Total Test Cases: {vector_data['total_cases']}")
    print(f"Routing Distribution:")
    for route, count in vector_data['routing_stats'].items():
        print(f"  {route:15}: {count:3} ({count/vector_data['total_cases']*100:5.1f}%)")
    print(f"\nClassification Accuracy: {vector_data['classification_accuracy']:.1f}%")
    print(f"Misclassifications: {len(vector_data['misclassifications'])}")

    # Analyze Vector misclassification patterns
    if vector_data['misclassifications']:
        vector_misc_types = Counter(m['actual'] for m in vector_data['misclassifications'])
        print(f"\nMisclassification Breakdown:")
        for misc_type, count in vector_misc_types.most_common():
            print(f"  Vector queries wrongly routed to {misc_type:15}: {count}")

    # Overall Statistics
    print("\n[3] OVERALL CLASSIFICATION PERFORMANCE")
    print("-" * 100)
    total_cases = sql_data['total_cases'] + vector_data['total_cases']
    sql_correct = sql_data['routing_stats']['sql_only']
    vector_correct = vector_data['routing_stats']['vector_only']
    total_correct = sql_correct + vector_correct
    overall_accuracy = (total_correct / total_cases * 100) if total_cases else 0

    print(f"Total Test Cases: {total_cases}")
    print(f"Correctly Classified: {total_correct}")
    print(f"Overall Accuracy: {overall_accuracy:.1f}%")

    # Error Analysis
    print("\n[4] ERROR ANALYSIS")
    print("-" * 100)

    # SQL → Vector errors (false negatives for SQL)
    sql_to_vector = [m for m in sql_data['misclassifications'] if m['actual'] == 'vector_only']
    if sql_to_vector:
        print(f"\nSQL queries misclassified as VECTOR ({len(sql_to_vector)} cases):")
        print("These are statistical queries that should use SQL but got routed to vector search.")
        print("\nTop 5 examples:")
        for i, misc in enumerate(sql_to_vector[:5], 1):
            print(f"\n  [{i}] Question: {misc['question']}")
            print(f"      Category: {misc['category']}")
            print(f"      Response: {misc['response_preview']}...")

    # Vector → SQL errors (false positives for SQL)
    vector_to_sql = [m for m in vector_data['misclassifications'] if m['actual'] == 'sql_only']
    if vector_to_sql:
        print(f"\n\nVECTOR queries misclassified as SQL ({len(vector_to_sql)} cases):")
        print("These are contextual queries that should use vector search but got routed to SQL.")
        print("\nTop 5 examples:")
        for i, misc in enumerate(vector_to_sql[:5], 1):
            print(f"\n  [{i}] Question: {misc['question']}")
            print(f"      Category: {misc['category']}")
            print(f"      Response: {misc['response_preview']}...")

    # Hybrid routing analysis
    sql_to_hybrid = [m for m in sql_data['misclassifications'] if m['actual'] == 'hybrid']
    vector_to_hybrid = [m for m in vector_data['misclassifications'] if m['actual'] == 'hybrid']

    if sql_to_hybrid or vector_to_hybrid:
        print(f"\n\nHYBRID routing (unexpected):")
        print(f"  SQL queries routed to HYBRID: {len(sql_to_hybrid)}")
        print(f"  Vector queries routed to HYBRID: {len(vector_to_hybrid)}")
        print("\nNote: Hybrid routing means both SQL and Vector were used.")
        print("For pure SQL/Vector test cases, this indicates over-aggressive classification.")

    # Recommendations
    print("\n[5] RECOMMENDATIONS")
    print("-" * 100)

    if sql_data['classification_accuracy'] < 80:
        print("\n⚠️  SQL classification accuracy is low (<80%)")
        print("   → Review QueryClassifier STATISTICAL_PATTERNS")
        print("   → Add more explicit SQL keywords/patterns")
        print("   → Check if test cases are actually suitable for SQL")

    if vector_data['classification_accuracy'] < 80:
        print("\n⚠️  Vector classification accuracy is low (<80%)")
        print("   → Review QueryClassifier CONTEXTUAL_PATTERNS")
        print("   → Ensure contextual keywords are properly detected")
        print("   → Check if test cases are truly contextual queries")

    if len(sql_to_vector) > 5:
        print("\n⚠️  Many SQL queries are being routed to Vector")
        print("   → Classifier may be too conservative with SQL classification")
        print("   → Consider making STATISTICAL_PATTERNS more aggressive")

    if len(vector_to_sql) > 5:
        print("\n⚠️  Many Vector queries are being routed to SQL")
        print("   → Classifier may be too aggressive with SQL classification")
        print("   → Consider strengthening CONTEXTUAL_PATTERNS priority")

    print("\n" + "="*100)


def main():
    """Run classification comparison analysis."""

    # Load both evaluation results
    sql_data = load_latest_evaluation("sql")
    vector_data = load_latest_evaluation("vector")

    if not sql_data:
        print("❌ SQL evaluation results not found. Run: poetry run python scripts/evaluate_sql.py")
        sys.exit(1)

    if not vector_data:
        print("❌ Vector evaluation results not found. Run: poetry run python scripts/evaluate_vector.py")
        sys.exit(1)

    # Check if files have classification data (new format)
    if 'routing_stats' not in sql_data:
        print("❌ SQL evaluation file is in old format. Please re-run: poetry run python scripts/evaluate_sql.py")
        sys.exit(1)

    if 'routing_stats' not in vector_data:
        print("❌ Vector evaluation file is in old format. Please re-run: poetry run python scripts/evaluate_vector.py")
        sys.exit(1)

    # Analyze and compare
    analyze_misclassifications(sql_data, vector_data)

    print("\n✅ Comparison complete!")
    print("\nTo fix classification issues:")
    print("  1. Review the error examples above")
    print("  2. Update patterns in: src/services/query_classifier.py")
    print("  3. Re-run evaluations to verify improvements")


if __name__ == "__main__":
    main()
