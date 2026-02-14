"""A/B Test: SQL Formatting Removal Impact on Quality.

This script tests whether removing the SQL agent's formatting step
(which adds 1 LLM call per SQL query) impacts the final answer quality.

Test Setup:
- Control: Current system with SQL agent formatting
- Treatment: SQL agent returns raw results only (no formatted answer)
- Metrics: Answer quality, completeness, accuracy

Expected Result:
- If quality is maintained: Remove formatting (save 500ms + cost per SQL query)
- If quality degrades: Keep formatting

Run:
    poetry run python tests/ab_test_sql_formatting.py
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class TestQuery:
    """Test query with expected characteristics."""

    query: str
    category: str  # simple, moderate, complex
    expected_elements: list[str]  # Key elements that should appear in answer
    description: str


# Test Queries (20 total: 7 simple, 7 moderate, 6 complex)
TEST_QUERIES = [
    # === SIMPLE QUERIES (7) ===
    TestQuery(
        query="Who scored the most points this season?",
        category="simple",
        expected_elements=["Shai", "points", "2100"],
        description="Single stat query - top scorer",
    ),
    TestQuery(
        query="How many rebounds does Domantas Sabonis have?",
        category="simple",
        expected_elements=["Sabonis", "rebounds"],
        description="Single player single stat",
    ),
    TestQuery(
        query="Who leads in assists?",
        category="simple",
        expected_elements=["assist", "lead"],
        description="Top assists leader",
    ),
    TestQuery(
        query="What is LeBron James' PPG?",
        category="simple",
        expected_elements=["LeBron", "PPG", "points"],
        description="Player PPG lookup",
    ),
    TestQuery(
        query="How many three-pointers has Stephen Curry made?",
        category="simple",
        expected_elements=["Curry", "three", "3P"],
        description="Player 3P count",
    ),
    TestQuery(
        query="What team does Nikola Jokic play for?",
        category="simple",
        expected_elements=["Jokic", "Nuggets", "DEN"],
        description="Player team lookup",
    ),
    TestQuery(
        query="How many blocks does Victor Wembanyama have?",
        category="simple",
        expected_elements=["Wembanyama", "blocks"],
        description="Player blocks count",
    ),
    # === MODERATE QUERIES (7) ===
    TestQuery(
        query="Compare Nikola Jokic and Joel Embiid stats",
        category="moderate",
        expected_elements=["Jokic", "Embiid", "points", "rebounds", "assists"],
        description="Two-player comparison",
    ),
    TestQuery(
        query="Top 5 three-point shooters by percentage",
        category="moderate",
        expected_elements=["3P%", "percentage", "top", "5"],
        description="Top N with percentage filtering",
    ),
    TestQuery(
        query="Who has more assists, Luka or Trae?",
        category="moderate",
        expected_elements=["Luka", "Trae", "assists", "more"],
        description="Direct player vs player stat",
    ),
    TestQuery(
        query="Show me the top rebounders averaging over 10 RPG",
        category="moderate",
        expected_elements=["rebounds", "RPG", "10", "averag"],
        description="Top N with threshold filter",
    ),
    TestQuery(
        query="Which players have 20+ PPG and 50%+ FG?",
        category="moderate",
        expected_elements=["PPG", "20", "FG%", "50"],
        description="Multi-condition filtering",
    ),
    TestQuery(
        query="Compare Lakers and Celtics offensive stats",
        category="moderate",
        expected_elements=["Lakers", "Celtics", "offensive", "points"],
        description="Team comparison",
    ),
    TestQuery(
        query="Who are the top 3 scorers on the Warriors?",
        category="moderate",
        expected_elements=["Warriors", "scorers", "top", "3"],
        description="Top N within specific team",
    ),
    # === COMPLEX QUERIES (6) ===
    TestQuery(
        query="Show me players averaging 25+ PPG, 5+ RPG, and 5+ APG",
        category="complex",
        expected_elements=["25", "PPG", "5", "RPG", "APG"],
        description="Triple-condition filtering",
    ),
    TestQuery(
        query="Compare the efficiency of Shai, Luka, and Giannis",
        category="complex",
        expected_elements=["Shai", "Luka", "Giannis", "efficiency", "FG%"],
        description="Three-player efficiency comparison",
    ),
    TestQuery(
        query="Which team has the best defensive stats and who contributes most?",
        category="complex",
        expected_elements=["defensive", "team", "best", "contribut"],
        description="Team ranking + player breakdown",
    ),
    TestQuery(
        query="Show player stats sorted by PER with minimum 30 games played",
        category="complex",
        expected_elements=["PER", "sorted", "30", "games"],
        description="Advanced stat sorting with threshold",
    ),
    TestQuery(
        query="Compare points, assists, and efficiency for guards averaging 20+ PPG",
        category="complex",
        expected_elements=["guards", "20", "PPG", "points", "assists", "efficiency"],
        description="Position filter + multi-stat comparison",
    ),
    TestQuery(
        query="Who has the highest true shooting percentage with over 200 attempts?",
        category="complex",
        expected_elements=["true shooting", "TS%", "200", "attempts"],
        description="Advanced stat with volume threshold",
    ),
]


@dataclass
class TestResult:
    """Result of A/B test comparison."""

    query: str
    category: str
    description: str
    control_answer: str
    treatment_answer: str
    control_has_elements: dict[str, bool]
    treatment_has_elements: dict[str, bool]
    control_score: float
    treatment_score: float
    winner: str  # "control", "treatment", or "tie"


class ABTestRunner:
    """Run A/B test comparing SQL formatting vs. no formatting."""

    def __init__(self):
        """Initialize test runner."""
        self.results: list[TestResult] = []

    def run_control(self, query: str) -> dict[str, Any]:
        """Run query with SQL formatting (CONTROL).

        This simulates the current system where SQL agent:
        1. Generates SQL
        2. Executes SQL
        3. Formats results into natural language answer (extra LLM call)
        4. Returns {sql, results, answer}

        Args:
            query: Test query

        Returns:
            Dict with answer and metadata
        """
        # TODO: Implement actual call to ChatService with current settings
        # For now, return mock response
        logger.info(f"[CONTROL] Running: {query}")
        return {
            "answer": "Mock answer with SQL formatting enabled",
            "tools_used": ["query_nba_database"],
            "sql_formatted": True,
        }

    def run_treatment(self, query: str) -> dict[str, Any]:
        """Run query WITHOUT SQL formatting (TREATMENT).

        This simulates the optimized system where SQL agent:
        1. Generates SQL
        2. Executes SQL
        3. Returns {sql, results} (NO formatted answer - skip LLM call)
        4. ReAct agent synthesizes from raw results only

        Args:
            query: Test query

        Returns:
            Dict with answer and metadata
        """
        # TODO: Implement actual call to ChatService with formatting disabled
        # For now, return mock response
        logger.info(f"[TREATMENT] Running: {query}")
        return {
            "answer": "Mock answer with SQL formatting disabled",
            "tools_used": ["query_nba_database"],
            "sql_formatted": False,
        }

    def score_answer(
        self,
        answer: str,
        expected_elements: list[str],
    ) -> tuple[dict[str, bool], float]:
        """Score answer quality based on expected elements.

        Args:
            answer: Generated answer text
            expected_elements: List of key terms/phrases that should appear

        Returns:
            Tuple of (element_presence_dict, overall_score)
        """
        answer_lower = answer.lower()
        presence = {}

        for element in expected_elements:
            # Check if element or close variant appears
            element_lower = element.lower()
            present = element_lower in answer_lower
            presence[element] = present

        # Score = percentage of expected elements present
        score = sum(presence.values()) / len(expected_elements) if expected_elements else 0.0
        return presence, score

    def compare_answers(
        self,
        test_query: TestQuery,
        control_answer: str,
        treatment_answer: str,
    ) -> TestResult:
        """Compare control vs treatment answers.

        Args:
            test_query: Test query with expected elements
            control_answer: Answer from control (with formatting)
            treatment_answer: Answer from treatment (no formatting)

        Returns:
            TestResult with comparison details
        """
        # Score both answers
        control_presence, control_score = self.score_answer(
            control_answer,
            test_query.expected_elements,
        )
        treatment_presence, treatment_score = self.score_answer(
            treatment_answer,
            test_query.expected_elements,
        )

        # Determine winner
        if control_score > treatment_score:
            winner = "control"
        elif treatment_score > control_score:
            winner = "treatment"
        else:
            winner = "tie"

        return TestResult(
            query=test_query.query,
            category=test_query.category,
            description=test_query.description,
            control_answer=control_answer,
            treatment_answer=treatment_answer,
            control_has_elements=control_presence,
            treatment_has_elements=treatment_presence,
            control_score=control_score,
            treatment_score=treatment_score,
            winner=winner,
        )

    def run_test(self, test_query: TestQuery) -> TestResult:
        """Run A/B test for a single query.

        Args:
            test_query: Query to test

        Returns:
            TestResult with comparison
        """
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Testing: {test_query.query}")
        logger.info(f"Category: {test_query.category}")
        logger.info(f"Description: {test_query.description}")

        # Run control
        control_result = self.run_control(test_query.query)
        control_answer = control_result["answer"]

        # Run treatment
        treatment_result = self.run_treatment(test_query.query)
        treatment_answer = treatment_result["answer"]

        # Compare
        result = self.compare_answers(
            test_query,
            control_answer,
            treatment_answer,
        )

        logger.info(f"Control Score: {result.control_score:.1%}")
        logger.info(f"Treatment Score: {result.treatment_score:.1%}")
        logger.info(f"Winner: {result.winner.upper()}")

        self.results.append(result)
        return result

    def run_all_tests(self) -> dict[str, Any]:
        """Run all A/B tests.

        Returns:
            Summary statistics
        """
        logger.info(f"\n{'#' * 80}")
        logger.info("Starting A/B Test: SQL Formatting Removal")
        logger.info(f"Total Queries: {len(TEST_QUERIES)}")
        logger.info(f"{'#' * 80}\n")

        # Run all tests
        for test_query in TEST_QUERIES:
            self.run_test(test_query)

        # Compute summary statistics
        summary = self.compute_summary()

        # Print summary
        self.print_summary(summary)

        return summary

    def compute_summary(self) -> dict[str, Any]:
        """Compute summary statistics from test results.

        Returns:
            Summary dict with metrics
        """
        total = len(self.results)
        control_wins = sum(1 for r in self.results if r.winner == "control")
        treatment_wins = sum(1 for r in self.results if r.winner == "treatment")
        ties = sum(1 for r in self.results if r.winner == "tie")

        avg_control_score = sum(r.control_score for r in self.results) / total
        avg_treatment_score = sum(r.treatment_score for r in self.results) / total

        # Per-category breakdown
        categories = ["simple", "moderate", "complex"]
        category_stats = {}
        for category in categories:
            cat_results = [r for r in self.results if r.category == category]
            if cat_results:
                category_stats[category] = {
                    "total": len(cat_results),
                    "control_wins": sum(1 for r in cat_results if r.winner == "control"),
                    "treatment_wins": sum(1 for r in cat_results if r.winner == "treatment"),
                    "ties": sum(1 for r in cat_results if r.winner == "tie"),
                    "avg_control_score": sum(r.control_score for r in cat_results)
                    / len(cat_results),
                    "avg_treatment_score": sum(r.treatment_score for r in cat_results)
                    / len(cat_results),
                }

        return {
            "total_tests": total,
            "control_wins": control_wins,
            "treatment_wins": treatment_wins,
            "ties": ties,
            "avg_control_score": avg_control_score,
            "avg_treatment_score": avg_treatment_score,
            "score_difference": avg_treatment_score - avg_control_score,
            "category_breakdown": category_stats,
        }

    def print_summary(self, summary: dict[str, Any]):
        """Print summary statistics.

        Args:
            summary: Summary dict from compute_summary()
        """
        logger.info(f"\n{'#' * 80}")
        logger.info("A/B TEST SUMMARY")
        logger.info(f"{'#' * 80}\n")

        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Control Wins (with formatting): {summary['control_wins']}")
        logger.info(f"Treatment Wins (no formatting): {summary['treatment_wins']}")
        logger.info(f"Ties: {summary['ties']}\n")

        logger.info(f"Average Control Score: {summary['avg_control_score']:.1%}")
        logger.info(f"Average Treatment Score: {summary['avg_treatment_score']:.1%}")
        logger.info(
            f"Score Difference (Treatment - Control): {summary['score_difference']:+.1%}\n"
        )

        logger.info("CATEGORY BREAKDOWN:")
        for category, stats in summary["category_breakdown"].items():
            logger.info(f"\n  {category.upper()}:")
            logger.info(f"    Total: {stats['total']}")
            logger.info(f"    Control Wins: {stats['control_wins']}")
            logger.info(f"    Treatment Wins: {stats['treatment_wins']}")
            logger.info(f"    Ties: {stats['ties']}")
            logger.info(f"    Avg Control: {stats['avg_control_score']:.1%}")
            logger.info(f"    Avg Treatment: {stats['avg_treatment_score']:.1%}")

        logger.info(f"\n{'#' * 80}")
        logger.info("RECOMMENDATION")
        logger.info(f"{'#' * 80}\n")

        # Decision logic
        if summary["treatment_wins"] > summary["control_wins"]:
            logger.info("✅ REMOVE SQL FORMATTING")
            logger.info("   Treatment (no formatting) performs BETTER than control")
            logger.info("   Savings: ~500ms + 1 LLM call per SQL query")
        elif summary["treatment_wins"] == summary["control_wins"]:
            logger.info("✅ REMOVE SQL FORMATTING (TIE)")
            logger.info("   Treatment performs EQUALLY to control")
            logger.info("   Savings: ~500ms + 1 LLM call per SQL query")
        elif summary["score_difference"] > -0.05:  # Less than 5% degradation
            logger.info("⚠️  CONSIDER REMOVING (MINOR DEGRADATION)")
            logger.info(
                f"   Treatment is {abs(summary['score_difference']):.1%} worse, but within acceptable threshold"
            )
            logger.info("   Savings: ~500ms + 1 LLM call per SQL query")
        else:
            logger.info("❌ KEEP SQL FORMATTING")
            logger.info(
                f"   Treatment performs significantly worse ({abs(summary['score_difference']):.1%} degradation)"
            )
            logger.info("   Quality loss not worth the performance gain")

        logger.info(f"\n{'#' * 80}\n")

    def export_results(self, filepath: str = "ab_test_results.json"):
        """Export test results to JSON file.

        Args:
            filepath: Output file path
        """
        output = {
            "test_queries": [
                {
                    "query": r.query,
                    "category": r.category,
                    "description": r.description,
                    "control_score": r.control_score,
                    "treatment_score": r.treatment_score,
                    "winner": r.winner,
                }
                for r in self.results
            ],
            "summary": self.compute_summary(),
        }

        with open(filepath, "w") as f:
            json.dump(output, f, indent=2)

        logger.info(f"Results exported to {filepath}")


def main():
    """Run A/B test."""
    runner = ABTestRunner()
    summary = runner.run_all_tests()
    runner.export_results("tests/ab_test_results.json")

    # Return exit code based on recommendation
    if summary["treatment_wins"] >= summary["control_wins"]:
        return 0  # Success - can remove formatting
    elif summary["score_difference"] > -0.05:
        return 0  # Acceptable degradation
    else:
        return 1  # Significant degradation - keep formatting


if __name__ == "__main__":
    exit(main())
