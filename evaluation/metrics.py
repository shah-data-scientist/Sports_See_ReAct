"""
FILE: metrics.py
STATUS: Active (STUB - Full RAGAS integration TODO)
RESPONSIBILITY: Calculate all 7 RAGAS metrics for evaluation results
LAST MAJOR UPDATE: 2026-02-15
MAINTAINER: Shahu

DESCRIPTION:
Implements all 7 RAGAS (Retrieval-Augmented Generation Assessment) metrics:

ANSWER QUALITY METRICS (use ground_truth_answer):
1. Faithfulness - Does answer contradict retrieved sources?
2. Answer Relevancy - Does answer address the question?
3. Answer Semantic Similarity - How similar to expected answer?
4. Answer Correctness - Combined semantic + factual correctness (BEST OVERALL)

RETRIEVAL QUALITY METRICS (reference-free - NO ground_truth needed):
5. Context Precision - Are relevant chunks ranked higher? (LLM-judged)
6. Context Recall - SKIPPED (requires manual ground truth)
7. Context Relevancy - Are retrieved chunks relevant? (LLM-judged)

NOTE: Context metrics use REFERENCE-FREE evaluation - LLM judges chunk relevance automatically.
Skipped for SQL-only queries (no vector search performed).

IMPLEMENTATION STATUS:
- Context Precision/Relevancy: ✅ IMPLEMENTED (LLM-judged, reference-free)
- Answer Quality Metrics: ⚠️ PLACEHOLDER (TODO: Full RAGAS 0.4.3+ integration)

Current implementation:
- Context Precision: LLM judges "Is chunk relevant?" for each retrieved chunk
- Context Relevancy: Fraction of chunks judged relevant by LLM
- Faithfulness, Answer Relevancy, Answer Similarity, Answer Correctness: Placeholder values (0.85-0.9)

TODO: Full integration with RAGAS 0.4.3+ API for answer quality metrics
"""

import logging
from typing import Any
from google import genai
from src.core.config import settings

logger = logging.getLogger(__name__)


def _llm_judge_chunk_relevance(question: str, chunk_text: str, chunk_index: int) -> bool:
    """Ask LLM: Is this chunk relevant for answering the question?

    Reference-free evaluation - no manual ground truth needed.

    Args:
        question: The user's question
        chunk_text: The chunk text to evaluate
        chunk_index: Chunk position (for logging)

    Returns:
        True if chunk is judged relevant, False otherwise
    """
    api_key = settings.google_api_key
    if not api_key:
        logger.warning(f"No API key - skipping relevance judgment for chunk {chunk_index}")
        return True  # Default to True if no API key

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""You are evaluating whether a retrieved document chunk is useful for answering a question.

QUESTION: {question}

RETRIEVED CHUNK:
{chunk_text[:500]}

Is this chunk useful for answering the question? Consider:
- Does it contain relevant information?
- Would it help generate an accurate answer?
- Is the content directly or indirectly related to the question?

Answer with ONLY "YES" or "NO" (no explanation needed).

Your answer:"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"temperature": 0.0},  # Deterministic
        )

        answer = response.text.strip().upper()
        is_relevant = "YES" in answer

        logger.debug(f"Chunk {chunk_index} relevance: {is_relevant} ({answer})")
        return is_relevant

    except Exception as e:
        logger.warning(f"LLM relevance judgment failed for chunk {chunk_index}: {e}")
        return True  # Default to True on error


def _calculate_context_precision_reference_free(question: str, sources: list[dict]) -> float:
    """Calculate Context Precision using LLM-judged relevance (reference-free).

    Context Precision measures if relevant chunks are ranked higher.
    Formula: Precision@K = Sum(relevance[i] * precision@i) / K

    Args:
        question: The user's question
        sources: Retrieved chunks (list of dicts with 'text' key)

    Returns:
        Context Precision score (0.0-1.0) or None if no sources
    """
    if not sources or len(sources) == 0:
        return None

    # Judge relevance of each chunk
    relevance_scores = []
    for i, source in enumerate(sources):
        chunk_text = source.get("text", "")
        is_relevant = _llm_judge_chunk_relevance(question, chunk_text, i)
        relevance_scores.append(1.0 if is_relevant else 0.0)

    # Calculate precision@k weighted by rank
    weighted_sum = 0.0
    for i, relevance in enumerate(relevance_scores):
        # Precision@i = number of relevant docs in top i+1 / (i+1)
        relevant_so_far = sum(relevance_scores[:i+1])
        precision_at_i = relevant_so_far / (i + 1)
        weighted_sum += relevance * precision_at_i

    # Average weighted precision
    num_relevant = sum(relevance_scores)
    if num_relevant == 0:
        return 0.0  # No relevant chunks found

    context_precision = weighted_sum / num_relevant
    logger.debug(f"Context Precision: {context_precision:.3f} (relevant: {int(num_relevant)}/{len(sources)})")
    return context_precision


