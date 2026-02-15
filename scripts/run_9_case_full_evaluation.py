"""
FILE: run_9_case_full_evaluation.py
STATUS: Active
RESPONSIBILITY: Run 9 test cases through full evaluation pipeline with RAGAS metrics
CREATED: 2026-02-15
MAINTAINER: Shahu

This script:
1. Runs the 9 test cases through the optimized ReAct agent
2. Calculates RAGAS metrics (Faithfulness, Answer Correctness, etc.)
3. Uses the analyzer to generate comprehensive markdown report
4. Compares to baseline metrics from evaluation_all_report_20260215_061543.md
"""

import json
import time
from datetime import datetime
from pathlib import Path

from src.services.chat import ChatService
from src.models.chat import ChatRequest
from src.evaluation.analyzer import analyze_results
from src.evaluation.metrics import calculate_ragas_metrics

# Test cases (same 9 from validation)
TEST_CASES = [
    # SQL-only queries
    {
        "question": "Who scored the most points this season?",
        "test_type": "SQL",
        "category": "simple_sql_top_n",
        "expected_routing": "sql_only",
        "ground_truth_answer": "Shai Gilgeous-Alexander scored the most points with 2485 points."
    },
    {
        "question": "Who are the top 3 rebounders in the league?",
        "test_type": "SQL",
        "category": "simple_sql_top_n",
        "expected_routing": "sql_only",
        "ground_truth_answer": "The top 3 rebounders are Ivica Zubac (1008), Domantas Sabonis (973), and Karl-Anthony Towns (922)."
    },
    {
        "question": "Who are the top 5 players in steals?",
        "test_type": "SQL",
        "category": "simple_sql_top_n",
        "expected_routing": "sql_only",
        "ground_truth_answer": "The top 5 players in steals are Dyson Daniels (228), Shai Gilgeous-Alexander (129), Nikola Jokić (126), Kris Dunn (126), and Cason Wallace (122)."
    },

    # Vector-only queries
    {
        "question": "What do Reddit users think about teams that have impressed?",
        "test_type": "VECTOR",
        "category": "simple",
        "expected_routing": "vector_only",
        "ground_truth_answer": "Reddit users have discussed teams like the Orlando Magic positively, noting their impressive performance."
    },
    {
        "question": "What are the most popular opinions about the top teams?",
        "test_type": "VECTOR",
        "category": "simple",
        "expected_routing": "vector_only",
        "ground_truth_answer": "Popular opinions focus on the Oklahoma City Thunder and Cleveland Cavaliers as top teams based on their records."
    },
    {
        "question": "What do fans debate about Reggie Miller's efficiency?",
        "test_type": "VECTOR",
        "category": "simple",
        "expected_routing": "vector_only",
        "ground_truth_answer": "Fans debate Reggie Miller's efficiency, with some discussing his high true shooting percentage despite varied opinions on efficiency as a metric."
    },

    # Hybrid queries
    {
        "question": "Who scored the most points this season and what makes them an effective scorer?",
        "test_type": "HYBRID",
        "category": "tier1_stat_plus_context",
        "expected_routing": "hybrid",
        "ground_truth_answer": "Shai Gilgeous-Alexander scored 2485 points. He is effective due to his high true shooting percentage (63.7%) and efficient scoring."
    },
    {
        "question": "Compare LeBron James and Kevin Durant's scoring this season and explain their scoring styles.",
        "test_type": "HYBRID",
        "category": "tier1_comparison_plus_context",
        "expected_routing": "hybrid",
        "ground_truth_answer": "LeBron scored 1708 points (51.3 FG%, 37.6 3P%) while Durant scored 1649 points (52.7 FG%, 43.0 3P%). Durant is more efficient from three-point range."
    },
    {
        "question": "What is Nikola Jokić's scoring average and why is he considered an elite offensive player?",
        "test_type": "HYBRID",
        "category": "tier1_stat_plus_explanation",
        "expected_routing": "hybrid",
        "ground_truth_answer": "Nikola Jokić averages 29.6 points per game. He is considered elite due to his scoring efficiency and playmaking ability."
    }
]

