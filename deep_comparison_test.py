#!/usr/bin/env python3
"""
Deep comparison of API responses vs evaluation results.
"""

import json
import requests
import time
from typing import Dict, Any, List

API_BASE = "http://localhost:8002/api/v1"

def call_api_detailed(query: str) -> Dict[str, Any]:
    """Make API call and return detailed response."""
    try:
        start = time.time()
        response = requests.post(
            f"{API_BASE}/chat",
            json={"query": query},
            timeout=30
        )
        elapsed_ms = (time.time() - start) * 1000

        if response.status_code != 200:
            return {
                "error": f"HTTP {response.status_code}",
                "error_detail": response.text[:500],
                "elapsed_ms": elapsed_ms
            }

        data = response.json()
        data["elapsed_ms"] = elapsed_ms
        return data

    except Exception as e:
        return {
            "error": type(e).__name__,
            "error_detail": str(e)
        }

def analyze_differences(eval_data: Dict, api_data: Dict) -> Dict[str, Any]:
    """Detailed analysis of differences."""
    analysis = {
        "routing": {
            "eval": eval_data.get("routing", "unknown"),
            "api": api_data.get("query_type", "unknown"),
            "match": eval_data.get("routing") == api_data.get("query_type")
        },
        "sql": {
            "eval_generated": bool(eval_data.get("generated_sql")),
            "api_generated": bool(api_data.get("generated_sql")),
            "eval_sql": eval_data.get("generated_sql", ""),
            "api_sql": api_data.get("generated_sql", ""),
            "match": eval_data.get("generated_sql") == api_data.get("generated_sql")
        },
        "sources": {
            "eval_count": eval_data.get("sources_count", 0),
            "api_count": len(api_data.get("sources", [])),
            "match": eval_data.get("sources_count") == len(api_data.get("sources", []))
        },
        "visualization": {
            "eval_has_viz": eval_data.get("visualization") is not None,
            "api_has_viz": api_data.get("visualization") is not None,
            "match": (eval_data.get("visualization") is not None) == (api_data.get("visualization") is not None)
        },
        "answer": {
            "eval_length": len(eval_data.get("response", "")),
            "api_length": len(api_data.get("answer", "")),
            "eval_preview": eval_data.get("response", "")[:200],
            "api_preview": api_data.get("answer", "")[:200]
        },
        "performance": {
            "eval_ms": eval_data.get("processing_time_ms", 0),
            "api_ms": api_data.get("elapsed_ms", 0),
            "diff_ms": api_data.get("elapsed_ms", 0) - eval_data.get("processing_time_ms", 0)
        }
    }

    # Count mismatches
    mismatches = sum([
        not analysis["routing"]["match"],
        not analysis["sql"]["match"],
        not analysis["sources"]["match"],
        not analysis["visualization"]["match"]
    ])

    analysis["total_mismatches"] = mismatches
    analysis["has_issues"] = mismatches > 0 or "error" in api_data

    return analysis

