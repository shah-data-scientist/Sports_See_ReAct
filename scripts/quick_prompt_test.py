"""
FILE: quick_prompt_test.py
STATUS: Active
RESPONSIBILITY: Quick prompt variation testing on small subset before full evaluation
LAST MAJOR UPDATE: 2026-02-07
MAINTAINER: Shahu
"""

import os
# Fix OpenMP conflict before any other imports
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import json
import logging
import time
from pathlib import Path

from src.core.config import settings
from src.core.observability import configure_observability, logfire
from evaluation.vector_test_cases import EVALUATION_TEST_CASES
from src.services.chat import ChatService

logger = logging.getLogger(__name__)

# Test subset: 3 samples per category (12 total)
SUBSET_INDICES = [
    0,   # simple: "Which player has the best 3-point percentage..."
    3,   # simple: "How many assists does the league leader have..."
    10,  # simple: "How many games has the longest current winning streak..."
    12,  # complex: "Compare the offensive efficiency of the top 3..."
    14,  # complex: "Which players have shown the most improvement..."
    19,  # complex: "What trends in player salary vs performance..."
    24,  # noisy: "who iz the best player ever??? lebron or jordan"
    26,  # noisy: "stats for that tall guy from milwaukee"
    28,  # noisy: "waht are teh top 10 plyers in teh leage rite now??"
    36,  # conversational: "Who is the leading scorer in the NBA this season?"
    42,  # conversational: "Tell me about the Lakers' recent performance."
    44,  # conversational: "Is he in the MVP race?"
]


# Prompt variations to test
PROMPT_VARIATIONS = {
    "phase4_current": """Tu es '{app_name} Analyst AI', un assistant expert en analyse sportive NBA.

CONTEXTE:
---
{context}
---

QUESTION DE L'UTILISATEUR:
{question}

INSTRUCTIONS CRITIQUES:
1. Réponds DIRECTEMENT à la question posée - ne dévie pas du sujet
2. Base ta réponse UNIQUEMENT sur les informations du contexte ci-dessus
3. N'ajoute JAMAIS d'informations qui ne sont pas dans le contexte
4. Si le contexte ne contient pas l'information nécessaire, dis clairement "Je ne trouve pas cette information dans le contexte fourni"
5. Sois précis et concis - va droit au but
6. Cite les sources (noms de joueurs, équipes, statistiques) exactement comme indiqué dans le contexte

RÉPONSE:""",

    "balanced_french": """Tu es '{app_name} Analyst AI', un assistant expert en analyse sportive NBA.

CONTEXTE:
---
{context}
---

QUESTION:
{question}

INSTRUCTIONS:
- Réponds directement à la question en te basant sur le contexte fourni
- Sois précis et factuel
- Cite les sources quand c'est pertinent
- Si l'information n'est pas dans le contexte, indique-le brièvement

RÉPONSE:""",

    "concise_french": """Tu es '{app_name} Analyst AI', assistant expert NBA.

CONTEXTE: {context}

QUESTION: {question}

Réponds de manière précise en te basant sur le contexte ci-dessus.""",

    "english_detailed": """You are '{app_name} Analyst AI', an expert NBA sports analysis assistant.

CONTEXT:
---
{context}
---

USER QUESTION:
{question}

INSTRUCTIONS:
1. Answer the question directly and precisely
2. Base your answer on the context provided above
3. Be concise and factual
4. Cite sources when relevant
5. If information is not in the context, briefly state that

ANSWER:""",

    "english_concise": """You are '{app_name} Analyst AI', an NBA analysis expert.

CONTEXT: {context}

QUESTION: {question}

Provide a precise answer based on the context above.""",
}


def _build_generation_client():
    """Build Gemini client for sample generation if available."""
    if settings.google_api_key:
        from google import genai
        logger.info("Using Gemini for sample generation")
        return genai.Client(api_key=settings.google_api_key)
    return None


