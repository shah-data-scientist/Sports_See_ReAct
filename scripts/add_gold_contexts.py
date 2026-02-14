"""
FILE: add_gold_contexts.py
STATUS: Experimental
RESPONSIBILITY: Add gold context to vector test cases for RAGAS Context Precision/Recall
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu

Generates gold (reference) context for each test case based on what SHOULD be retrieved.
Gold context is derived from:
- Known Reddit posts in vector store
- Glossary definitions
- Empty for out-of-scope queries
"""

import io
import sys
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.vector_test_cases import EVALUATION_TEST_CASES

# ==============================================================================
# KNOWN CONTENT IN VECTOR STORE (from manual inspection)
# ==============================================================================

REDDIT_POSTS = {
    "playoffs_impressed": {
        "title": "Who are teams in the playoffs that have impressed you?",
        "upvotes": 31,
        "summary": "Reddit post asking which playoff teams have impressed fans. Comments discuss surprising performances.",
    },
    "two_best_teams": {
        "title": "How is it that the two best teams in the playoffs...",
        "upvotes": 457,
        "summary": "Discussion about why the two best playoff teams perform well or unexpected aspects.",
    },
    "reggie_miller": {
        "title": "Reggie Miller is the most efficient first option in NBA playoffs",
        "upvotes": 1300,
        "max_comment_upvotes": 11515,
        "summary": "High-engagement discussion about Reggie Miller's playoff efficiency with detailed statistical debates.",
    },
    "home_court": {
        "title": "Which NBA team did not have home court advantage until the NBA Finals?",
        "upvotes": 272,
        "summary": "Historical discussion about teams that reached finals without home court advantage.",
    },
}

GLOSSARY_TERMS = {
    "pick and roll": "An offensive play where a player sets a screen (pick) for the ball handler and then moves (rolls) toward the basket to receive a pass.",
    "zone defense": "A defensive strategy where players guard specific areas of the court rather than individual opponents.",
    "triple-double": "A statistical achievement where a player accumulates double-digit totals in three of five categories: points, rebounds, assists, steals, and blocks.",
    "fast break": "A quick offensive transition after gaining possession, attempting to score before the defense can set up.",
    "alley-oop": "A play where one player throws the ball near the basket and a teammate jumps to catch and score in mid-air.",
}


def generate_gold_context(test_case):
    """Generate gold (reference) context for a test case.

    Returns list of context strings that SHOULD be retrieved.
    """
    question_lower = test_case.question.lower()
    gt_lower = test_case.ground_truth.lower()

    contexts = []

    # Reddit discussion queries
    if "reddit" in gt_lower or "discussion" in gt_lower or "fans" in gt_lower:
        if "impressed" in question_lower or "playoff" in question_lower and "teams" in question_lower:
            contexts.append(f"Reddit Post: {REDDIT_POSTS['playoffs_impressed']['title']} ({REDDIT_POSTS['playoffs_impressed']['upvotes']} upvotes) - {REDDIT_POSTS['playoffs_impressed']['summary']}")

        if "two best" in question_lower or "best teams" in question_lower:
            contexts.append(f"Reddit Post: {REDDIT_POSTS['two_best_teams']['title']} ({REDDIT_POSTS['two_best_teams']['upvotes']} upvotes) - {REDDIT_POSTS['two_best_teams']['summary']}")

        if "reggie miller" in question_lower or "efficiency" in question_lower and "efficient" in question_lower:
            contexts.append(f"Reddit Post: {REDDIT_POSTS['reggie_miller']['title']} ({REDDIT_POSTS['reggie_miller']['upvotes']} upvotes, {REDDIT_POSTS['reggie_miller']['max_comment_upvotes']} max comment upvotes) - {REDDIT_POSTS['reggie_miller']['summary']}")

        if "home court" in question_lower or "home advantage" in question_lower:
            contexts.append(f"Reddit Post: {REDDIT_POSTS['home_court']['title']} ({REDDIT_POSTS['home_court']['upvotes']} upvotes) - {REDDIT_POSTS['home_court']['summary']}")

        # Generic playoff discussions
        if "playoff" in question_lower and not contexts:
            contexts.extend([
                f"Reddit Post: {REDDIT_POSTS['playoffs_impressed']['title']}",
                f"Reddit Post: {REDDIT_POSTS['reggie_miller']['title']}",
            ])

    # Glossary/terminology queries
    if "what is" in question_lower or "what does" in question_lower or "define" in question_lower:
        for term, definition in GLOSSARY_TERMS.items():
            if term in question_lower:
                contexts.append(f"Basketball Glossary: {term.title()} - {definition}")

    # Out-of-scope queries
    if "out of scope" in gt_lower or "doesn't contain" in gt_lower:
        # No relevant context should exist
        contexts = []

    # If no specific context found but Reddit is mentioned in ground truth
    if not contexts and "reddit" in gt_lower:
        # Default to general playoff discussions
        contexts = [
            f"Reddit Post: {REDDIT_POSTS['playoffs_impressed']['title']}",
            f"Reddit Post: {REDDIT_POSTS['reggie_miller']['title']}",
        ]

    return contexts


def main():
    """Generate and display gold contexts for all test cases."""
    print("\n" + "="*80)
    print("  GOLD CONTEXT GENERATION FOR VECTOR TEST CASES")
    print("="*80)
    print(f"  Total test cases: {len(EVALUATION_TEST_CASES)}")
    print("="*80 + "\n")

    test_cases_with_gold_context = []

    for i, tc in enumerate(EVALUATION_TEST_CASES, 1):
        gold_contexts = generate_gold_context(tc)

        test_cases_with_gold_context.append({
            "question": tc.question,
            "category": tc.category.value,
            "ground_truth": tc.ground_truth,
            "gold_contexts": gold_contexts,
        })

        print(f"[{i}/{len(EVALUATION_TEST_CASES)}] {tc.category.value}")
        print(f"  Q: {tc.question[:70]}...")
        print(f"  Gold Contexts: {len(gold_contexts)}")
        for j, ctx in enumerate(gold_contexts, 1):
            print(f"    {j}. {ctx[:80]}...")
        print()

    # Save to JSON
    import json
    output_file = Path("evaluation_results/vector_gold_contexts.json")
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(test_cases_with_gold_context, f, indent=2, ensure_ascii=False)

    print("="*80)
    print(f"  Gold contexts saved to: {output_file}")
    print("="*80)

    # Statistics
    with_context = sum(1 for tc in test_cases_with_gold_context if tc["gold_contexts"])
    without_context = len(test_cases_with_gold_context) - with_context

    print(f"\n  Test cases with gold context:    {with_context}/{len(test_cases_with_gold_context)}")
    print(f"  Test cases without gold context: {without_context}/{len(test_cases_with_gold_context)}")
    print(f"  (Out-of-scope queries should have no context)\n")


if __name__ == "__main__":
    main()