def main():
    print("="*80)
    print("DEEP COMPARISON: API vs Evaluation Results")
    print("="*80)

    # Test one query from each type
    test_cases = [
        {
            "type": "sql",
            "query": "Who scored the most points this season?",
            "eval_file": "evaluation_results/evaluation_sql_20260216_234022.json"
        },
        {
            "type": "vector",
            "query": "What do Reddit users think about teams that have impressed in the playoffs?",
            "eval_file": "evaluation_results/evaluation_vector_20260216_234636.json"
        },
        {
            "type": "hybrid",
            "query": "Who scored the most points this season and what makes them an effective scorer?",
            "eval_file": "evaluation_results/evaluation_hybrid_20260216_235058.json"
        }
    ]

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {test['type'].upper()} Query")
        print('='*80)
        print(f"Query: {test['query']}")

        # Load evaluation result
        with open(test['eval_file'], 'r', encoding='utf-8') as f:
            eval_data = json.load(f)

        eval_result = None
        for result in eval_data["results"]:
            if result["question"] == test["query"]:
                eval_result = result
                break

        if not eval_result:
            print("  ✗ Query not found in evaluation data")
            continue

        # Call API
        print("\n  Calling API...")
        api_result = call_api_detailed(test["query"])

        if "error" in api_result:
            print(f"  ✗ API Error: {api_result['error']}")
            print(f"    Detail: {api_result.get('error_detail', 'N/A')[:200]}")
            results.append({
                "query": test["query"],
                "type": test["type"],
                "status": "error",
                "error": api_result
            })
            continue

        # Analyze differences
        analysis = analyze_differences(eval_result, api_result)

        print("\n  ROUTING:")
        print(f"    Eval: {analysis['routing']['eval']}")
        print(f"    API:  {analysis['routing']['api']}")
        print(f"    Match: {'✓' if analysis['routing']['match'] else '✗'}")

        print("\n  SQL GENERATION:")
        print(f"    Eval generated: {analysis['sql']['eval_generated']}")
        print(f"    API generated:  {analysis['sql']['api_generated']}")
        if analysis['sql']['eval_generated'] or analysis['sql']['api_generated']:
            print(f"    Match: {'✓' if analysis['sql']['match'] else '✗'}")
            if not analysis['sql']['match']:
                print(f"    Eval SQL: {analysis['sql']['eval_sql'][:80]}...")
                print(f"    API SQL:  {analysis['sql']['api_sql'][:80]}...")

        print("\n  SOURCES:")
        print(f"    Eval count: {analysis['sources']['eval_count']}")
        print(f"    API count:  {analysis['sources']['api_count']}")
        print(f"    Match: {'✓' if analysis['sources']['match'] else '✗'}")

        print("\n  VISUALIZATION:")
        print(f"    Eval has viz: {analysis['visualization']['eval_has_viz']}")
        print(f"    API has viz:  {analysis['visualization']['api_has_viz']}")
        print(f"    Match: {'✓' if analysis['visualization']['match'] else '✗'}")

        print("\n  ANSWER:")
        print(f"    Eval length: {analysis['answer']['eval_length']} chars")
        print(f"    API length:  {analysis['answer']['api_length']} chars")
        print(f"    Eval preview: {analysis['answer']['eval_preview']}")
        print(f"    API preview:  {analysis['answer']['api_preview']}")

        print("\n  PERFORMANCE:")
        print(f"    Eval: {analysis['performance']['eval_ms']:.0f}ms")
        print(f"    API:  {analysis['performance']['api_ms']:.0f}ms")
        print(f"    Diff: {analysis['performance']['diff_ms']:+.0f}ms")

        print(f"\n  SUMMARY: {analysis['total_mismatches']} mismatches")

        results.append({
            "query": test["query"],
            "type": test["type"],
            "status": "success",
            "analysis": analysis
        })

        time.sleep(3)  # Rate limiting

    # Overall summary
    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print('='*80)

    errors = sum(1 for r in results if r["status"] == "error")
    successes = sum(1 for r in results if r["status"] == "success")
    issues = sum(1 for r in results if r.get("analysis", {}).get("has_issues", False))

    print(f"Total tests: {len(results)}")
    print(f"Errors: {errors}")
    print(f"Successes: {successes}")
    print(f"With issues: {issues}")

    if successes > 0:
        print("\nKey findings:")

        # Routing analysis
        routing_changed = sum(
            1 for r in results
            if r["status"] == "success" and not r["analysis"]["routing"]["match"]
        )
        if routing_changed > 0:
            print(f"  • Routing changed in {routing_changed}/{successes} queries")
            print(f"    (Eval: 'unknown' → API: 'agent')")

    # Save results
    output = "deep_comparison_results.json"
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed results saved to: {output}")

if __name__ == "__main__":
    main()
