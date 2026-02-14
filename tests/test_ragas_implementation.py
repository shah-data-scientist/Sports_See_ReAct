"""
Test script for RAGAS implementation.

Tests:
1. RAGAS calculator with sample data
2. All 7 metrics are calculated
3. SQL-only query (context metrics are None)
4. Vector query (all metrics calculated)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.ragas_calculator import calculate_ragas_metrics, format_ragas_report


def test_sql_only_query():
    """Test RAGAS calculation for SQL-only query (no vector search)."""
    print("\n" + "=" * 80)
    print("TEST 1: SQL-ONLY QUERY (Context metrics should be None)")
    print("=" * 80)

    question = "Who scored the most points this season?"
    answer = "Shai Gilgeous-Alexander scored the most points with 2,485 points."
    sources = []  # SQL-only, no vector sources
    ground_truth_answer = "Shai Gilgeous-Alexander scored 2485 points."
    ground_truth_vector = None  # SQL-only

    metrics = calculate_ragas_metrics(
        question=question,
        answer=answer,
        sources=sources,
        ground_truth_answer=ground_truth_answer,
        ground_truth_vector=ground_truth_vector
    )

    print("\nMetrics Calculated:")
    print(f"  Faithfulness: {metrics.get('faithfulness', 'N/A')}")
    print(f"  Answer Relevancy: {metrics.get('answer_relevancy', 'N/A')}")
    print(f"  Answer Semantic Similarity: {metrics.get('answer_semantic_similarity', 'N/A')}")
    print(f"  Answer Correctness: {metrics.get('answer_correctness', 'N/A')} ⭐")
    print(f"  Context Precision: {metrics.get('context_precision', 'N/A')} (should be None)")
    print(f"  Context Recall: {metrics.get('context_recall', 'N/A')} (should be None)")
    print(f"  Context Relevancy: {metrics.get('context_relevancy', 'N/A')} (should be None)")

    # Verify context metrics are None for SQL-only
    assert metrics["context_precision"] is None, "Context Precision should be None for SQL-only"
    assert metrics["context_recall"] is None, "Context Recall should be None for SQL-only"
    assert metrics["context_relevancy"] is None, "Context Relevancy should be None for SQL-only"

    print("\n✅ TEST 1 PASSED: Context metrics correctly set to None for SQL-only query")


def test_vector_query():
    """Test RAGAS calculation for Vector query (all 7 metrics)."""
    print("\n" + "=" * 80)
    print("TEST 2: VECTOR QUERY (All 7 metrics should be calculated)")
    print("=" * 80)

    question = "What do fans think about efficiency in basketball?"
    answer = "Fans believe that Reggie Miller is one of the most efficient scorers, with a 115% true shooting percentage."
    sources = [
        {
            "text": "Reddit user: Reggie Miller is the most efficient scorer with 115 TS%.",
            "score": 0.85,
            "source": "Reddit 3.pdf"
        },
        {
            "text": "Efficiency is measured by true shooting percentage.",
            "score": 0.78,
            "source": "Reddit 3.pdf"
        },
        {
            "text": "LeBron James is the GOAT.",
            "score": 0.45,
            "source": "Reddit 1.pdf"
        }
    ]
    ground_truth_answer = "Fans consider Reggie Miller to be highly efficient with a 115% TS%."
    ground_truth_vector = "Should retrieve Reddit 3.pdf discussing efficiency, mentioning Reggie Miller with 115 TS%"

    metrics = calculate_ragas_metrics(
        question=question,
        answer=answer,
        sources=sources,
        ground_truth_answer=ground_truth_answer,
        ground_truth_vector=ground_truth_vector
    )

    print("\nMetrics Calculated:")
    print(f"  Faithfulness: {metrics.get('faithfulness', 'N/A')}")
    print(f"  Answer Relevancy: {metrics.get('answer_relevancy', 'N/A')}")
    print(f"  Answer Semantic Similarity: {metrics.get('answer_semantic_similarity', 'N/A')}")
    print(f"  Answer Correctness: {metrics.get('answer_correctness', 'N/A')} ⭐")
    print(f"  Context Precision: {metrics.get('context_precision', 'N/A')}")
    print(f"  Context Recall: {metrics.get('context_recall', 'N/A')}")
    print(f"  Context Relevancy: {metrics.get('context_relevancy', 'N/A')}")

    # Verify all metrics are present
    assert metrics["faithfulness"] is not None, "Faithfulness should be calculated"
    assert metrics["answer_relevancy"] is not None, "Answer Relevancy should be calculated"
    assert metrics["answer_semantic_similarity"] is not None, "Answer Semantic Similarity should be calculated"
    assert metrics["answer_correctness"] is not None, "Answer Correctness should be calculated"
    assert metrics["context_precision"] is not None, "Context Precision should be calculated"
    assert metrics["context_recall"] is not None, "Context Recall should be calculated"
    assert metrics["context_relevancy"] is not None, "Context Relevancy should be calculated"

    print("\n✅ TEST 2 PASSED: All 7 metrics calculated for Vector query")


def test_format_report():
    """Test formatting of RAGAS report with nuclear explanations."""
    print("\n" + "=" * 80)
    print("TEST 3: FORMAT RAGAS REPORT (Nuclear Explanations)")
    print("=" * 80)

    metrics = {
        "faithfulness": 0.92,
        "answer_relevancy": 0.88,
        "answer_semantic_similarity": 0.95,
        "answer_correctness": 0.91,
        "context_precision": 0.75,
        "context_recall": 0.80,
        "context_relevancy": 0.70
    }

    report = format_ragas_report(metrics)

    print("\n" + report)

    # Verify report contains all metrics
    assert "FAITHFULNESS: 0.92" in report or "FAITHFULNESS: 0.920" in report
    assert "ANSWER RELEVANCY: 0.88" in report or "ANSWER RELEVANCY: 0.880" in report
    assert "ANSWER CORRECTNESS: 0.91" in report or "ANSWER CORRECTNESS: 0.910" in report
    assert "CONTEXT PRECISION: 0.75" in report or "CONTEXT PRECISION: 0.750" in report

    # Verify explanations are present
    assert "WHAT: Does answer contradict" in report
    assert "HOW:" in report
    assert "INTERPRETATION:" in report

    print("\n✅ TEST 3 PASSED: Report formatted with nuclear explanations")


if __name__ == "__main__":
    try:
        test_sql_only_query()
        test_vector_query()
        test_format_report()

        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✅")
        print("=" * 80)
        print("\nRAGAS Implementation Summary:")
        print("- ✅ SQL-only queries: Context metrics set to None")
        print("- ✅ Vector queries: All 7 metrics calculated")
        print("- ✅ Report formatting: Nuclear explanations included")
        print("\nNext steps:")
        print("1. Run full evaluation: poetry run python -m src.evaluation.run_evaluation --type all")
        print("2. Review generated reports with RAGAS metrics")
        print("3. Commit changes")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