def main():
    """Run full evaluation with RAGAS metrics."""

    print("\n" + "=" * 100)
    print("FULL EVALUATION - 9 Test Cases with RAGAS Metrics")
    print("=" * 100)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test cases: {len(TEST_CASES)}")
    print("=" * 100)

    # Initialize services
    print("\nInitializing services...")
    chat_service = ChatService()

    # Run queries and collect results
    results = []

    for i, test_case in enumerate(TEST_CASES, 1):
        question = test_case["question"]
        print(f"\n[{i}/{len(TEST_CASES)}] Testing: '{question[:60]}...'")

        start_time = time.time()

        try:
            # Execute query
            request = ChatRequest(
                query=question,
                conversation_id=f"eval-{i}",
                turn_number=1
            )

            response = chat_service.chat(request)
            processing_time = (time.time() - start_time) * 1000

            # Extract information
            tools_used = response.tools_used if hasattr(response, 'tools_used') else []
            query_type = response.query_type if hasattr(response, 'query_type') else "unknown"
            sources = response.sources if hasattr(response, 'sources') else []

            # Determine actual routing
            sql_executed = "query_nba_database" in tools_used
            vector_executed = "search_knowledge_base" in tools_used

            if sql_executed and vector_executed:
                actual_routing = "hybrid"
            elif sql_executed:
                actual_routing = "sql_only"
            elif vector_executed:
                actual_routing = "vector_only"
            else:
                actual_routing = "unknown"

            # Check for misclassification
            is_misclassified = actual_routing != test_case["expected_routing"]

            # Build result entry
            result = {
                "test_number": i,
                "question": question,
                "answer": response.answer,
                "test_type": test_case["test_type"],
                "category": test_case["category"],
                "expected_routing": test_case["expected_routing"],
                "actual_routing": actual_routing,
                "query_type": query_type,
                "is_misclassified": is_misclassified,
                "tools_used": tools_used,
                "sources": [
                    {
                        "text": s.text if hasattr(s, 'text') else (s.content if hasattr(s, 'content') else str(s)),
                        "metadata": s.metadata if hasattr(s, 'metadata') else {}
                    }
                    for s in sources
                ],
                "sources_count": len(sources),
                "processing_time_ms": round(processing_time, 2),
                "success": True,
                "ground_truth_answer": test_case["ground_truth_answer"]
            }

            # Add SQL info if available
            if hasattr(response, 'generated_sql') and response.generated_sql:
                result["generated_sql"] = response.generated_sql

            results.append(result)

            print(f"  ✓ Success (routing: {actual_routing}, time: {processing_time:.0f}ms)")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                "test_number": i,
                "question": question,
                "test_type": test_case["test_type"],
                "category": test_case["category"],
                "error": str(e),
                "success": False,
                "processing_time_ms": (time.time() - start_time) * 1000
            })

    # Calculate RAGAS metrics
    print("\n" + "=" * 100)
    print("Calculating RAGAS Metrics...")
    print("=" * 100)

    for result in results:
        if result.get("success"):
            print(f"\nEvaluating: '{result['question'][:50]}...'")

            try:
                # Evaluate with RAGAS
                eval_result = calculate_ragas_metrics(
                    question=result["question"],
                    answer=result["answer"],
                    sources=result["sources"],  # Pass the full sources list
                    ground_truth_answer=result["ground_truth_answer"]
                )

                # Add metrics to result
                result["ragas_metrics"] = eval_result

                print(f"  Faithfulness: {eval_result.get('faithfulness', 0):.3f}")
                print(f"  Answer Correctness: {eval_result.get('answer_correctness', 0):.3f}")
                cp = eval_result.get('context_precision')
                if cp is not None:
                    print(f"  Context Precision: {cp:.3f}")
                else:
                    print(f"  Context Precision: N/A (no sources)")

            except Exception as e:
                print(f"  ⚠️  RAGAS evaluation failed: {e}")
                result["ragas_metrics"] = {}

    # Use analyzer to generate report
    print("\n" + "=" * 100)
    print("Generating Analysis Report...")
    print("=" * 100)

    analysis = analyze_results(results, test_cases=TEST_CASES)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("evaluation_results")
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / f"evaluation_optimized_9cases_{timestamp}.json"
    report_path = output_dir / f"evaluation_optimized_9cases_{timestamp}.md"

    # Save JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "total_queries": len(results),
            "results": results,
            "analysis": analysis
        }, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Results saved to: {json_path}")

    # Generate markdown report
    generate_comprehensive_report(results, analysis, json_path, report_path)

    print(f"✓ Report saved to: {report_path}")
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)


