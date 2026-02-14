"""Regenerate SQL evaluation report from updated JSON.

Usage:
    poetry run python scripts/regenerate_sql_report.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.runners.run_sql_evaluation import generate_comprehensive_report


def main():
    """Regenerate report and clean up."""
    print("\n" + "=" * 80)
    print("REGENERATE SQL EVALUATION REPORT")
    print("=" * 80)

    results_dir = Path("evaluation_results")
    
    # Find latest JSON
    json_files = sorted(results_dir.glob("sql_evaluation_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not json_files:
        print("ERROR: No SQL evaluation JSON files found")
        return
    
    latest_json = json_files[0]
    print(f"\n1. Using JSON: {latest_json.name}")
    
    # Load results
    results = json.loads(latest_json.read_text(encoding="utf-8"))
    print(f"   Total queries: {len(results)}")
    print(f"   Successful: {sum(1 for r in results if r.get('success', False))}/{len(results)}")
    
    # Generate report
    print(f"\n2. Generating comprehensive report...")
    report_path = generate_comprehensive_report(results, latest_json.name)
    print(f"   Report saved: {report_path}")
    
    # Clean up old files
    print(f"\n3. Cleaning up old SQL evaluation files...")
    old_files = []
    for f in results_dir.glob("sql_evaluation_*"):
        if f.name not in [latest_json.name, Path(report_path).name]:
            old_files.append(f)
    
    if old_files:
        print(f"   Found {len(old_files)} old files:")
        for f in old_files:
            print(f"     - {f.name}")
            f.unlink()
        print(f"   ✅ Deleted {len(old_files)} old files")
    else:
        print(f"   No old files to delete")
    
    # Summary
    success_count = sum(1 for r in results if r.get('success', False))
    print("\n" + "=" * 80)
    print("REGENERATION COMPLETE")
    print("=" * 80)
    print(f"\n✓ JSON: {latest_json.name}")
    print(f"✓ Report: {Path(report_path).name}")
    print(f"✓ Success Rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    print(f"✓ Cleaned: {len(old_files)} old files")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
