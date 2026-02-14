"""
FILE: generate_comparative_report.py
STATUS: Active
RESPONSIBILITY: Generate Phase 3 comparative analysis report with charts
LAST MAJOR UPDATE: 2026-02-07
MAINTAINER: Shahu
"""

import json
from pathlib import Path


def load_evaluation_results():
    """Load all evaluation results."""
    results_dir = Path("evaluation_results")

    baseline = json.loads((results_dir / "ragas_baseline.json").read_text(encoding="utf-8"))

    phase2_path = results_dir / "ragas_phase2.json"
    phase2 = json.loads(phase2_path.read_text(encoding="utf-8")) if phase2_path.exists() else None

    phase5_path = results_dir / "ragas_phase5_extended.json"
    phase5 = json.loads(phase5_path.read_text(encoding="utf-8")) if phase5_path.exists() else None

    return {
        "baseline": baseline,
        "phase2": phase2,
        "phase5": phase5,
    }


def calculate_improvements(baseline, current):
    """Calculate percentage improvements."""
    improvements = {}
    for metric in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
        baseline_val = baseline["overall_scores"].get(metric, 0) or 0
        current_val = current["overall_scores"].get(metric, 0) or 0

        if baseline_val > 0:
            pct_change = ((current_val - baseline_val) / baseline_val) * 100
        else:
            pct_change = 0 if current_val == 0 else 100

        improvements[metric] = {
            "baseline": baseline_val,
            "current": current_val,
            "absolute_change": current_val - baseline_val,
            "percent_change": pct_change,
        }

    return improvements


def print_executive_summary(results):
    """Print executive summary."""
    print("\n" + "=" * 100)
    print("  PHASE 3: COMPARATIVE EVALUATION ANALYSIS")
    print("  NBA RAG System - SQL Integration Impact Assessment")
    print("=" * 100)

    baseline = results["baseline"]
    phase2 = results["phase2"]
    phase5 = results["phase5"]

    print("\n  EVALUATION TIMELINE")
    print("  " + "-" * 94)
    print(f"  Baseline (Phase 1)  : {baseline.get('timestamp', 'N/A')}")
    print(f"    - Configuration   : Vector search only (FAISS, 302 documents)")
    print(f"    - Test cases      : {baseline.get('sample_count', 0)} (original set)")

    if phase2:
        print(f"\n  Phase 2 Evaluation  : {phase2.get('timestamp', 'N/A')}")
        print(f"    - Configuration   : Vector + SQL hybrid (569 players, 45 stats)")
        print(f"    - Test cases      : {phase2.get('sample_count', 0)} (same as baseline)")

    if phase5:
        print(f"\n  Phase 5 Evaluation  : {phase5.get('timestamp', 'N/A')}")
        print(f"    - Configuration   : Vector + SQL hybrid")
        print(f"    - Test cases      : {phase5.get('sample_count', 0)} (extended with hybrid scenarios)")

    print("  " + "-" * 94)


def print_comparison_table(results):
    """Print side-by-side comparison table."""
    baseline = results["baseline"]
    phase2 = results["phase2"]
    phase5 = results["phase5"]

    def fmt(val):
        return f"{val:.3f}" if val is not None else "N/A  "

    def pct(val):
        sign = "+" if val > 0 else ""
        return f"{sign}{val:>6.1f}%"

    print("\n  OVERALL METRICS COMPARISON")
    print("  " + "=" * 94)
    print(f"  {'Metric':<20} {'Baseline':>10} {'Phase 2':>10} {'Change':>10} {'Phase 5':>10} {'Change':>10}")
    print("  " + "-" * 94)

    metrics = [
        ("Faithfulness", "faithfulness"),
        ("Answer Relevancy", "answer_relevancy"),
        ("Context Precision", "context_precision"),
        ("Context Recall", "context_recall"),
    ]

    for label, key in metrics:
        base_val = baseline["overall_scores"].get(key, 0) or 0

        p2_val = phase2["overall_scores"].get(key, 0) if phase2 else None
        p2_delta = ((p2_val - base_val) / base_val * 100) if p2_val is not None and base_val > 0 else None

        p5_val = phase5["overall_scores"].get(key, 0) if phase5 else None
        p5_delta = ((p5_val - base_val) / base_val * 100) if p5_val is not None and base_val > 0 else None

        print(f"  {label:<20} {fmt(base_val):>10} "
              f"{fmt(p2_val) if p2_val is not None else 'N/A      ':>10} "
              f"{pct(p2_delta) if p2_delta is not None else 'N/A      ':>10} "
              f"{fmt(p5_val) if p5_val is not None else 'N/A      ':>10} "
              f"{pct(p5_delta) if p5_delta is not None else 'N/A      ':>10}")

    print("  " + "=" * 94)