def generate_comprehensive_report(results, analysis, json_path, report_path):
    """Generate comprehensive markdown report."""

    # Calculate summary stats
    total = len(results)
    successful = sum(1 for r in results if r.get("success"))
    failed = total - successful

    # RAGAS metrics
    ragas_scores = {
        "faithfulness": [],
        "answer_correctness": [],
        "answer_relevancy": [],
        "context_precision": [],
        "context_relevancy": []
    }

    for r in results:
        if r.get("ragas_metrics"):
            for metric, values in ragas_scores.items():
                if metric in r["ragas_metrics"] and r["ragas_metrics"][metric] is not None:
                    values.append(r["ragas_metrics"][metric])

    avg_ragas = {
        metric: sum(scores) / len(scores) if scores else 0
        for metric, scores in ragas_scores.items()
    }

    # Generate report
    report = f"""# Optimized Evaluation Report - 9 Test Cases

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Dataset:** {total} test cases (post-optimization)

**Results JSON:** `{json_path.name}`

---

## Executive Summary

- **Total Queries:** {total}
- **Successful Executions:** {successful} ({successful/total*100:.1f}%)
- **Failed Executions:** {failed}
- **Misclassifications:** {sum(1 for r in results if r.get('is_misclassified', False))}

### RAGAS Metrics (Post-Optimization)

| Metric | Score | Status |
|--------|-------|--------|
| Faithfulness | {avg_ragas['faithfulness']:.3f} | {'✅' if avg_ragas['faithfulness'] >= 0.9 else '⚠️'} |
| Answer Correctness | {avg_ragas['answer_correctness']:.3f} | {'✅' if avg_ragas['answer_correctness'] >= 0.9 else '⚠️'} |
| Answer Relevancy | {avg_ragas['answer_relevancy']:.3f} | {'✅' if avg_ragas['answer_relevancy'] >= 0.9 else '⚠️'} |
| Context Precision | {avg_ragas['context_precision']:.3f} | {'✅' if avg_ragas['context_precision'] >= 0.8 else '⚠️'} |
| Context Relevancy | {avg_ragas['context_relevancy']:.3f} | {'✅' if avg_ragas['context_relevancy'] >= 0.8 else '⚠️'} |

### Comparison to Baseline

**Baseline (Before Optimization):**
- Context Precision: 0.333 ❌
- Context Relevancy: 0.333 ❌
- Wasteful vector searches: 3/9 (33%)

**Post-Optimization:**
- Context Precision: {avg_ragas['context_precision']:.3f} {'✅' if avg_ragas['context_precision'] > 0.333 else '❌'}
- Context Relevancy: {avg_ragas['context_relevancy']:.3f} {'✅' if avg_ragas['context_relevancy'] > 0.333 else '❌'}
- Wasteful vector searches: {sum(1 for r in results if r.get('test_type') == 'SQL' and 'search_knowledge_base' in r.get('tools_used', []))}/3 ({sum(1 for r in results if r.get('test_type') == 'SQL' and 'search_knowledge_base' in r.get('tools_used', []))/3*100:.0f}%)

**Improvement:**
- Context Precision: {(avg_ragas['context_precision'] - 0.333) / 0.333 * 100:+.0f}%
- Context Relevancy: {(avg_ragas['context_relevancy'] - 0.333) / 0.333 * 100:+.0f}%

---

## Smart Tool Selection Analysis

### Routing Accuracy

| Expected | Actual | Count | Percentage |
|----------|--------|-------|------------|
"""

    # Routing breakdown
    routing_counts = {}
    for r in results:
        expected = r.get("expected_routing", "unknown")
        actual = r.get("actual_routing", "unknown")
        key = (expected, actual)
        routing_counts[key] = routing_counts.get(key, 0) + 1

    for (expected, actual), count in sorted(routing_counts.items()):
        match_status = "✅" if expected == actual else "❌"
        report += f"| {expected} | {actual} | {count} | {count/total*100:.0f}% {match_status} |\n"

    report += "\n### Tool Execution Efficiency\n\n"
    report += "| Query Type | SQL Executed | Vector Executed | Wasteful? |\n"
    report += "|------------|--------------|-----------------|----------|\n"

    for r in results:
        if r.get("success"):
            test_type = r.get("test_type")
            sql_exec = "query_nba_database" in r.get("tools_used", [])
            vec_exec = "search_knowledge_base" in r.get("tools_used", [])

            # Check if wasteful (SQL-only query with vector execution)
            wasteful = test_type == "SQL" and vec_exec

            report += f"| {test_type} | {'✓' if sql_exec else '✗'} | {'✓' if vec_exec else '✗'} | {'⚠️ YES' if wasteful else '✅ NO'} |\n"

    report += f"\n---\n\n**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    # Write report
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)


if __name__ == "__main__":
    main()