def _generate_with_retry(client, prompt: str, *, use_gemini: bool, max_retries: int = 3) -> str:
    """Generate response with retry logic."""
    for attempt in range(max_retries):
        try:
            if use_gemini:
                response = client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=prompt,
                )
                return response.text
            else:
                raise ValueError("Non-Gemini generation not supported in quick test")
        except Exception as e:
            is_retryable = (
                "429" in str(e)
                or "rate" in str(e).lower()
                or "ResourceExhausted" in type(e).__name__
            )
            if is_retryable and attempt < max_retries - 1:
                wait = 10 * (2 ** attempt)
                logger.warning(f"Rate limited, waiting {wait}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("All retries exhausted")


@logfire.instrument("quick_prompt_test")
def test_prompt_variation(
    prompt_name: str,
    prompt_template: str,
    chat_service: ChatService,
    subset: list,
) -> dict:
    """Test a single prompt variation on the subset.

    Args:
        prompt_name: Name of the prompt variation
        prompt_template: Prompt template string
        chat_service: ChatService instance
        subset: List of (index, test_case) tuples

    Returns:
        Dict with results for this prompt variation
    """
    gemini_client = _build_generation_client()
    if not gemini_client:
        raise ValueError("Gemini API key required for quick testing")

    logger.info(f"\n{'='*60}")
    logger.info(f"Testing prompt: {prompt_name}")
    logger.info(f"{'='*60}")

    samples = []

    for idx, tc in subset:
        logger.info(f"Sample {idx + 1}: {tc.question[:60]}")

        try:
            # Search (same for all prompts)
            search_results = chat_service.search(query=tc.question, k=settings.search_k)
            contexts = [r.text for r in search_results]
            context_str = "\n\n---\n\n".join(
                f"Source: {r.source} (Score: {r.score:.1f}%)\n{r.text}"
                for r in search_results
            )

            # Generate answer with this prompt variation
            prompt = prompt_template.format(
                app_name=settings.app_name,
                context=context_str,
                question=tc.question,
            )

            answer = _generate_with_retry(gemini_client, prompt, use_gemini=True)

            samples.append({
                "index": idx,
                "question": tc.question,
                "answer": answer,
                "contexts": contexts,
                "reference": tc.ground_truth,
                "category": tc.category.value,
            })

            time.sleep(2)  # Rate limiting

        except Exception as e:
            logger.error(f"Failed on sample {idx}: {e}")
            raise

    return {
        "prompt_name": prompt_name,
        "samples": samples,
        "sample_count": len(samples),
    }


def _build_evaluator_llm():
    """Build RAGAS evaluator LLM."""
    from ragas.llms import LangchainLLMWrapper

    if settings.google_api_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        logger.info("Using Gemini as RAGAS evaluator LLM")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            google_api_key=settings.google_api_key,
            temperature=0.0,
        )
    else:
        from langchain_mistralai import ChatMistralAI
        logger.info("Using Mistral as RAGAS evaluator LLM")
        llm = ChatMistralAI(
            model=settings.chat_model,
            api_key=settings.mistral_api_key,
            temperature=0.0,
        )
    return LangchainLLMWrapper(llm)


def _build_evaluator_embeddings():
    """Build embeddings for RAGAS evaluator."""
    from langchain_mistralai import MistralAIEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper

    logger.info("Using Mistral embeddings for RAGAS evaluator")
    embeddings = MistralAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.mistral_api_key,
    )
    return LangchainEmbeddingsWrapper(embeddings)


@logfire.instrument("evaluate_prompt_variation")
def evaluate_prompt_variation(result: dict) -> dict:
    """Run RAGAS evaluation on prompt variation results.

    Args:
        result: Dict with samples from test_prompt_variation

    Returns:
        Dict with metrics for this prompt
    """
    from ragas import EvaluationDataset, evaluate
    from ragas.metrics import Faithfulness, ResponseRelevancy

    logger.info(f"Evaluating prompt: {result['prompt_name']}")

    evaluator_llm = _build_evaluator_llm()
    evaluator_embeddings = _build_evaluator_embeddings()

    # Build dataset
    dataset_dicts = [
        {
            "user_input": s["question"],
            "response": s["answer"],
            "retrieved_contexts": s["contexts"],
            "reference": s["reference"],
        }
        for s in result["samples"]
    ]
    eval_dataset = EvaluationDataset.from_list(dataset_dicts)

    # Only evaluate 2 key metrics for speed
    metrics = [
        Faithfulness(llm=evaluator_llm),
        ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings),
    ]

    logger.info(f"Running RAGAS on {len(result['samples'])} samples...")
    ragas_result = evaluate(dataset=eval_dataset, metrics=metrics)

    df = ragas_result.to_pandas()

    # Calculate metrics
    def _safe_mean(series):
        valid = series.dropna()
        return float(valid.mean()) if len(valid) > 0 else None

    faithfulness = _safe_mean(df.get("faithfulness", []))
    answer_relevancy = _safe_mean(df.get("answer_relevancy", []))

    return {
        "prompt_name": result["prompt_name"],
        "sample_count": result["sample_count"],
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy,
    }


