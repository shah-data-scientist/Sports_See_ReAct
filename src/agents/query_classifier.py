"""
File: src/agents/query_classifier.py
Description: Query classification for NBA statistics queries
Responsibilities: Classify queries as sql_only, vector_only, or hybrid
Created: 2026-02-16
"""

import logging
import re
from typing import Callable

from google import genai

logger = logging.getLogger(__name__)

# Classification Confidence Thresholds
HEURISTIC_CONFIDENCE_THRESHOLD = 0.9  # Use heuristic if confidence >= this
CONFIDENCE_VERY_HIGH = 0.98  # Very high confidence (strong signals)
CONFIDENCE_HIGH = 0.95  # High confidence (clear indicators)
CONFIDENCE_MEDIUM_HIGH = 0.90  # Medium-high confidence
CONFIDENCE_MEDIUM = 0.85  # Medium confidence
CONFIDENCE_LOW = 0.50  # Low confidence (triggers LLM classification)

# Signal Counting Base Confidence
HYBRID_BASE_CONFIDENCE = 0.75  # Base confidence for hybrid queries
VECTOR_BASE_CONFIDENCE = 0.80  # Base confidence for vector-only queries
SQL_BASE_CONFIDENCE = 0.85  # Base confidence for SQL-only queries
VECTOR_MAX_CONFIDENCE = 0.92  # Maximum confidence for vector-only
SQL_MAX_CONFIDENCE = 0.95  # Maximum confidence for SQL-only

# Confidence Adjustment Factors
CONFIDENCE_BOOST_PER_HYBRID_SIGNAL = 0.05  # +5% per matching signal
CONFIDENCE_BOOST_PER_VECTOR_SIGNAL = 0.03  # +3% per vector-only signal
CONFIDENCE_BOOST_PER_SQL_SIGNAL = 0.02  # +2% per SQL-only signal


