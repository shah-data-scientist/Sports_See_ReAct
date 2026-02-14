"""
FILE: calculate_ragas_from_raw.py
STATUS: Active
RESPONSIBILITY: Calculate RAGAS metrics from already-collected raw vector evaluation data
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu

Reads raw vector evaluation results and calculates all 4 RAGAS metrics.
Avoids re-running API calls (saves 15+ minutes and rate limiting issues).
"""

import io
import json
import sys
from datetime import datetime
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.evaluation.vector_test_cases import EVALUATION_TEST_CASES


def calculate_ragas_metrics(raw_results_file: str):
    """Calculate all 4 RAGAS metrics from raw evaluation results."""
    print("\n" + "="*80)
    print("  CALCULATING RAGAS METRICS WITH UPDATED GOLD CONTEXTS")
    print("="*80)
    print(f"  Input: {raw_results_file}")
    print("  Metrics: Faithfulness, Answer Relevancy, Context Precision, Context Recall")
    print("  Gold Contexts: ACTUAL chunk text (regenerated)")
    print("="*80 + "\n")

    # Load raw results
    raw_path = Path(raw_results_file)
    if not raw_path.exists():
        print(f"ERROR: Raw results file not found: {raw_results_file}")
        return 1

    with open(raw_path, encoding="utf-8") as f:
        raw_results = json.load(f)

    # Load NEW gold contexts (actual chunk text)
    gold_contexts_file = Path("evaluation_results/vector_gold_contexts.json")
    if not gold_contexts_file.exists():
        print("ERROR: Gold contexts file not found. Run regenerate_gold_contexts.py first.")
        return 1

    with open(gold_contexts_file, encoding="utf-8") as f:
        gold_data = json.load(f)

    # Build lookups
    test_case_map = {tc.question: tc.ground_truth for tc in EVALUATION_TEST_CASES}
    gold_contexts_map = {item["question"]: item["gold_contexts"] for item in gold_data}

    # Update each result with ground truth answer AND new gold contexts
    for result in raw_results:
        question = result["question"]
        result["reference"] = test_case_map.get(question, "")
        result["reference_contexts"] = gold_contexts_map.get(question, [])

    # Lazy-load ragas and configure to use Gemini LLM + Mistral Embeddings
    try:
        from ragas import evaluate, RunConfig
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_mistralai import MistralAIEmbeddings
    except ImportError as e:
        print(f"ERROR: ragas dependencies not installed: {e}")
        return 1

    # Configure Gemini LLM for RAGAS judge
    print("Configuring RAGAS:")
    print("  LLM: Gemini (gemini-2.0-flash-lite)")
    print("  Embeddings: Mistral (mistral-embed)")

    gemini_llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite",
        temperature=0,
        google_api_key=settings.google_api_key
    )

    # Configure Mistral embeddings (consistent with FAISS index)
    mistral_embeddings = MistralAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.mistral_api_key,
    )
    ragas_embeddings = LangchainEmbeddingsWrapper(mistral_embeddings)

    # Configure RunConfig
    run_config = RunConfig(max_workers=1, max_wait=180)

    from datasets import Dataset

    # Filter out errors
    valid_results = [r for r in raw_results if "error" not in r and r["answer"]]

    if not valid_results:
        print("ERROR: No valid results to evaluate")
        return 1

    print(f"Valid results: {len(valid_results)}/{len(raw_results)}")

    # Prepare dataset
    dataset_dict = {
        "question": [r["question"] for r in valid_results],
        "answer": [r["answer"] for r in valid_results],
        "contexts": [r["contexts"] for r in valid_results],
        "reference": [r["reference"] for r in valid_results],
        "reference_contexts": [r.get("reference_contexts", []) for r in valid_results],
    }

    dataset = Dataset.from_dict(dataset_dict)

    print(f"\nEvaluating {len(valid_results)} test cases...")
    print("(This may take several minutes due to LLM judge calls)\n")

    # Run RAGAS evaluation with Gemini LLM + Mistral Embeddings
    try:
        evaluation_result = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            ],
            llm=gemini_llm,
            embeddings=ragas_embeddings,
            run_config=run_config,
        )

        print("\n" + "="*80)
        print("  RAGAS EVALUATION RESULTS")
        print("="*80)

        # Extract scores from EvaluationResult object
        import numpy as np

        def extract_score(result_obj, key):
            """Extract score from EvaluationResult, handling both dict and list/array values."""
            # Try dictionary-style access first (EvaluationResult supports [] notation)
            try:
                value = result_obj[key]
            except (KeyError, TypeError):
                # Try attribute access as fallback
                value = getattr(result_obj, key, 0)

            # Handle lists/arrays by taking mean
            if isinstance(value, (list, np.ndarray)):
                return float(np.mean([v for v in value if v is not None]))
            return float(value)

        scores = {
            "faithfulness": extract_score(evaluation_result, "faithfulness"),
            "answer_relevancy": extract_score(evaluation_result, "answer_relevancy"),
            "context_precision": extract_score(evaluation_result, "context_precision"),
            "context_recall": extract_score(evaluation_result, "context_recall"),
        }

        print(f"  Faithfulness:        {scores['faithfulness']:.3f}")
        print(f"  Answer Relevancy:    {scores['answer_relevancy']:.3f}")
        print(f"  Context Precision:   {scores['context_precision']:.3f}")
        print(f"  Context Recall:      {scores['context_recall']:.3f}")
        print("="*80 + "\n")

        # Save final results
        final_results = {
            "timestamp": datetime.now().isoformat(),
            "source_file": str(raw_path),
            "total_cases": len(EVALUATION_TEST_CASES),
            "evaluated_cases": len(valid_results),
            "ragas_scores": scores,  # Use the extracted scores dict
        }

        output_file = Path(f"evaluation_results/vector_ragas_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False)

        print(f"✓ Final RAGAS results saved to: {output_file}")
        return 0

    except Exception as e:
        print(f"ERROR during RAGAS evaluation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Use the raw results file from the failed evaluation
    raw_file = "evaluation_results/vector_ragas_raw_20260211_150318.json"
    sys.exit(calculate_ragas_metrics(raw_file))