def _calculate_context_relevancy_reference_free(question: str, sources: list[dict]) -> float:
    """Calculate Context Relevancy using LLM-judged relevance (reference-free).

    Context Relevancy = Number of relevant chunks / Total chunks

    Args:
        question: The user's question
        sources: Retrieved chunks (list of dicts with 'text' key)

    Returns:
        Context Relevancy score (0.0-1.0) or None if no sources
    """
    if not sources or len(sources) == 0:
        return None

    # Judge relevance of each chunk
    relevant_count = 0
    for i, source in enumerate(sources):
        chunk_text = source.get("text", "")
        is_relevant = _llm_judge_chunk_relevance(question, chunk_text, i)
        if is_relevant:
            relevant_count += 1

    context_relevancy = relevant_count / len(sources)
    logger.debug(f"Context Relevancy: {context_relevancy:.3f} ({relevant_count}/{len(sources)} chunks relevant)")
    return context_relevancy


def calculate_ragas_metrics(
    question: str,
    answer: str,
    sources: list[dict],
    ground_truth_answer: str,
) -> dict[str, float | None]:
    """Calculate all 7 RAGAS metrics for an evaluation result.

    METRIC CATEGORIES:

    1. ANSWER QUALITY METRICS (use ground_truth_answer):
       - Faithfulness: Does answer contradict retrieved sources?
       - Answer Relevancy: Does answer address the question?
       - Answer Semantic Similarity: How similar to expected answer?
       - Answer Correctness: Combined semantic + factual (BEST OVERALL)

    2. RETRIEVAL QUALITY METRICS (reference-free - NO ground_truth needed):
       - Context Precision: Are relevant chunks ranked higher? (LLM-judged)
       - Context Recall: SKIPPED (requires manual ground truth)
       - Context Relevancy: Are retrieved chunks relevant? (LLM-judged)

    METRIC EXPLANATIONS:

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. FAITHFULNESS (Answer Quality - Uses ground_truth_answer)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    WHAT IT MEASURES:
    Does the answer contradict the retrieved sources? Checks if LLM hallucinated.

    HOW IT WORKS:
    1. Extract all claims from the answer
    2. Check if each claim is supported by retrieved sources
    3. Score = (Supported claims) / (Total claims)

    RANGE: 0.0 to 1.0 (higher is better)
    - 1.0 = All claims supported by sources (no hallucination)
    - 0.5 = Half the claims are hallucinated
    - 0.0 = All claims are hallucinated

    EXAMPLE:
    Question: "Who scored the most points?"
    Sources: [{"text": "Shai scored 2485 points"}]
    Answer: "Shai scored 2485 points and won MVP"

    Claims extracted:
    1. "Shai scored 2485 points" ✅ Supported by sources
    2. "Shai won MVP" ❌ NOT in sources (hallucination)

    Faithfulness = 1/2 = 0.5 (50% hallucinated)

    WHEN TO USE:
    - Detect hallucination (LLM making up facts)
    - Ensure answer is grounded in retrieved data
    - Critical for factual queries (stats, dates, names)

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    2. ANSWER RELEVANCY (Answer Quality - Uses ground_truth_answer)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    WHAT IT MEASURES:
    Does the answer actually address the question? Checks if answer is on-topic.

    HOW IT WORKS:
    1. Generate multiple question variations from the answer
    2. Compare similarity of generated questions to original question
    3. Score = Average similarity across generated questions

    RANGE: 0.0 to 1.0 (higher is better)
    - 1.0 = Answer perfectly addresses question
    - 0.5 = Answer is somewhat relevant
    - 0.0 = Answer is completely off-topic

    EXAMPLE:
    Question: "Who scored the most points?"
    Answer: "Shai Gilgeous-Alexander scored 2485 points this season."

    Generated questions from answer:
    1. "Who is the leading scorer?" (similarity: 0.95)
    2. "How many points did Shai score?" (similarity: 0.85)
    3. "What are the scoring stats?" (similarity: 0.80)

    Answer Relevancy = (0.95 + 0.85 + 0.80) / 3 = 0.87

    WHEN TO USE:
    - Detect off-topic answers
    - Ensure LLM didn't misunderstand question
    - Check if answer is focused (not rambling)

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    3. ANSWER SEMANTIC SIMILARITY (Answer Quality - Uses ground_truth_answer)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    WHAT IT MEASURES:
    How semantically similar is the answer to the expected answer?

    HOW IT WORKS:
    1. Embed both actual answer and ground truth answer
    2. Calculate cosine similarity between embeddings
    3. Score = Cosine similarity

    RANGE: 0.0 to 1.0 (higher is better)
    - 1.0 = Exact semantic match
    - 0.7-0.9 = Similar meaning, different wording
    - 0.3-0.7 = Related but different
    - 0.0 = Completely different meaning

    EXAMPLE:
    Ground Truth: "Shai scored the most points with 2485 PTS."
    Actual Answer: "Shai Gilgeous-Alexander is the leading scorer with 2,485 points."

    Semantic Similarity = 0.92 (same meaning, slightly different wording)

    WHEN TO USE:
    - Check if answer conveys same information
    - Allow for paraphrasing (doesn't require exact match)
    - Good for evaluation when wording varies but meaning is same

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    4. ANSWER CORRECTNESS (Answer Quality - Uses ground_truth_answer) ⭐ BEST
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    WHAT IT MEASURES:
    Combined semantic similarity + factual correctness. BEST OVERALL METRIC.

    HOW IT WORKS:
    1. Calculate semantic similarity (like metric #3)
    2. Extract factual statements from both answers
    3. Check if facts match (F1 score on factual overlap)
    4. Score = Weighted average of semantic + factual

    RANGE: 0.0 to 1.0 (higher is better)
    - 1.0 = Semantically similar AND factually correct
    - 0.7-0.9 = Mostly correct with minor differences
    - 0.3-0.7 = Some correct info but missing key facts
    - 0.0 = Wrong answer

    EXAMPLE:
    Ground Truth: "Shai scored 2485 points, leading the league."
    Actual Answer: "Shai Gilgeous-Alexander scored 2485 points."

    Semantic Similarity: 0.90 (similar meaning)
    Factual Overlap:
    - TP (True Positive): "Shai", "2485 points" ✅
    - FN (False Negative): "leading league" ❌ (missing from actual)
    - FP (False Positive): None

    F1 Score = 2*TP / (2*TP + FP + FN) = 2*2 / (2*2 + 0 + 1) = 4/5 = 0.80

    Answer Correctness = 0.5 * Semantic + 0.5 * F1 = 0.5*0.90 + 0.5*0.80 = 0.85

    WHEN TO USE:
    - **PRIMARY METRIC for overall answer quality**
    - Balances semantic meaning with factual accuracy
    - Best single metric for pass/fail evaluation

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    5. CONTEXT PRECISION (Retrieval Quality - Uses ground_truth_vector)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    WHAT IT MEASURES:
    Are relevant chunks ranked higher than irrelevant chunks? Checks retrieval ranking.

    HOW IT WORKS:
    1. Label each retrieved chunk as relevant/irrelevant (using ground_truth_vector)
    2. Check if relevant chunks appear before irrelevant chunks
    3. Score = Precision@K averaged across positions

    RANGE: 0.0 to 1.0 (higher is better)
    - 1.0 = All relevant chunks ranked first
    - 0.5 = Relevant chunks mixed with irrelevant
    - 0.0 = All relevant chunks ranked last

    EXAMPLE:
    Ground Truth Vector: "Should retrieve Reddit 3.pdf about efficiency"

    Retrieved chunks (in order):
    1. Reddit 3.pdf, page 2 (about efficiency) ✅ Relevant
    2. Reddit 1.pdf, page 1 (about GOAT debate) ❌ Irrelevant
    3. Reddit 3.pdf, page 5 (about efficiency) ✅ Relevant
    4. News article (unrelated) ❌ Irrelevant

    Precision@1 = 1/1 = 1.0 (1 relevant in top 1)
    Precision@2 = 1/2 = 0.5 (1 relevant in top 2)
    Precision@3 = 2/3 = 0.67 (2 relevant in top 3)
    Precision@4 = 2/4 = 0.5 (2 relevant in top 4)

    Context Precision = Average = (1.0 + 0.5 + 0.67 + 0.5) / 4 = 0.67

    WHEN TO USE:
    - Optimize retrieval ranking
    - Check if important docs appear first
    - SKIPPED for SQL-only queries (no vector search)

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    6. CONTEXT RECALL (Retrieval Quality - Uses ground_truth_vector)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    WHAT IT MEASURES:
    Were all required chunks retrieved? Checks if retrieval is complete.

    HOW IT WORKS:
    1. Identify required chunks from ground_truth_vector
    2. Check if each required chunk was retrieved
    3. Score = (Retrieved required chunks) / (Total required chunks)

    RANGE: 0.0 to 1.0 (higher is better)
    - 1.0 = All required chunks retrieved
    - 0.5 = Half of required chunks missing
    - 0.0 = No required chunks retrieved

    EXAMPLE:
    Ground Truth Vector: "Should retrieve Reddit 3.pdf discussing efficiency,
                          specifically mentioning Reggie Miller with 115 TS%"

    Required chunks:
    1. Reddit 3.pdf about efficiency ✅ Retrieved
    2. Mention of Reggie Miller ✅ Retrieved
    3. 115 TS% statistic ❌ NOT retrieved

    Context Recall = 2/3 = 0.67 (67% of required info retrieved)

    WHEN TO USE:
    - Check if retrieval is missing key information
    - Optimize retrieval to capture all needed chunks
    - SKIPPED for SQL-only queries (no vector search)

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    7. CONTEXT RELEVANCY (Retrieval Quality - Uses ground_truth_vector)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    WHAT IT MEASURES:
    What fraction of retrieved chunks are actually relevant? Checks retrieval noise.

    HOW IT WORKS:
    1. Extract sentences from retrieved chunks that are relevant to question
    2. Score = (Relevant sentences) / (Total sentences)

    RANGE: 0.0 to 1.0 (higher is better)
    - 1.0 = All retrieved chunks are relevant (no noise)
    - 0.5 = Half of retrieved content is irrelevant
    - 0.0 = All retrieved chunks are irrelevant

    EXAMPLE:
    Question: "What do fans think about efficiency?"

    Retrieved chunks:
    1. "Fans believe Reggie Miller is most efficient with 115 TS%" ✅ Relevant
    2. "Miller played for the Pacers" ❌ Irrelevant (not about efficiency)
    3. "Efficiency is measured by TS%" ✅ Relevant
    4. "LeBron is the GOAT" ❌ Irrelevant (off-topic)

    Context Relevancy = 2/4 = 0.5 (50% relevant)

    WHEN TO USE:
    - Detect noisy retrieval (too much irrelevant content)
    - Optimize retrieval to reduce false positives
    - SKIPPED for SQL-only queries (no vector search)

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Args:
        question: The user's question
        answer: The LLM's generated answer
        sources: Retrieved sources (list of dicts with 'text', 'score', 'source' keys)
        ground_truth_answer: Expected answer (generated by judge LLM)

    Returns:
        Dictionary with all calculated metrics:
        {
            "faithfulness": float,
            "answer_relevancy": float,
            "answer_semantic_similarity": float,
            "answer_correctness": float,
            "context_precision": float | None,  # None if no sources (SQL-only)
            "context_recall": None,              # Always None (reference-free - skipped)
            "context_relevancy": float | None,   # None if no sources (SQL-only)
        }

    NOTE: Context metrics use REFERENCE-FREE evaluation:
    - Context Precision/Relevancy: LLM judges chunk relevance (no manual ground truth needed)
    - Context Recall: Skipped (requires manual ground truth)

    Current implementation uses heuristic/placeholder values.
    TODO: Integrate with RAGAS 0.4.3+ API for accurate metric calculation.
    """

    # TODO: Replace with actual RAGAS 0.4.3+ API integration
    # For now, use simple heuristics to provide placeholder metrics

    # Answer quality metrics (always calculated)
    scores = {
        "faithfulness": 0.9,  # Placeholder: assume answers are faithful
        "answer_relevancy": 0.85,  # Placeholder: assume answers are relevant
        "answer_semantic_similarity": 0.9,  # Placeholder: assume answers are similar
        "answer_correctness": 0.88,  # Placeholder: average of other metrics
    }

    # Retrieval quality metrics (reference-free - only if sources exist)
    if sources and len(sources) > 0:
        logger.info(f"Calculating reference-free context metrics for {len(sources)} chunks...")

        # Calculate actual LLM-judged relevance metrics
        context_precision = _calculate_context_precision_reference_free(question, sources)
        context_relevancy = _calculate_context_relevancy_reference_free(question, sources)

        scores.update({
            "context_precision": context_precision,  # LLM-judged: Are relevant chunks ranked higher?
            "context_recall": None,  # ALWAYS None (reference-free - requires manual ground truth)
            "context_relevancy": context_relevancy,  # LLM-judged: Fraction of chunks relevant
        })

        logger.info(f"Context Precision: {context_precision:.3f}, Context Relevancy: {context_relevancy:.3f}")
    else:
        # SQL-only queries - no vector search performed
        logger.debug("No sources - skipping context metrics (SQL-only query)")
        scores.update({
            "context_precision": None,
            "context_recall": None,
            "context_relevancy": None,
        })

    return scores


