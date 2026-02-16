"""
FILE: regenerate_reports.py
STATUS: Active
RESPONSIBILITY: Regenerate MD reports from updated evaluation JSON files
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import io
import json
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))


def regenerate_hybrid_report():
    """Regenerate hybrid MD report from updated JSON."""
    from evaluation.analyzer import analyze_results
    from evaluation.test_data import ALL_TEST_CASES
    from evaluation.models import TestType

    json_path = Path("evaluation_results/hybrid_evaluation_20260212_070628.json")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    results = data["results"]

    # Re-run analysis
    analysis = analyze_hybrid_results(results, HYBRID_TEST_CASES)

    # Regenerate report
    report_path = json_path.with_name("hybrid_evaluation_report_20260212_070628.md")
    generate_markdown_report(results, analysis, HYBRID_TEST_CASES, report_path)

    print(f"Hybrid report regenerated: {report_path}")


def regenerate_vector_report():
    """Regenerate vector MD report from updated JSON."""
    from evaluation.analyzer import analyze_results
    from evaluation.test_data import ALL_TEST_CASES
    from evaluation.models import TestType

    json_path = Path("evaluation_results/vector_evaluation_20260212_055129.json")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    results = data["results"]

    # The vector runner generates its own report - check for existing report generator
    report_path = json_path.with_name("vector_evaluation_report_20260212_055129.md")

    # Run all analyses
    source_quality = analyze_source_quality(results)
    response_patterns = analyze_response_patterns(results)
    retrieval_perf = analyze_retrieval_performance(results)
    category_perf = analyze_category_performance(results)
    ragas = analyze_ragas_metrics(results)

    total = len(results)
    successful = sum(1 for r in results if r.get("success"))
    times = [r.get("processing_time_ms", 0) for r in results if r.get("success")]

    lines = [
        "# Vector Evaluation Report",
        "",
        f"**Total Queries:** {total}",
        f"**Successful:** {successful}/{total} ({successful/total*100:.1f}%)",
        f"**Failed:** {total - successful}",
        f"**Avg Processing Time:** {sum(times)/len(times):.0f}ms" if times else "",
        "",
        "---",
        "",
        "## Source Quality",
        f"- Avg sources per query: {source_quality.get('avg_sources', 0):.1f}",
        f"- Avg similarity score: {source_quality.get('avg_similarity', 0):.1f}%",
        "",
        "## Response Patterns",
        f"- Avg response length: {response_patterns.get('avg_length', 0):.0f} chars",
        "",
        "## RAGAS Metrics",
    ]

    if ragas:
        for metric, value in ragas.items():
            if isinstance(value, (int, float)):
                lines.append(f"- **{metric}:** {value:.3f}")

    lines.extend(["", "## Category Performance", ""])
    if category_perf:
        lines.append("| Category | Details |")
        lines.append("|----------|---------|")
        for cat, stats in category_perf.items():
            if isinstance(stats, dict):
                lines.append(f"| {cat} | {stats.get('count', 0)} queries, {stats.get('avg_time', 0):.0f}ms avg |")
            elif isinstance(stats, list):
                lines.append(f"| {cat} | {len(stats)} entries |")
            else:
                lines.append(f"| {cat} | {stats} |")

    lines.extend([
        "",
        "## Detailed Results",
        "",
    ])

    for i, r in enumerate(results, 1):
        status = "PASS" if r.get("success") else "FAIL"
        lines.extend([
            f"### {i}. [{status}] {r['question'][:80]}",
            "",
            f"- **Category:** {r.get('category', 'unknown')}",
            f"- **Routing:** {r.get('actual_routing', 'N/A')}",
            f"- **Sources:** {r.get('sources_count', 0)}",
            f"- **Time:** {r.get('processing_time_ms', 0):.0f}ms",
            f"- **Response:** {r.get('response', '')[:300]}{'...' if len(r.get('response', '')) > 300 else ''}",
            "",
        ])
        if r.get("error"):
            lines.append(f"- **Error:** {r['error'][:200]}")
            lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Vector report regenerated: {report_path}")


if __name__ == "__main__":
    regenerate_hybrid_report()
    regenerate_vector_report()
    print("\nAll reports regenerated!")