def print_comparison_table(results: list[dict]) -> None:
    """Print comparison table of prompt variations."""
    def fmt(val):
        return f"{val:.3f}" if val is not None else "N/A"

    print("\n" + "=" * 80)
    print("  QUICK PROMPT VARIATION TEST RESULTS")
    print("  12 samples (3 per category)")
    print("=" * 80)

    print("\n  METRICS BY PROMPT VARIATION")
    print("  " + "-" * 76)
    print(f"  {'Prompt Name':<25} {'Faithful':>12} {'Relevancy':>12} {'Score':>12}")
    print("  " + "-" * 76)

    # Sort by combined score (weighted: 40% faithfulness, 60% relevancy since relevancy is the priority)
    for r in sorted(results, key=lambda x: (x["faithfulness"] or 0) * 0.4 + (x["answer_relevancy"] or 0) * 0.6, reverse=True):
        score = (r["faithfulness"] or 0) * 0.4 + (r["answer_relevancy"] or 0) * 0.6
        print(f"  {r['prompt_name']:<25} {fmt(r['faithfulness']):>12} "
              f"{fmt(r['answer_relevancy']):>12} {fmt(score):>12}")

    print("  " + "-" * 76)
    print("  Note: Score = 0.4*Faithfulness + 0.6*AnswerRelevancy (prioritize relevancy)")
    print("=" * 80 + "\n")


def main() -> int:
    """Run quick prompt variation testing.

    Returns:
        Exit code (0 for success)
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    configure_observability()

    logger.info("Initializing ChatService with SQL enabled...")
    chat_service = ChatService(enable_sql=True)
    chat_service.ensure_ready()

    # Build subset
    subset = [(i, EVALUATION_TEST_CASES[i]) for i in SUBSET_INDICES]
    logger.info(f"Testing on {len(subset)} samples from 4 categories")

    # Test each prompt variation
    all_results = []

    for prompt_name, prompt_template in PROMPT_VARIATIONS.items():
        try:
            # Generate samples
            result = test_prompt_variation(prompt_name, prompt_template, chat_service, subset)

            # Evaluate
            metrics = evaluate_prompt_variation(result)
            all_results.append(metrics)

            logger.info(f"✓ {prompt_name}: F={metrics['faithfulness']:.3f}, R={metrics['answer_relevancy']:.3f}")

            # Save intermediate result
            output_path = Path(f"quick_test_results/{prompt_name}.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as f:
                json.dump({**result, **metrics}, f, indent=2, ensure_ascii=False)

            # Cooldown between prompts
            if prompt_name != list(PROMPT_VARIATIONS.keys())[-1]:
                logger.info("Cooling down 30s before next prompt...")
                time.sleep(30)

        except Exception as e:
            logger.error(f"Failed testing prompt '{prompt_name}': {e}")
            continue

    # Print comparison
    print_comparison_table(all_results)

    # Save summary
    summary_path = Path("quick_test_results/SUMMARY.json")
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "test_type": "Quick Prompt Variation Test",
                "sample_count": len(subset),
                "prompt_variations_tested": len(all_results),
                "results": all_results,
                "winner": max(all_results, key=lambda x: (x["faithfulness"] or 0) * 0.4 + (x["answer_relevancy"] or 0) * 0.6),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    logger.info(f"Summary saved to {summary_path}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
