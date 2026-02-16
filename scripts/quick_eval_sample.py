"""
FILE: quick_eval_sample.py
STATUS: Active
RESPONSIBILITY: Quick sample evaluation test - run 2 queries per evaluation type and verify metrics
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import json
from datetime import datetime
from pathlib import Path

# Run existing evaluation runners with small sample sets
from evaluation.runners.run_sql_evaluation import run_evaluation as run_sql_eval
from evaluation.runners.run_vector_evaluation import run_evaluation as run_vector_eval

TEST_OUTPUT_DIR = Path("evaluation_results/test_run_2026_02_12")


def main():
    """Run quick sample evaluations for verification."""
    print("\n" + "=" * 80)
    print("QUICK SAMPLE EVALUATION - METRICS VERIFICATION")
    print("=" * 80)
    print(f"\nOutput directory: {TEST_OUTPUT_DIR.absolute()}")

    # Create output directory
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Run evaluations and collect reports
    reports = []

    print("\n[1/2] Running SQL sample evaluation...")
    try:
        sql_files = run_sql_eval(sample_size=2)
        print(f"✓ SQL evaluation complete")
        if sql_files:
            reports.append(("SQL", sql_files))
    except Exception as e:
        print(f"✗ SQL evaluation error: {e}")

    print("\n[2/2] Running Vector sample evaluation...")
    try:
        vector_files = run_vector_eval(sample_size=2)
        print(f"✓ Vector evaluation complete")
        if vector_files:
            reports.append(("Vector", vector_files))
    except Exception as e:
        print(f"✗ Vector evaluation error: {e}")

    # Summarize results
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)

    for eval_type, files in reports:
        print(f"\n{eval_type.upper()} EVALUATION:")
        if isinstance(files, dict):
            for file_type, path in files.items():
                print(f"  {file_type}: {path}")
                if "report" in file_type.lower() and Path(path).exists():
                    # Read and check for metrics in report
                    content = Path(path).read_text(encoding="utf-8")
                    has_metrics = all(keyword in content for keyword in [
                        "Execution Summary", "total_queries", "successful"
                    ])
                    if has_metrics:
                        print(f"    ✓ Metrics present")
                    else:
                        print(f"    ⚠ Some metrics may be missing")

    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print("\nCheck the markdown reports in evaluation_results/test_run_2026_02_12/")
    print("to verify that all metrics are present.")


if __name__ == "__main__":
    main()