class QueryClassifier:
    """Classifier for NBA statistics queries using hybrid approach.

    Uses heuristic pattern matching with confidence scoring, falling back
    to LLM classification when confidence is low.

    Attributes:
        client: Gemini client for LLM classification
        model: Model name for LLM classification
    """

    def __init__(
        self,
        client: genai.Client,
        model: str = "gemini-2.0-flash",
    ):
        """Initialize query classifier.

        Args:
            client: Gemini client for LLM classification
            model: Model name for LLM classification
        """
        self.client = client
        self._model = model

    def classify(self, question: str) -> str:
        """Classify query using hybrid approach: heuristic + LLM fallback.

        Strategy:
        1. Try heuristic classification with confidence scoring
        2. If confidence >= 0.9, use heuristic result (fast, 70% of queries)
        3. If confidence < 0.9, use LLM classification (accurate, 30% of queries)
        4. LLM uses prompt caching to reduce token costs

        Args:
            question: User question

        Returns:
            "sql_only", "vector_only", or "hybrid"
        """
        # Try heuristic classification first
        confidence, query_type = self._heuristic_classify_with_confidence(question)

        # If high confidence, use heuristic result
        if confidence >= HEURISTIC_CONFIDENCE_THRESHOLD:
            logger.debug(f"Heuristic classification (confidence={confidence:.2f}): {query_type}")
            return query_type

        # Low confidence - use LLM for accurate classification
        logger.info(f"Heuristic uncertain (confidence={confidence:.2f}), using LLM classification")
        return self._llm_classify(question)

    def _heuristic_classify_with_confidence(self, question: str) -> tuple[float, str]:
        """Heuristic classification with confidence scoring.

        Args:
            question: User question

        Returns:
            Tuple of (confidence score 0-1, query_type)
        """
        q_lower = question.lower()

        # COMPREHENSIVE SQL PATTERNS: Anticipate all common statistical query variations
        # Organized by category for maintainability

        # Category 1: Player stat queries
        player_stat_patterns = [
            # "How many X did/does/has player"
            r"how many (points|assists|rebounds|steals|blocks|turnovers|fouls|three-pointers|threes|games|minutes) (did|does|has|have|had)",
            # "What is/What's player's stat"
            r"(what is|what's|whats) \w+('s|s)? (points|assists|rebounds|steals|blocks|average|total|stats|ppg|apg|rpg|shooting|percentage)",
            # "How much did player score/average"
            r"how (much|many) (did|does|has) \w+ (score|average|record|get|have|tally)",
        ]

        # Category 2: Team queries
        team_queries_patterns = [
            r"how many players (on|in) (the )?\w+ (roster|team|squad)",
            r"list( all)? players (on|in|from) (the )?\w+",
            r"(what|which) players (are|were) on (the )?\w+",
            r"(what is|what's|whats) (the )?\w+ (roster|lineup|squad)",
        ]

        # Category 3: Ranking/Top N queries
        ranking_patterns = [
            r"(who|which player) (has|scored|recorded|got) (the )?(most|highest|top|best)",
            r"(top|best|highest|leading) \d* (scorers?|rebounders?|players?|performers?|shooters?)",
            r"(who|which) (is|are|was|were) (the )?(best|top|leading|highest)",
        ]

        # Category 4: Comparison queries (SQL-only if no "why/how")
        comparison_patterns = [
            r"compare \w+('s)? (and|vs|versus) \w+('s)? (stats|numbers|performance|season)",
            r"(who|which) (is|was) better[:,]? \w+ (or|vs|versus) \w+",
        ]

        # Category 5: Count/Aggregate queries
        count_patterns = [
            r"how many (teams|players|games|seasons|championships)",
            r"(count|total number of) (players|teams|games)",
        ]

        # Check all SQL patterns
        all_sql_patterns = (
            player_stat_patterns
            + team_queries_patterns
            + ranking_patterns
            + comparison_patterns
            + count_patterns
        )

        for pattern in all_sql_patterns:
            if re.search(pattern, q_lower):
                logger.debug(f"Matched SQL pattern: {pattern}")
                return (CONFIDENCE_VERY_HIGH, "sql_only")

        # COMPREHENSIVE VECTOR-ONLY PATTERNS: Anticipate all opinion/discussion variations
        # Strong vector-only signals (override other signals)

        # Category 1: Fan opinions/thoughts
        fan_opinion_signals = [
            "what do fans", "what are fans", "do fans", "are fans",
            "fans think", "fans believe", "fans feel", "fans say",
            "fan reactions", "fan sentiment", "fan opinion", "fan perspective",
        ]

        # Category 2: Discussion/debate queries
        discussion_signals = [
            "according to discussions", "according to discussion", "in discussions",
            "debate about", "debated", "controversial", "argued",
            "most discussed", "most talked about", "most debated",
            "discussion topic", "debate topic", "talked about topic",
            "popular discussion", "common debate", "hot topic",
        ]

        # Category 3: Reddit/social media specific
        social_media_signals = [
            "what do reddit", "what are reddit", "redditors think", "redditors say",
            "on reddit", "reddit users", "r/nba", "social media",
            "what do people think", "what are people", "people believe",
            "what do users think", "what are users",
        ]

        # Category 4: Opinion/belief queries
        opinion_signals = [
            "popular opinion", "common belief", "general consensus",
            "considered to be", "regarded as", "seen as", "viewed as",
            "perception of", "reputation of", "opinion about",
        ]

        # Category 5: User-specific queries
        user_specific_signals = [
            "what did u/", "u/ posted", "user posted", "redditor said",
        ]

        # Combine all strong vector signals
        strong_vector_signals = (
            fan_opinion_signals
            + discussion_signals
            + social_media_signals
            + opinion_signals
            + user_specific_signals
        )

        # Vector-only signals (why/how/opinion questions)
        vector_signals = [
            "why", "how", "what do", "what are", "debate", "think",
            "opinion", "believe", "consider", "argue", "discuss",
            "fan", "reddit", "style", "strategy", "approach",
            "makes them", "makes him", "makes her", "playing style"
        ]

        # SQL-only signals (statistical queries)
        sql_signals = [
            "top", "most", "highest", "lowest", "average", "total",
            "rank", "leader", "best", "worst", "compare", "vs",
            "scored", "points", "rebounds", "assists", "steals",
            "blocks", "percentage", "stats", "statistics"
        ]

        # COMPREHENSIVE HYBRID PATTERNS: Queries needing both stats AND context
        # These require SQL data + vector search for complete answers

        # Category 1: Biographical queries
        biographical_signals = [
            "who is", "who was", "tell me about", "what about",
            "introduce me to", "describe", "profile of",
        ]

        # Category 2: Impact/value analysis (needs stats + context)
        impact_analysis_signals = [
            "what impact", "how valuable", "value of", "importance of",
            "contribution of", "role of", "significance of",
        ]

        # Category 3: Stats + explanation queries
        stats_plus_context = [
            "and why", "and how", "and what makes", "and explain",
            "stats and", "numbers and", "performance and",
        ]

        # Combine hybrid signals
        hybrid_signals = (
            biographical_signals
            + impact_analysis_signals
            + stats_plus_context
        )

        # Check strong vector signals first (highest priority - very confident)
        if any(signal in q_lower for signal in strong_vector_signals):
            return (CONFIDENCE_HIGH, "vector_only")

        # Check hybrid (biographical queries - very confident)
        if any(signal in q_lower for signal in hybrid_signals):
            return (CONFIDENCE_HIGH, "hybrid")

        # Count signals for each type
        vector_count = sum(1 for signal in vector_signals if signal in q_lower)
        sql_count = sum(1 for signal in sql_signals if signal in q_lower)

        # If strong vector signal (why/how/think) present, prioritize vector
        # even if SQL signals are also present
        has_strong_opinion = any(word in q_lower for word in ["why", "how", "think", "believe", "opinion"])
        if has_strong_opinion and vector_count > 0:
            # If also asking for stats (e.g., "why did he score so many points?"), it's hybrid
            if any(word in q_lower for word in ["scored", "points", "stats", "average"]):
                return (CONFIDENCE_MEDIUM, "hybrid")
            return (CONFIDENCE_MEDIUM_HIGH, "vector_only")

        # If both have signals, it's hybrid (but lower confidence)
        if vector_count > 0 and sql_count > 0:
            confidence = HYBRID_BASE_CONFIDENCE + (min(vector_count, sql_count) * CONFIDENCE_BOOST_PER_HYBRID_SIGNAL)
            return (min(confidence, CONFIDENCE_MEDIUM_HIGH), "hybrid")

        # If only vector signals
        if vector_count > 0:
            confidence = VECTOR_BASE_CONFIDENCE + (vector_count * CONFIDENCE_BOOST_PER_VECTOR_SIGNAL)
            return (min(confidence, VECTOR_MAX_CONFIDENCE), "vector_only")

        # If only SQL signals
        if sql_count > 0:
            confidence = SQL_BASE_CONFIDENCE + (sql_count * CONFIDENCE_BOOST_PER_SQL_SIGNAL)
            return (min(confidence, SQL_MAX_CONFIDENCE), "sql_only")

        # Ambiguous query (no clear signals) - low confidence, default to SQL
        return (CONFIDENCE_LOW, "sql_only")

    def _llm_classify(self, question: str) -> str:
        """Classify query using LLM with prompt caching.

        Uses cached system prompt to save tokens on repeated calls.

        Args:
            question: User question

        Returns:
            "sql_only", "vector_only", or "hybrid"
        """
        # Classification prompt with caching
        system_prompt = """You are an NBA query classifier. Classify queries into exactly ONE type:

**sql_only**: Statistical queries (numbers, stats, rankings, comparisons)
- Examples: "Top 5 scorers", "Shai's PPG", "Compare Jokic vs Embiid stats"

**vector_only**: Contextual queries (opinions, discussions, explanations, styles)
- Examples: "Why is LeBron the GOAT?", "What do fans think about the Lakers?", "Explain Curry's playing style"

**hybrid**: Biographical or queries needing BOTH stats AND context
- Examples: "Who is Nikola Jokic?", "Tell me about Luka Doncic", "What makes Giannis valuable?"

Output ONLY the classification: sql_only, vector_only, or hybrid"""

        user_prompt = f"Classify this NBA query:\n\n{question}\n\nClassification:"

        try:
            response = self.client.models.generate_content(
                model=self._model,
                contents=user_prompt,
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.0,  # Deterministic classification
                    "cached_content": None,  # TODO: Add prompt caching
                },
            )

            classification = response.text.strip().lower()

            # Validate classification
            if classification in ["sql_only", "vector_only", "hybrid"]:
                logger.debug(f"LLM classification: {classification}")
                return classification

            # Invalid response - log and default to sql_only
            logger.warning(f"Invalid LLM classification '{classification}', defaulting to sql_only")
            return "sql_only"

        except Exception as e:
            logger.error(f"LLM classification failed: {e}", exc_info=True)
            return "sql_only"  # Safe default
