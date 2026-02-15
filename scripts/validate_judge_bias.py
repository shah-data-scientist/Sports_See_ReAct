"""
FILE: validate_judge_bias.py
STATUS: Active
RESPONSIBILITY: Compare Gemini vs Claude as judges to quantify evaluation bias
CREATED: 2026-02-15
MAINTAINER: Shahu

This script evaluates the same answers with both:
1. Gemini (same model as generator) - potentially biased
2. Claude (different model) - unbiased baseline

Metrics compared:
- Answer Correctness
- Faithfulness
- Answer Relevancy
- Context Precision
- Context Relevancy

Output: Bias report showing score differences and examples
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# LLM clients
from google import genai
from anthropic import Anthropic

# Check for API keys
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not set - needed for Gemini judge")
if not os.getenv("ANTHROPIC_API_KEY"):
    raise ValueError("ANTHROPIC_API_KEY not set - needed for Claude judge")

print("Initializing LLM clients...")
gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def load_test_results() -> List[Dict]:
    """Load the 9 test case results from previous run."""
    results_path = Path("evaluation_results/9_case_smart_tool_selection_test.json")

    if not results_path.exists():
        raise FileNotFoundError(
            f"Test results not found at {results_path}. "
            "Please run test_9_evaluation_cases.py first."
        )

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["results"]


def judge_with_gemini(question: str, answer: str, ground_truth: str) -> Dict[str, float]:
    """Evaluate answer quality using Gemini as judge.

    Args:
        question: Original user question
        answer: Generated answer to evaluate
        ground_truth: Expected/reference answer

    Returns:
        Dict with metric scores (0-1)
    """

    prompt = f"""You are evaluating the quality of an AI assistant's answer.

USER QUESTION:
{question}

GENERATED ANSWER:
{answer}

EXPECTED ANSWER (Reference):
{ground_truth}

Rate the GENERATED ANSWER on these metrics (0.0 to 1.0):

1. CORRECTNESS: Does it provide accurate information matching the reference?
   - 1.0 = Completely correct, matches reference facts
   - 0.5 = Partially correct, missing some facts
   - 0.0 = Incorrect or contradicts reference

2. FAITHFULNESS: Does it avoid hallucinations?
   - 1.0 = All claims are supported
   - 0.5 = Some unsupported claims
   - 0.0 = Contains hallucinations

3. RELEVANCY: Does it directly address the question?
   - 1.0 = Directly answers, no drift
   - 0.5 = Relevant but incomplete
   - 0.0 = Off-topic or tangential

Respond with ONLY this JSON format:
{{
  "correctness": 0.0-1.0,
  "faithfulness": 0.0-1.0,
  "relevancy": 0.0-1.0,
  "reasoning": "Brief explanation"
}}"""

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"temperature": 0.0}  # Deterministic
        )

        # Parse JSON response
        result = json.loads(response.text)

        return {
            "correctness": result["correctness"],
            "faithfulness": result["faithfulness"],
            "relevancy": result["relevancy"],
            "reasoning": result.get("reasoning", "")
        }

    except Exception as e:
        print(f"Gemini judge error: {e}")
        return {
            "correctness": 0.0,
            "faithfulness": 0.0,
            "relevancy": 0.0,
            "reasoning": f"Error: {str(e)}"
        }


def judge_with_claude(question: str, answer: str, ground_truth: str) -> Dict[str, float]:
    """Evaluate answer quality using Claude as judge (unbiased baseline).

    Args:
        question: Original user question
        answer: Generated answer to evaluate
        ground_truth: Expected/reference answer

    Returns:
        Dict with metric scores (0-1)
    """

    prompt = f"""You are evaluating the quality of an AI assistant's answer.

USER QUESTION:
{question}

GENERATED ANSWER:
{answer}

EXPECTED ANSWER (Reference):
{ground_truth}

Rate the GENERATED ANSWER on these metrics (0.0 to 1.0):

1. CORRECTNESS: Does it provide accurate information matching the reference?
   - 1.0 = Completely correct, matches reference facts
   - 0.5 = Partially correct, missing some facts
   - 0.0 = Incorrect or contradicts reference

2. FAITHFULNESS: Does it avoid hallucinations?
   - 1.0 = All claims are supported
   - 0.5 = Some unsupported claims
   - 0.0 = Contains hallucinations

3. RELEVANCY: Does it directly address the question?
   - 1.0 = Directly answers, no drift
   - 0.5 = Relevant but incomplete
   - 0.0 = Off-topic or tangential

