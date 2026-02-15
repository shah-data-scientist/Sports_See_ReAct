"""
FILE: sample_eval_direct.py
STATUS: Active
RESPONSIBILITY: Direct sample evaluation - test service layer directly (bypasses API layer)
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import json
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.observability import logger
from src.evaluation.analyzer import analyze_results
from src.evaluation.test_data import ALL_TEST_CASES
from src.evaluation.models import TestType
from src.models.chat import ChatRequest
from src.services.chat import ChatService

TEST_OUTPUT_DIR = Path("evaluation_results/test_run_2026_02_12")


def run_sql_sample():
    """Run 2 SQL test cases and generate report with metrics."""
    logger.info("=" * 80)
    logger.info("SAMPLE SQL EVALUATION (2 test cases)")
    logger.info("=" * 80)

    service = ChatService()
    service.ensure_ready()

    test_cases = SQL_TEST_CASES[:2]
    results = []

    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n[{i}/2] Testing: {test_case.question}")
        try:
            start_time = time.time()
            request = ChatRequest(query=test_case.question)
            response = service.chat(request)
            elapsed_ms = (time.time() - start_time) * 1000

            results.append({
                "query": test_case.question,
                "success": True,
                "response": response.answer if hasattr(response, 'answer') else response.get("answer", ""),
                "sources": response.sources if hasattr(response, 'sources') else response.get("sources", []),
                "processing_time_ms": elapsed_ms,
                "category": test_case.category,
            })
            logger.info(f"✓ Success ({elapsed_ms:.0f}ms)")

        except Exception as e:
            logger.error(f"✗ Error: {e}")
            results.append({
                "query": test_case.question,
                "success": False,
                "response": str(e),
                "sources": [],
                "processing_time_ms": 0,
                "category": test_case.category,
            })

    # Analyze
    successful = [r for r in results if r["success"]]
    analysis = {
        "execution_summary": {
            "total_queries": len(results),
            "successful": len(successful),
            "failed": len(results) - len(successful),
            "success_rate": f"{len(successful)/len(results)*100:.1f}%" if results else "0%",
        },
        "latency": {
            "avg_ms": statistics.mean([r["processing_time_ms"] for r in successful]) if successful else 0,
        },
        "quality_analysis": {
            "error_taxonomy": analyze_error_taxonomy(results),
            "response_quality": analyze_response_quality(results),
            "query_structure": analyze_query_structure(results),
            "query_complexity": analyze_query_complexity(results),
            "column_selection": analyze_column_selection(results),
            "fallback_patterns": analyze_fallback_patterns(results),
        },
    }

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results_file = TEST_OUTPUT_DIR / f"sql_sample_results_{timestamp}.json"
    analysis_file = TEST_OUTPUT_DIR / f"sql_sample_analysis_{timestamp}.json"
    report_file = TEST_OUTPUT_DIR / f"sql_sample_report_{timestamp}.md"

    results_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    analysis_file.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    report = f"""# SQL Sample Evaluation Report
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Test Cases:** 2 samples

## Execution Summary
- **Total Queries:** {analysis['execution_summary']['total_queries']}
- **Successful:** {analysis['execution_summary']['successful']}
- **Failed:** {analysis['execution_summary']['failed']}
- **Success Rate:** {analysis['execution_summary']['success_rate']}

## Latency Metrics
- **Average:** {analysis['latency']['avg_ms']:.0f}ms

## Quality Analysis Metrics

### Error Taxonomy
```json
{json.dumps(analysis['quality_analysis']['error_taxonomy'], indent=2)}
```

### Response Quality
```json
{json.dumps(analysis['quality_analysis']['response_quality'], indent=2)}
```

### Query Structure Analysis
```json
{json.dumps(analysis['quality_analysis']['query_structure'], indent=2)}
```

### Query Complexity
```json
{json.dumps(analysis['quality_analysis']['query_complexity'], indent=2)}
```

### Column Selection
```json
{json.dumps(analysis['quality_analysis']['column_selection'], indent=2)}
```

### Fallback Patterns
```json
{json.dumps(analysis['quality_analysis']['fallback_patterns'], indent=2)}
```

