"""
FILE: generate_sql_matrix_report.py
STATUS: Active
RESPONSIBILITY: Generate a matrix evaluation report for the SQL dataset
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import io
import json
import re
import sys
from pathlib import Path
from statistics import mean, stdev

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def load_latest_evaluation() -> dict:
    """Load the most recent SQL evaluation JSON file."""
    results_dir = Path("evaluation_results")
    files = sorted(results_dir.glob("sql_evaluation_*.json"), reverse=True)
    if not files:
        raise FileNotFoundError("No SQL evaluation results found in evaluation_results/")
    with open(files[0], encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded evaluation: {files[0].name} ({data['timestamp']})")
    return data


def load_test_cases() -> list[dict]:
    """Load test cases with ground truth from the test case module."""
    from evaluation.sql_test_cases import SQL_TEST_CASES
    cases = []
    for tc in SQL_TEST_CASES:
        cases.append({
            "question": tc.question,
            "category": tc.category,
            "expected_sql": tc.expected_sql,
            "ground_truth_answer": tc.ground_truth_answer,
            "ground_truth_data": tc.ground_truth_data,
        })
    return cases


def extract_numbers(text: str) -> list[float]:
    """Extract numeric values from a response string."""
    # Match integers and decimals, including comma-separated thousands
    numbers = re.findall(r"[\d,]+\.?\d*", text)
    result = []
    for n in numbers:
        try:
            result.append(float(n.replace(",", "")))
        except ValueError:
            pass
    return result


def check_ground_truth_match(response: str, ground_truth_data, ground_truth_answer: str) -> dict:
    """Check if the response matches ground truth data."""
    if ground_truth_data is None:
        return {"match": "no_gt", "detail": "No ground truth data defined"}

    response_lower = response.lower().strip()

    # Check for "cannot find" / "no information" type failures
    failure_phrases = [
        "available context doesn't contain",
        "cannot find",
        "no information",
        "i don't have",
        "not available",
        "i couldn't find",
    ]
    for phrase in failure_phrases:
        if phrase in response_lower:
            return {"match": "fail", "detail": f"Response indicates no data found: '{phrase}'"}

    response_numbers = extract_numbers(response)

    # Single value ground truth
    if isinstance(ground_truth_data, dict):
        gt_values = [v for v in ground_truth_data.values() if isinstance(v, (int, float))]
        if not gt_values:
            return {"match": "no_gt", "detail": "Ground truth has no numeric values"}

        matched = 0
        for gt_val in gt_values:
            for resp_val in response_numbers:
                if abs(resp_val - gt_val) < 0.5:  # Tolerance for rounding
                    matched += 1
                    break
        if matched == len(gt_values):
            return {"match": "full", "detail": f"All {matched} values matched"}
        elif matched > 0:
            return {"match": "partial", "detail": f"{matched}/{len(gt_values)} values matched"}
        else:
            return {"match": "fail", "detail": f"0/{len(gt_values)} values matched"}

    # List ground truth
    if isinstance(ground_truth_data, list):
        if not ground_truth_data:
            return {"match": "no_gt", "detail": "Ground truth list is empty"}

        total_values = 0
        total_matched = 0
        for item in ground_truth_data:
            if isinstance(item, dict):
                gt_values = [v for v in item.values() if isinstance(v, (int, float))]
                total_values += len(gt_values)
                for gt_val in gt_values:
                    for resp_val in response_numbers:
                        if abs(resp_val - gt_val) < 0.5:
                            total_matched += 1
                            break

        if total_values == 0:
            return {"match": "no_gt", "detail": "Ground truth has no numeric values"}
        if total_matched == total_values:
            return {"match": "full", "detail": f"All {total_matched}/{total_values} values matched"}
        elif total_matched > 0:
            return {"match": "partial", "detail": f"{total_matched}/{total_values} values matched"}
        else:
            return {"match": "fail", "detail": f"0/{total_values} values matched"}

    return {"match": "no_gt", "detail": "Unknown ground truth format"}


def generate_report(eval_data: dict, test_cases: list[dict]) -> str:
    """Generate a comprehensive matrix report."""
    lines = []
    w = lines.append

    results = eval_data["results"]

    # Build a lookup from question → test case for ground truth
    tc_lookup = {tc["question"]: tc for tc in test_cases}

    # ═══════════════════════════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════════════════════════
    w("# SQL Evaluation Matrix Report")
    w(f"\n**Date:** {eval_data['timestamp'][:10]}")
    w(f"**Total Test Cases:** {eval_data['total_cases']}")
    w(f"**Successful Executions:** {eval_data['successful']}/{eval_data['total_cases']}")
    w(f"**Failed Executions:** {eval_data['failed']}")
    w(f"**Classification Accuracy:** {eval_data['classification_accuracy']:.1f}%")
    w("")

    # ═══════════════════════════════════════════════════════════════
    # 1. CLASSIFICATION MATRIX
    # ═══════════════════════════════════════════════════════════════
    w("## 1. Classification Routing Matrix")
    w("")
    w("| Metric | Value |")
    w("|--------|-------|")
    rs = eval_data["routing_stats"]
    total = sum(rs.values())
    for route, count in rs.items():
        pct = (count / total * 100) if total > 0 else 0
        w(f"| {route} | {count} ({pct:.1f}%) |")
    w(f"| **Total** | **{total}** |")
    w("")

    if eval_data["misclassifications"]:
        w("### Misclassifications")
        w("")
        w("| # | Question | Expected | Actual | Response Preview |")
        w("|---|----------|----------|--------|------------------|")
        for i, m in enumerate(eval_data["misclassifications"], 1):
            preview = m["response_preview"][:80].replace("|", "\\|").replace("\n", " ")
            w(f"| {i} | {m['question'][:60]} | {m['expected']} | {m['actual']} | {preview} |")
        w("")
    else:
        w("**No misclassifications detected.**")
        w("")

    # ═══════════════════════════════════════════════════════════════
    # 2. CATEGORY PERFORMANCE MATRIX
    # ═══════════════════════════════════════════════════════════════
    w("## 2. Category Performance Matrix")
    w("")

    # Group results by category
    cat_groups = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in cat_groups:
            cat_groups[cat] = []
        cat_groups[cat].append(r)

    # Define category ordering (logical groups)
    category_order = [
        "simple_sql_top_n", "simple_sql_player_stats", "simple_sql_team_roster",
        "comparison_sql_players",
        "aggregation_sql_league", "aggregation_sql_count",
        "complex_sql_subquery", "complex_sql_multiple_conditions",
        "complex_sql_calculated_triple_condition", "complex_sql_calculated_field",
        "complex_sql_ratio_calculation", "complex_sql_percentage_calculation",
        "complex_sql_filtering", "complex_sql_filtering_calculation",
        "complex_sql_versatility",
        "conversational_initial", "conversational_casual",
        "conversational_followup", "conversational_comparison",
        "conversational_filter_followup",
    ]

    w("| Category | Count | Success | Routing OK | Avg Time (ms) |")
    w("|----------|------:|--------:|-----------:|--------------:|")

    for cat in category_order:
        if cat not in cat_groups:
            continue
        group = cat_groups[cat]
        count = len(group)
        success = sum(1 for r in group if r.get("success", False))
        routing_ok = sum(1 for r in group if not r.get("is_misclassified", True))
        times = [r.get("processing_time_ms", 0) for r in group if r.get("success")]
        avg_time = mean(times) if times else 0
        cat_short = cat.replace("_", " ").title()
        w(f"| {cat_short} | {count} | {success}/{count} | {routing_ok}/{count} | {avg_time:,.0f} |")

    w("")

    # ═══════════════════════════════════════════════════════════════
    # 3. GROUND TRUTH ACCURACY MATRIX
    # ═══════════════════════════════════════════════════════════════
    w("## 3. Ground Truth Accuracy Matrix")
    w("")
    w("Compares LLM response against ground truth data for each test case.")
    w("")

    gt_results = []  # (category, question, match_status, detail)
    match_counts = {"full": 0, "partial": 0, "fail": 0, "no_gt": 0}

    for r in results:
        q = r["question"]
        tc = tc_lookup.get(q)
        if tc and r.get("success"):
            gt_check = check_ground_truth_match(
                r["response"],
                tc["ground_truth_data"],
                tc["ground_truth_answer"]
            )
            gt_results.append((r["category"], q, gt_check["match"], gt_check["detail"]))
            match_counts[gt_check["match"]] += 1
        elif not r.get("success"):
            gt_results.append((r.get("category", "?"), q, "fail", "Execution failed"))
            match_counts["fail"] += 1

    w("### Summary")
    w("")
    evaluable = match_counts["full"] + match_counts["partial"] + match_counts["fail"]
    w(f"- **Full Match:** {match_counts['full']} ({match_counts['full']/evaluable*100:.1f}% of evaluable)" if evaluable > 0 else "- **Full Match:** 0")
    w(f"- **Partial Match:** {match_counts['partial']} ({match_counts['partial']/evaluable*100:.1f}% of evaluable)" if evaluable > 0 else "- **Partial Match:** 0")
    w(f"- **No Match / Fail:** {match_counts['fail']} ({match_counts['fail']/evaluable*100:.1f}% of evaluable)" if evaluable > 0 else "- **No Match / Fail:** 0")
    w(f"- **No Ground Truth Defined:** {match_counts['no_gt']}")
    w(f"- **Total Evaluable:** {evaluable}/{len(results)}")
    w("")

    # Group by category for ground truth
    w("### Detailed Ground Truth by Category")
    w("")

    # Group gt_results by parent category
    parent_categories = {
        "Simple SQL": ["simple_sql_top_n", "simple_sql_player_stats", "simple_sql_team_roster"],
        "Comparison SQL": ["comparison_sql_players"],
        "Aggregation SQL": ["aggregation_sql_league", "aggregation_sql_count"],
        "Complex SQL": [
            "complex_sql_subquery", "complex_sql_multiple_conditions",
            "complex_sql_calculated_triple_condition", "complex_sql_calculated_field",
            "complex_sql_ratio_calculation", "complex_sql_percentage_calculation",
            "complex_sql_filtering", "complex_sql_filtering_calculation",
            "complex_sql_versatility",
        ],
        "Conversational SQL": [
            "conversational_initial", "conversational_casual",
            "conversational_followup", "conversational_comparison",
            "conversational_filter_followup",
        ],
    }

    for parent, subcats in parent_categories.items():
        parent_results = [g for g in gt_results if g[0] in subcats]
        if not parent_results:
            continue
        full = sum(1 for _, _, m, _ in parent_results if m == "full")
        partial = sum(1 for _, _, m, _ in parent_results if m == "partial")
        fail = sum(1 for _, _, m, _ in parent_results if m == "fail")
        no_gt = sum(1 for _, _, m, _ in parent_results if m == "no_gt")
        total_cat = len(parent_results)
        evaluable_cat = full + partial + fail

        w(f"#### {parent} ({total_cat} cases)")
        w("")
        if evaluable_cat > 0:
            accuracy = (full / evaluable_cat) * 100
            w(f"**Accuracy (full match):** {accuracy:.0f}% ({full}/{evaluable_cat} evaluable)")
        w("")
        w("| # | Question | Match | Detail |")
        w("|---|----------|-------|--------|")
        for i, (cat, question, match, detail) in enumerate(parent_results, 1):
            icon = {"full": "FULL", "partial": "PARTIAL", "fail": "FAIL", "no_gt": "N/A"}[match]
            q_short = question[:65]
            detail_short = detail[:50]
            w(f"| {i} | {q_short} | {icon} | {detail_short} |")
        w("")

    # ═══════════════════════════════════════════════════════════════
    # 4. RESPONSE TIME ANALYSIS
    # ═══════════════════════════════════════════════════════════════
    w("## 4. Response Time Analysis")
    w("")

    all_times = [r["processing_time_ms"] for r in results if r.get("success") and "processing_time_ms" in r]

    if all_times:
        w(f"- **Mean:** {mean(all_times):,.0f} ms")
        w(f"- **Std Dev:** {stdev(all_times):,.0f} ms" if len(all_times) > 1 else "- **Std Dev:** N/A")
        w(f"- **Min:** {min(all_times):,.0f} ms")
        w(f"- **Max:** {max(all_times):,.0f} ms")
        w(f"- **Median:** {sorted(all_times)[len(all_times)//2]:,.0f} ms")
        w("")

        # Outliers (> 2x mean)
        avg = mean(all_times)
        outliers = [(r["question"], r["processing_time_ms"]) for r in results
                     if r.get("success") and r.get("processing_time_ms", 0) > avg * 2]
        if outliers:
            w("### Slow Queries (> 2x average)")
            w("")
            w("| Question | Time (ms) |")
            w("|----------|----------:|")
            for q, t in sorted(outliers, key=lambda x: -x[1]):
                w(f"| {q[:65]} | {t:,.0f} |")
            w("")

    # ═══════════════════════════════════════════════════════════════
    # 5. FULL RESPONSE MATRIX
    # ═══════════════════════════════════════════════════════════════
    w("## 5. Full Response Matrix")
    w("")
    w("| # | Category | Question | Routing | GT Match | Time (ms) | Response (truncated) |")
    w("|--:|----------|----------|---------|----------|----------:|----------------------|")

    for i, r in enumerate(results, 1):
        cat = r.get("category", "?")
        q = r["question"][:45]
        routing = r.get("actual_routing", "?")
        time_ms = r.get("processing_time_ms", 0)

        # Find ground truth match
        gt_match = "?"
        for _, gq, gm, _ in gt_results:
            if gq == r["question"]:
                gt_match = {"full": "FULL", "partial": "PART", "fail": "FAIL", "no_gt": "N/A"}[gm]
                break

        resp = r.get("response", r.get("error", "N/A"))
        resp_short = resp[:60].replace("|", "\\|").replace("\n", " ").strip()

        misclass = " *" if r.get("is_misclassified") else ""
        w(f"| {i} | {cat[:25]} | {q} | {routing}{misclass} | {gt_match} | {time_ms:,.0f} | {resp_short} |")

    w("")
    w("*\\* = misclassified*")
    w("")

    # ═══════════════════════════════════════════════════════════════
    # 6. OVERALL SCORES
    # ═══════════════════════════════════════════════════════════════
    w("## 6. Overall Evaluation Scores")
    w("")
    w("| Metric | Score |")
    w("|--------|------:|")
    w(f"| Execution Success Rate | {eval_data['successful']}/{eval_data['total_cases']} ({eval_data['successful']/eval_data['total_cases']*100:.1f}%) |")
    w(f"| Classification Accuracy | {eval_data['classification_accuracy']:.1f}% |")
    if evaluable > 0:
        gt_accuracy = (match_counts["full"] + match_counts["partial"]) / evaluable * 100
        gt_full_accuracy = match_counts["full"] / evaluable * 100
        w(f"| Ground Truth Full Match | {gt_full_accuracy:.1f}% ({match_counts['full']}/{evaluable}) |")
        w(f"| Ground Truth Full+Partial | {gt_accuracy:.1f}% ({match_counts['full']+match_counts['partial']}/{evaluable}) |")
    if all_times:
        w(f"| Mean Response Time | {mean(all_times):,.0f} ms |")
    w("")

    return "\n".join(lines)


def main():
    eval_data = load_latest_evaluation()
    test_cases = load_test_cases()
    report = generate_report(eval_data, test_cases)

    output_path = Path("evaluation_results/SQL_EVALUATION_MATRIX_REPORT.md")
    output_path.write_text(report, encoding="utf-8")
    print(f"\nMatrix report saved to: {output_path}")
    print(f"Report length: {len(report):,} characters")


if __name__ == "__main__":
    main()