Respond with ONLY this JSON format:
{{
  "correctness": 0.0-1.0,
  "faithfulness": 0.0-1.0,
  "relevancy": 0.0-1.0,
  "reasoning": "Brief explanation"
}}"""

    try:
        message = claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.0,  # Deterministic
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON response
        result = json.loads(message.content[0].text)

        return {
            "correctness": result["correctness"],
            "faithfulness": result["faithfulness"],
            "relevancy": result["relevancy"],
            "reasoning": result.get("reasoning", "")
        }

    except Exception as e:
        print(f"Claude judge error: {e}")
        return {
            "correctness": 0.0,
            "faithfulness": 0.0,
            "relevancy": 0.0,
            "reasoning": f"Error: {str(e)}"
        }


def create_ground_truth(test_case: Dict) -> str:
    """Create reference answer from test case data.

    For bias validation, we use a simple ground truth based on
    the question type and expected answer structure.
    """
    question = test_case["question"]
    test_type = test_case.get("test_type", "UNKNOWN")

    # Simple ground truths for the 9 test cases
    ground_truths = {
        "Who scored the most points this season?":
            "Shai Gilgeous-Alexander scored the most points with 2485 points.",

        "Who are the top 3 rebounders in the league?":
            "The top 3 rebounders are Ivica Zubac (1008), Domantas Sabonis (973), and Karl-Anthony Towns (922).",

        "Who are the top 5 players in steals?":
            "The top 5 players in steals are Dyson Daniels (228), Shai Gilgeous-Alexander (129), Nikola Jokić (126), Kris Dunn (126), and Cason Wallace (122).",

        "What do Reddit users think about teams that have impressed?":
            "Reddit users have discussed teams like the Orlando Magic positively, noting their impressive performance.",

        "What are the most popular opinions about the top teams?":
            "Popular opinions focus on the Oklahoma City Thunder and Cleveland Cavaliers as top teams based on their records.",

        "What do fans debate about Reggie Miller's efficiency?":
            "Fans debate Reggie Miller's efficiency, with some discussing his high true shooting percentage despite varied opinions on efficiency as a metric.",

        "Who scored the most points this season and what makes them an effective scorer?":
            "Shai Gilgeous-Alexander scored 2485 points. He is effective due to his high true shooting percentage (63.7%) and efficient scoring.",

        "Compare LeBron James and Kevin Durant's scoring this season and explain their scoring styles.":
            "LeBron scored 1708 points (51.3 FG%, 37.6 3P%) while Durant scored 1649 points (52.7 FG%, 43.0 3P%). Durant is more efficient from three-point range.",

        "What is Nikola Jokić's scoring average and why is he considered an elite offensive player?":
            "Nikola Jokić averages 29.6 points per game. He is considered elite due to his scoring efficiency and playmaking ability."
    }

    return ground_truths.get(question, "Reference answer not available.")


def calculate_bias_stats(comparisons: List[Dict]) -> Dict:
    """Calculate bias statistics from judge comparisons."""

    gemini_scores = {
        "correctness": [],
        "faithfulness": [],
        "relevancy": []
    }

    claude_scores = {
        "correctness": [],
        "faithfulness": [],
        "relevancy": []
    }

    biases = {
        "correctness": [],
        "faithfulness": [],
        "relevancy": []
    }

    for comp in comparisons:
        for metric in ["correctness", "faithfulness", "relevancy"]:
            gemini_score = comp["gemini_scores"][metric]
            claude_score = comp["claude_scores"][metric]
            bias = gemini_score - claude_score

            gemini_scores[metric].append(gemini_score)
            claude_scores[metric].append(claude_score)
            biases[metric].append(bias)

    stats = {}

    for metric in ["correctness", "faithfulness", "relevancy"]:
        avg_gemini = sum(gemini_scores[metric]) / len(gemini_scores[metric])
        avg_claude = sum(claude_scores[metric]) / len(claude_scores[metric])
        avg_bias = sum(biases[metric]) / len(biases[metric])

        stats[metric] = {
            "avg_gemini": round(avg_gemini, 3),
            "avg_claude": round(avg_claude, 3),
            "avg_bias": round(avg_bias, 3),
            "bias_percentage": round(avg_bias * 100, 1),
            "max_bias": round(max(biases[metric]), 3),
            "min_bias": round(min(biases[metric]), 3)
        }

    return stats


def main():
    """Run bias validation on 9 test cases."""

    print("\n" + "=" * 100)
    print("JUDGE BIAS VALIDATION - Gemini vs Claude")
    print("=" * 100)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Comparing:")
    print("  • Gemini 2.0 Flash (same as generator) - potentially biased")
    print("  • Claude 3.5 Sonnet (different model) - unbiased baseline")
    print("=" * 100)

    # Load test results
    print("\nLoading test results...")
    test_results = load_test_results()
    print(f"Loaded {len(test_results)} test cases")

    # Evaluate each case with both judges
    comparisons = []

    for i, test_case in enumerate(test_results, 1):
        question = test_case["question"]
        answer = test_case.get("answer_preview", "")
        ground_truth = create_ground_truth(test_case)

        print(f"\n[{i}/{len(test_results)}] Evaluating: '{question[:60]}...'")

        # Judge with Gemini
        print("  • Gemini judge...", end=" ", flush=True)
        gemini_scores = judge_with_gemini(question, answer, ground_truth)
        print(f"✓ (C:{gemini_scores['correctness']:.2f}, F:{gemini_scores['faithfulness']:.2f}, R:{gemini_scores['relevancy']:.2f})")

        # Judge with Claude
        print("  • Claude judge...", end=" ", flush=True)
        claude_scores = judge_with_claude(question, answer, ground_truth)
        print(f"✓ (C:{claude_scores['correctness']:.2f}, F:{claude_scores['faithfulness']:.2f}, R:{claude_scores['relevancy']:.2f})")

        # Calculate bias
        bias = {
            "correctness": gemini_scores['correctness'] - claude_scores['correctness'],
            "faithfulness": gemini_scores['faithfulness'] - claude_scores['faithfulness'],
            "relevancy": gemini_scores['relevancy'] - claude_scores['relevancy']
        }

        # Flag significant bias
        max_bias = max(abs(bias['correctness']), abs(bias['faithfulness']), abs(bias['relevancy']))
        if max_bias > 0.15:
            print(f"  ⚠️  Bias detected: {max_bias:+.2f} (Gemini - Claude)")

        comparisons.append({
            "test_number": i,
            "question": question,
            "answer": answer,
            "test_type": test_case.get("test_type"),
            "category": test_case.get("category"),
            "gemini_scores": gemini_scores,
            "claude_scores": claude_scores,
            "bias": bias
        })

    # Calculate overall statistics
    print("\n" + "=" * 100)
    print("BIAS ANALYSIS RESULTS")
    print("=" * 100)

    stats = calculate_bias_stats(comparisons)

    print("\nOverall Score Comparison:")
    print(f"{'Metric':<15} {'Gemini Avg':<12} {'Claude Avg':<12} {'Bias':<10} {'Bias %'}")
    print("-" * 60)

    for metric in ["correctness", "faithfulness", "relevancy"]:
        s = stats[metric]
        bias_sign = "+" if s['avg_bias'] > 0 else ""
        print(f"{metric.title():<15} {s['avg_gemini']:<12.3f} {s['avg_claude']:<12.3f} "
              f"{bias_sign}{s['avg_bias']:<10.3f} {bias_sign}{s['bias_percentage']:.1f}%")

    # Interpretation
    print("\n" + "=" * 100)
    print("INTERPRETATION")
    print("=" * 100)

    avg_total_bias = sum(stats[m]['avg_bias'] for m in ["correctness", "faithfulness", "relevancy"]) / 3

    if avg_total_bias > 0.10:
        verdict = "⚠️  SIGNIFICANT BIAS DETECTED"
        recommendation = "Use different judge (Claude or GPT-4) for production evaluation"
    elif avg_total_bias > 0.05:
        verdict = "⚠️  MODERATE BIAS DETECTED"
        recommendation = "Acceptable for development, but consider different judge for production"
    else:
        verdict = "✅ MINIMAL BIAS"
        recommendation = "Same-model judging is acceptable for your use case"

    print(f"\nVerdict: {verdict}")
    print(f"Average Bias: {avg_total_bias:+.3f} ({avg_total_bias*100:+.1f}%)")
    print(f"\nRecommendation: {recommendation}")

    # Show examples of high bias
    print("\n" + "=" * 100)
    print("HIGH BIAS EXAMPLES (|bias| > 0.15)")
    print("=" * 100)

    high_bias_examples = [
        c for c in comparisons
        if max(abs(c['bias']['correctness']), abs(c['bias']['faithfulness']), abs(c['bias']['relevancy'])) > 0.15
    ]

    if high_bias_examples:
        for example in high_bias_examples:
            max_bias_metric = max(example['bias'].items(), key=lambda x: abs(x[1]))
            print(f"\nTest #{example['test_number']}: {example['question'][:60]}...")
            print(f"  Largest bias: {max_bias_metric[0]} = {max_bias_metric[1]:+.3f}")
            print(f"  Gemini scores: C={example['gemini_scores']['correctness']:.2f}, "
                  f"F={example['gemini_scores']['faithfulness']:.2f}, "
                  f"R={example['gemini_scores']['relevancy']:.2f}")
            print(f"  Claude scores: C={example['claude_scores']['correctness']:.2f}, "
                  f"F={example['claude_scores']['faithfulness']:.2f}, "
                  f"R={example['claude_scores']['relevancy']:.2f}")
            print(f"  Gemini reasoning: {example['gemini_scores']['reasoning'][:100]}...")
            print(f"  Claude reasoning: {example['claude_scores']['reasoning'][:100]}...")
    else:
        print("\nNo examples with bias > 0.15 found. Good agreement between judges!")

    # Save results
    output_path = Path("evaluation_results/judge_bias_validation.json")
    output_path.parent.mkdir(exist_ok=True)

    output_data = {
        "test_date": datetime.now().isoformat(),
        "gemini_model": "gemini-2.0-flash",
        "claude_model": "claude-3-5-sonnet-20241022",
        "total_cases": len(comparisons),
        "statistics": stats,
        "verdict": verdict,
        "average_bias": round(avg_total_bias, 3),
        "recommendation": recommendation,
        "comparisons": comparisons
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 100)
    print(f"Results saved to: {output_path}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)


if __name__ == "__main__":
    main()