## Sample Query Results
{json.dumps(results, indent=2)}
"""

    report_file.write_text(report, encoding="utf-8")

    logger.info(f"\n✓ SQL sample evaluation complete!")
    logger.info(f"  Results: {results_file.name}")
    logger.info(f"  Analysis: {analysis_file.name}")
    logger.info(f"  Report: {report_file.name}")

    return report_file


def run_vector_sample():
    """Run 2 Vector test cases and generate report with metrics."""
    logger.info("\n" + "=" * 80)
    logger.info("SAMPLE VECTOR EVALUATION (2 test cases)")
    logger.info("=" * 80)

    service = ChatService()
    service.ensure_ready()

    test_cases = EVALUATION_TEST_CASES[:2]
    results = []

    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n[{i}/2] Testing: {test_case.question}")
        try:
            start_time = time.time()
            request = ChatRequest(query=test_case.question)
            response = service.chat(request)
            elapsed_ms = (time.time() - start_time) * 1000

            results.append({
                "query": test_case.question,
                "success": True,
                "response": response.get("answer", ""),
                "sources": response.get("sources", []),
                "processing_time_ms": elapsed_ms,
                "category": str(test_case.category),
            })
            logger.info(f"✓ Success ({elapsed_ms:.0f}ms, {len(response.get('sources', []))} sources)")

        except Exception as e:
            logger.error(f"✗ Error: {e}")
            results.append({
                "query": test_case.question,
                "success": False,
                "response": str(e),
                "sources": [],
                "processing_time_ms": 0,
                "category": str(test_case.category),
            })

    # Analyze
    successful = [r for r in results if r["success"]]
    analysis = {
        "execution_summary": {
            "total_queries": len(results),
            "successful": len(successful),
            "failed": len(results) - len(successful),
            "success_rate": f"{len(successful)/len(results)*100:.1f}%" if results else "0%",
        },
        "latency": {
            "avg_ms": statistics.mean([r["processing_time_ms"] for r in successful]) if successful else 0,
        },
        "quality_analysis": {
            "source_quality": analyze_source_quality(results),
            "retrieval_performance": analyze_retrieval_performance(results),
            "response_patterns": analyze_response_patterns(results),
        },
    }

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results_file = TEST_OUTPUT_DIR / f"vector_sample_results_{timestamp}.json"
    analysis_file = TEST_OUTPUT_DIR / f"vector_sample_analysis_{timestamp}.json"
    report_file = TEST_OUTPUT_DIR / f"vector_sample_report_{timestamp}.md"

    results_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    analysis_file.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    report = f"""# Vector Sample Evaluation Report
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Test Cases:** 2 samples

## Execution Summary
- **Total Queries:** {analysis['execution_summary']['total_queries']}
- **Successful:** {analysis['execution_summary']['successful']}
- **Failed:** {analysis['execution_summary']['failed']}
- **Success Rate:** {analysis['execution_summary']['success_rate']}

## Latency Metrics
- **Average:** {analysis['latency']['avg_ms']:.0f}ms

## Quality Analysis Metrics

### Source Quality
```json
{json.dumps(analysis['quality_analysis']['source_quality'], indent=2)}
```

### Retrieval Performance
```json
{json.dumps(analysis['quality_analysis']['retrieval_performance'], indent=2)}
```

### Response Patterns
```json
{json.dumps(analysis['quality_analysis']['response_patterns'], indent=2)}
```

## Sample Query Results
{json.dumps(results, indent=2)}
"""

    report_file.write_text(report, encoding="utf-8")

    logger.info(f"\n✓ Vector sample evaluation complete!")
    logger.info(f"  Results: {results_file.name}")
    logger.info(f"  Analysis: {analysis_file.name}")
    logger.info(f"  Report: {report_file.name}")

    return report_file


if __name__ == "__main__":
    logger.info("Starting direct sample evaluations...")
    logger.info(f"Output directory: {TEST_OUTPUT_DIR.absolute()}\n")

    sql_report = run_sql_sample()
    vector_report = run_vector_sample()

    logger.info("\n" + "=" * 80)
    logger.info("SAMPLE EVALUATIONS COMPLETE")
    logger.info("=" * 80)
    logger.info(f"\nAll files saved to: {TEST_OUTPUT_DIR.absolute()}")
    logger.info("\nMarkdown reports generated:")
    logger.info(f"  SQL: {sql_report.name}")
    logger.info(f"  Vector: {vector_report.name}")
    logger.info("\n✓ Verify metrics by opening the markdown reports!")
