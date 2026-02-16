"""
Generate SQL evaluation report from checkpoint results.
"""
import json
from datetime import datetime
from pathlib import Path
from evaluation.runners.run_sql_evaluation import generate_comprehensive_report

def generate_report():
    """Generate comprehensive SQL evaluation report from checkpoint."""

    # Load checkpoint
    checkpoint_path = Path("evaluation_results/sql_evaluation_checkpoint.json")
    with open(checkpoint_path, 'r', encoding='utf-8') as f:
        checkpoint_data = json.load(f)

    results = checkpoint_data['results']
    completed = checkpoint_data['completed']

    print(f"Loaded {completed} completed test cases from checkpoint")

    # Generate comprehensive report using the runner's function
    print("Generating comprehensive report...")
    report_path = generate_comprehensive_report(results, str(checkpoint_path))

    print(f"\n✅ Report generated successfully!")
    print(f"📄 Report path: {report_path}")

    # Print summary stats
    total = len(results)
    successful = sum(1 for r in results if r.get("success", False))
    failed = total - successful
    success_rate = (successful / total * 100) if total > 0 else 0

    misclassified = sum(1 for r in results if r.get("is_misclassified", False))
    classification_accuracy = ((total - misclassified) / total * 100) if total > 0 else 0

    processing_times = [r["processing_time_ms"] for r in results if r.get("success", False)]
    avg_time = sum(processing_times) / len(processing_times) if processing_times else 0

    print("\n" + "="*80)
    print("SQL EVALUATION SUMMARY")
    print("="*80)
    print(f"Total test cases:        {total}")
    print(f"Successful:              {successful} ({success_rate:.1f}%)")
    print(f"Failed:                  {failed}")
    print(f"Classification accuracy: {classification_accuracy:.1f}%")
    print(f"Misclassifications:      {misclassified}")
    print(f"Average processing time: {avg_time:.0f}ms")
    print("="*80)

    return report_path

if __name__ == "__main__":
    generate_report()