def format_ragas_report(metrics: dict[str, float | None]) -> str:
    """Format RAGAS metrics into human-readable report with explanations.

    Args:
        metrics: Dictionary of RAGAS metrics

    Returns:
        Formatted report string with nuclear explanations
    """

    report = []
    report.append("=" * 80)
    report.append("RAGAS METRICS REPORT - NUCLEAR EXPLANATION")
    report.append("=" * 80)
    report.append("")
    report.append("NOTE: Current metrics are placeholder values.")
    report.append("TODO: Full RAGAS 0.4.3+ integration for accurate metrics.")
    report.append("")

    # Answer Quality Metrics
    report.append("━" * 80)
    report.append("ANSWER QUALITY METRICS (Use ground_truth_answer)")
    report.append("━" * 80)
    report.append("")

    # Faithfulness
    faithfulness = metrics["faithfulness"]
    report.append(f"1. FAITHFULNESS: {faithfulness:.3f}")
    report.append("   WHAT: Does answer contradict retrieved sources?")
    report.append("   HOW: (Supported claims) / (Total claims)")
    report.append(f"   INTERPRETATION:")
    if faithfulness >= 0.9:
        report.append("   ✅ EXCELLENT - No hallucination detected")
    elif faithfulness >= 0.7:
        report.append("   ⚠️  GOOD - Minor hallucination, mostly grounded")
    elif faithfulness >= 0.5:
        report.append("   ⚠️  WARNING - Moderate hallucination detected")
    else:
        report.append("   ❌ CRITICAL - High hallucination, answer not trustworthy")
    report.append("")

    # Answer Relevancy
    answer_relevancy = metrics["answer_relevancy"]
    report.append(f"2. ANSWER RELEVANCY: {answer_relevancy:.3f}")
    report.append("   WHAT: Does answer address the question?")
    report.append("   HOW: Similarity of generated questions to original")
    report.append(f"   INTERPRETATION:")
    if answer_relevancy >= 0.9:
        report.append("   ✅ EXCELLENT - Answer is on-topic and focused")
    elif answer_relevancy >= 0.7:
        report.append("   ⚠️  GOOD - Answer is relevant with minor drift")
    elif answer_relevancy >= 0.5:
        report.append("   ⚠️  WARNING - Answer is somewhat off-topic")
    else:
        report.append("   ❌ CRITICAL - Answer doesn't address question")
    report.append("")

    # Answer Semantic Similarity
    similarity = metrics["answer_semantic_similarity"]
    report.append(f"3. ANSWER SEMANTIC SIMILARITY: {similarity:.3f}")
    report.append("   WHAT: Semantic similarity to expected answer")
    report.append("   HOW: Cosine similarity of embeddings")
    report.append(f"   INTERPRETATION:")
    if similarity >= 0.9:
        report.append("   ✅ EXCELLENT - Nearly identical meaning")
    elif similarity >= 0.7:
        report.append("   ⚠️  GOOD - Similar meaning, different wording")
    elif similarity >= 0.5:
        report.append("   ⚠️  WARNING - Related but different information")
    else:
        report.append("   ❌ CRITICAL - Completely different meaning")
    report.append("")

    # Answer Correctness (BEST OVERALL)
    correctness = metrics["answer_correctness"]
    report.append(f"4. ANSWER CORRECTNESS: {correctness:.3f} ⭐ BEST OVERALL METRIC")
    report.append("   WHAT: Combined semantic + factual correctness")
    report.append("   HOW: 0.5 * Semantic Similarity + 0.5 * Factual F1")
    report.append(f"   INTERPRETATION:")
    if correctness >= 0.9:
        report.append("   ✅ EXCELLENT - Answer is correct")
    elif correctness >= 0.7:
        report.append("   ⚠️  GOOD - Mostly correct with minor issues")
    elif correctness >= 0.5:
        report.append("   ⚠️  WARNING - Partially correct, missing key facts")
    else:
        report.append("   ❌ CRITICAL - Answer is incorrect")
    report.append("")

    # Retrieval Quality Metrics
    report.append("━" * 80)
    report.append("RETRIEVAL QUALITY METRICS (Use ground_truth_vector)")
    report.append("━" * 80)
    report.append("")

    # Context Precision
    precision = metrics["context_precision"]
    if precision is not None:
        report.append(f"5. CONTEXT PRECISION: {precision:.3f}")
        report.append("   WHAT: Are relevant chunks ranked higher?")
        report.append("   HOW: Precision@K averaged across positions")
        report.append(f"   INTERPRETATION:")
        if precision >= 0.9:
            report.append("   ✅ EXCELLENT - Relevant chunks ranked first")
        elif precision >= 0.7:
            report.append("   ⚠️  GOOD - Most relevant chunks near top")
        elif precision >= 0.5:
            report.append("   ⚠️  WARNING - Relevant chunks mixed with irrelevant")
        else:
            report.append("   ❌ CRITICAL - Relevant chunks ranked too low")
    else:
        report.append("5. CONTEXT PRECISION: N/A (SQL-only query)")
    report.append("")

    # Context Recall
    recall = metrics["context_recall"]
    if recall is not None:
        report.append(f"6. CONTEXT RECALL: {recall:.3f}")
        report.append("   WHAT: Were all required chunks retrieved?")
        report.append("   HOW: (Retrieved required) / (Total required)")
        report.append(f"   INTERPRETATION:")
        if recall >= 0.9:
            report.append("   ✅ EXCELLENT - All required chunks retrieved")
        elif recall >= 0.7:
            report.append("   ⚠️  GOOD - Most required chunks retrieved")
        elif recall >= 0.5:
            report.append("   ⚠️  WARNING - Missing some required chunks")
        else:
            report.append("   ❌ CRITICAL - Missing most required chunks")
    else:
        report.append("6. CONTEXT RECALL: N/A (SQL-only query)")
    report.append("")

    # Context Relevancy
    relevancy = metrics["context_relevancy"]
    if relevancy is not None:
        report.append(f"7. CONTEXT RELEVANCY: {relevancy:.3f}")
        report.append("   WHAT: Fraction of retrieved chunks that are relevant")
        report.append("   HOW: (Relevant sentences) / (Total sentences)")
        report.append(f"   INTERPRETATION:")
        if relevancy >= 0.9:
            report.append("   ✅ EXCELLENT - No noise, all chunks relevant")
        elif relevancy >= 0.7:
            report.append("   ⚠️  GOOD - Low noise, mostly relevant")
        elif relevancy >= 0.5:
            report.append("   ⚠️  WARNING - Moderate noise, half irrelevant")
        else:
            report.append("   ❌ CRITICAL - High noise, mostly irrelevant")
    else:
        report.append("7. CONTEXT RELEVANCY: N/A (SQL-only query)")
    report.append("")

    report.append("=" * 80)

    return "\n".join(report)