def print_category_analysis(results):
    """Print category-level analysis."""
    print("\n  PERFORMANCE BY QUERY CATEGORY")
    print("  " + "=" * 94)

    categories = ["simple", "complex", "noisy", "conversational"]

    for cat in categories:
        print(f"\n  {cat.upper()} QUERIES")
        print("  " + "-" * 94)

        # Find category results
        baseline_cat = next((c for c in results["baseline"]["category_scores"] if c["category"] == cat), None)
        phase2_cat = next((c for c in results["phase2"]["category_scores"] if c["category"] == cat), None) if results["phase2"] else None
        phase5_cat = next((c for c in results["phase5"]["category_scores"] if c["category"] == cat), None) if results["phase5"] else None

        if not baseline_cat:
            continue

        metrics_display = [
            ("Faithfulness", "faithfulness"),
            ("Answer Relevancy", "answer_relevancy"),
            ("Context Precision", "context_precision"),
            ("Context Recall", "context_recall"),
        ]

        for label, key in metrics_display:
            base_val = baseline_cat.get(key, 0) or 0
            p2_val = phase2_cat.get(key, 0) if phase2_cat else None
            p5_val = phase5_cat.get(key, 0) if phase5_cat else None

            def fmt(v):
                return f"{v:.3f}" if v is not None else "N/A  "

            def delta(curr, base):
                if curr is not None and base > 0:
                    pct = ((curr - base) / base) * 100
                    sign = "+" if pct > 0 else ""
                    return f"{sign}{pct:>6.1f}%"
                return "N/A      "

            print(f"    {label:<18} Base: {fmt(base_val)}  "
                  f"P2: {fmt(p2_val)} ({delta(p2_val, base_val)})  "
                  f"P5: {fmt(p5_val)} ({delta(p5_val, base_val)})")

    print("  " + "=" * 94)


def print_key_findings(results):
    """Print key findings and analysis."""
    print("\n  KEY FINDINGS")
    print("  " + "=" * 94)

    baseline = results["baseline"]
    phase2 = results["phase2"]
    phase5 = results["phase5"]

    if phase2:
        p2_improvements = calculate_improvements(baseline, phase2)

        print("\n  PHASE 2 IMPACT (SQL Integration on Existing Test Cases)")
        print("  " + "-" * 94)

        for metric, data in p2_improvements.items():
            label = metric.replace("_", " ").title()
            symbol = "+" if data["percent_change"] > 0 else ("-" if data["percent_change"] < 0 else "=")
            print(f"    {symbol} {label:<20} {data['baseline']:.3f} -> {data['current']:.3f} "
                  f"({data['percent_change']:+.1f}%)")

    if phase5:
        p5_improvements = calculate_improvements(baseline, phase5)

        print("\n  PHASE 5 IMPACT (Extended Hybrid Test Cases)")
        print("  " + "-" * 94)

        for metric, data in p5_improvements.items():
            label = metric.replace("_", " ").title()
            symbol = "+" if data["percent_change"] > 0 else ("-" if data["percent_change"] < 0 else "=")
            print(f"    {symbol} {label:<20} {data['baseline']:.3f} -> {data['current']:.3f} "
                  f"({data['percent_change']:+.1f}%)")

    print("  " + "=" * 94)


def print_bias_analysis():
    """Print bias and limitations analysis."""
    print("\n  BIAS & LIMITATIONS ANALYSIS")
    print("  " + "=" * 94)

    print("\n  1. NATURAL LANGUAGE → SQL MAPPING LIMITATIONS")
    print("  " + "-" * 94)
    print("    • Ambiguous queries: 'best player' → multiple interpretations (PPG, PER, WS)")
    print("    • Column name mapping: Users say 'three-pointers' not 'three_pm'")
    print("    • Aggregation complexity: Multi-step calculations may fail")
    print("    • Few-shot coverage: 8 examples don't cover all query patterns")
    print("    • Temperature=0.0 trade-off: Deterministic but less creative")

    print("\n  2. QUERY CLASSIFICATION BIAS")
    print("  " + "-" * 94)
    print("    • Pattern-based classifier: Rule-based, not ML → brittle to new patterns")
    print("    • False positives: 'compare' triggers STATISTICAL even if qualitative")
    print("    • Keyword dependency: Relies on specific words (points, rebounds, etc.)")
    print("    • Context loss: Conversational queries may misclassify without history")
    print("    • Tie-breaking: Defaults to CONTEXTUAL when stat/context patterns equal")

    print("\n  3. TEST CASE COVERAGE GAPS")
    print("  " + "-" * 94)
    print("    • Single season only: No historical comparisons (Jordanvs LeBron era)")
    print("    • No game-level data: Can't answer 'last 5 games' queries accurately")
    print("    • Team stats missing: Player-centric, limited team-level queries")
    print("    • Advanced metrics: PER, WS, VORP in DB but not in documents")
    print("    • Real-time data: Static snapshot, no live scores/updates")

    print("\n  4. EVALUATION METHODOLOGY BIAS")
    print("  " + "-" * 94)
    print("    • Ground truth quality: Hand-written, may not match RAGAS expectations")
    print("    • Evaluator model bias: Gemini Flash Lite preferences != human judgment")
    print("    • Context window limits: Long SQL results may truncate")
    print("    • Metric correlation: High faithfulness doesn't guarantee usefulness")
    print("    • Sample size: 47-80 test cases may not represent production distribution")

    print("\n  5. HYBRID ROUTING EDGE CASES")
    print("  " + "-" * 94)
    print("    • SQL failure fallback: No graceful degradation to vector-only")
    print("    • Context combination: SQL + Vector results may contradict")
    print("    • Token budget: Hybrid context = 2x size → higher costs")
    print("    • Latency: SQL query + Vector search + LLM = 2-3s total")
    print("    • Cache misses: No result caching → repeated queries cost API calls")

    print("\n  6. DATA QUALITY & REPRESENTATION BIAS")
    print("  " + "-" * 94)
    print("    • Excel formatting issues: Time formats, missing values, encoding")
    print("    • Static team abbreviations: Hardcoded, no validation against roster moves")
    print("    • Missing player metadata: No injury status, contract info, draft year")
    print("    • Stats normalization: Per-game vs totals confusion")
    print("    • Sample bias: 569 players ≠ all active NBA players")

    print("  " + "=" * 94)


def print_recommendations():
    """Print recommendations."""
    print("\n  RECOMMENDATIONS FOR IMPROVEMENT")
    print("  " + "=" * 94)

    print("\n  HIGH PRIORITY")
    print("  " + "-" * 94)
    print("    1. Add ML-based query classifier (replace regex patterns)")
    print("    2. Implement SQL fallback to vector search on tool failure")
    print("    3. Expand few-shot examples to 15-20 covering edge cases")
    print("    4. Add query result caching (Redis) to reduce API costs")
    print("    5. Implement context de-duplication for hybrid results")

    print("\n  MEDIUM PRIORITY")
    print("  " + "-" * 94)
    print("    6. Add multi-season historical data support")
    print("    7. Create team-level statistics table")
    print("    8. Implement conversational context tracking")
    print("    9. Add query explanation (show SQL to user)")
    print("    10. Build confidence scores for classification")

    print("\n  LOW PRIORITY / FUTURE")
    print("  " + "-" * 94)
    print("    11. Real-time data integration via API")
    print("    12. Advanced metric calculation (PER, BPM, Win Shares)")
    print("    13. Natural language column aliasing (points → pts)")
    print("    14. Multi-turn query optimization")
    print("    15. User feedback loop for classification improvement")

    print("  " + "=" * 94)


def generate_ascii_chart(metric_name, baseline_val, phase2_val, phase5_val):
    """Generate simple ASCII bar chart."""
    max_val = max(baseline_val, phase2_val or 0, phase5_val or 0, 1.0)
    scale = 50  # characters

    def bar(val):
        if val is None:
            return "N/A"
        length = int((val / max_val) * scale)
        return "[" + "#" * length + "-" * (scale - length) + "] " + f"{val:.3f}"

    print(f"\n  {metric_name.upper()}")
    print(f"  Baseline (P1): {bar(baseline_val)}")
    if phase2_val is not None:
        print(f"  Phase 2      : {bar(phase2_val)}")
    if phase5_val is not None:
        print(f"  Phase 5      : {bar(phase5_val)}")


def print_visual_comparison(results):
    """Print ASCII charts for visual comparison."""
    print("\n  VISUAL PERFORMANCE COMPARISON")
    print("  " + "=" * 94)

    baseline = results["baseline"]["overall_scores"]
    phase2 = results["phase2"]["overall_scores"] if results["phase2"] else {}
    phase5 = results["phase5"]["overall_scores"] if results["phase5"] else {}

    metrics = [
        ("Faithfulness", "faithfulness"),
        ("Answer Relevancy", "answer_relevancy"),
        ("Context Precision", "context_precision"),
        ("Context Recall", "context_recall"),
    ]

    for label, key in metrics:
        generate_ascii_chart(
            label,
            baseline.get(key, 0) or 0,
            phase2.get(key),
            phase5.get(key),
        )

    print("\n  " + "=" * 94)


def save_report(results):
    """Save comprehensive report to file."""
    report_path = Path("evaluation_results/PHASE3_COMPARATIVE_REPORT.md")

    # This would write the entire report to markdown
    # For now, we'll just indicate it's been generated
    print(f"\n  [INFO] Full report would be saved to: {report_path}")


def main():
    """Generate comparative analysis report."""
    try:
        results = load_evaluation_results()

        print_executive_summary(results)
        print_comparison_table(results)
        print_visual_comparison(results)
        print_category_analysis(results)
        print_key_findings(results)
        print_bias_analysis()
        print_recommendations()

        print("\n" + "=" * 100)
        print("  END OF PHASE 3 COMPARATIVE ANALYSIS REPORT")
        print("=" * 100 + "\n")

    except FileNotFoundError as e:
        print(f"\n[ERROR] Missing evaluation results: {e}")
        print("Run evaluations first:")
        print("  1. Baseline already exists: evaluation_results/ragas_baseline.json")
        print("  2. Phase 2: poetry run python scripts/evaluate_phase2.py")
        print("  3. Phase 5: poetry run python scripts/evaluate_phase5.py")
        return 1

    except Exception as e:
        print(f"\n[ERROR] Failed to generate report: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
