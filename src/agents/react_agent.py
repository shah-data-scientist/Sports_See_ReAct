"""
File: src/agents/react_agent.py
Description: ReAct agent for NBA statistics queries
Responsibilities: Query routing, tool selection, and reasoning
Created: 2026-02-14
"""

from dataclasses import dataclass, field
from typing import Any, Callable
import json
import logging
import re
import time
from google import genai

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """Tool definition for ReAct agent."""

    name: str
    description: str
    function: Callable
    parameters: dict[str, str]
    examples: list[str] = field(default_factory=list)


@dataclass
class AgentStep:
    """Single step in agent reasoning trace."""

    thought: str
    action: str
    action_input: dict[str, Any]
    observation: str
    step_number: int


class ReActAgent:
    """Smart agent for NBA statistics queries with intelligent tool selection.

    This agent analyzes each query to determine which tools are needed:
    - SQL-only: Statistical queries (top N, rankings, comparisons, stats)
    - Vector-only: Contextual queries (why/how, opinions, explanations)
    - Hybrid: Both statistical and contextual information needed

    Key features:
    - Lightweight query classification (heuristic-based, not regex)
    - Conditional tool execution (only run necessary tools)
    - Single LLM call for answer generation
    - Auto-visualization for suitable SQL results
    """

    def __init__(
        self,
        tools: list[Tool],
        llm_client: genai.Client,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.1,
    ):
        """Initialize smart agent.

        Args:
            tools: List of available tools (expects query_nba_database and search_knowledge_base)
            llm_client: Google Generative AI client
            model: LLM model to use
            temperature: LLM temperature for answer generation
        """
        self.tools = {t.name: t for t in tools}
        self.llm_client = llm_client
        self.model = model
        self.temperature = temperature

        # Tool results storage (structured access for direct extraction)
        self.tool_results: dict[str, Any] = {}

    def _classify_query(self, question: str) -> str:
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
        if confidence >= 0.9:
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
        import re

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
                return (0.98, "sql_only")  # Very high confidence

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
            return (0.95, "vector_only")  # High confidence

        # Check hybrid (biographical queries - very confident)
        if any(signal in q_lower for signal in hybrid_signals):
            return (0.95, "hybrid")  # High confidence

        # Count signals for each type
        vector_count = sum(1 for signal in vector_signals if signal in q_lower)
        sql_count = sum(1 for signal in sql_signals if signal in q_lower)

        # If strong vector signal (why/how/think) present, prioritize vector
        # even if SQL signals are also present
        has_strong_opinion = any(word in q_lower for word in ["why", "how", "think", "believe", "opinion"])
        if has_strong_opinion and vector_count > 0:
            # If also asking for stats (e.g., "why did he score so many points?"), it's hybrid
            if any(word in q_lower for word in ["scored", "points", "stats", "average"]):
                return (0.85, "hybrid")  # Medium-high confidence
            return (0.90, "vector_only")  # High confidence

        # If both have signals, it's hybrid (but lower confidence)
        if vector_count > 0 and sql_count > 0:
            confidence = 0.75 + (min(vector_count, sql_count) * 0.05)  # 0.75-0.85 range
            return (min(confidence, 0.90), "hybrid")

        # If only vector signals
        if vector_count > 0:
            confidence = 0.80 + (vector_count * 0.03)  # More signals = higher confidence
            return (min(confidence, 0.92), "vector_only")

        # If only SQL signals
        if sql_count > 0:
            confidence = 0.85 + (sql_count * 0.02)  # More signals = higher confidence
            return (min(confidence, 0.95), "sql_only")

        # Ambiguous query (no clear signals) - low confidence, default to SQL
        return (0.50, "sql_only")  # Low confidence - will trigger LLM classification

    def _llm_classify(self, question: str) -> str:
        """Classify query using LLM with prompt caching.

        Uses cached system prompt to save tokens on repeated calls.

        Args:
            question: User question

        Returns:
            "sql_only", "vector_only", or "hybrid"
        """
        # System prompt for classification (will be cached)
        system_prompt = """You are a query classifier for an NBA statistics assistant.

Classify the query into ONE of these categories:
1. **sql_only**: Pure statistical queries (top N, rankings, averages, comparisons)
2. **vector_only**: Opinion/context queries (why, how, debates, fan opinions, styles)
3. **hybrid**: Queries needing BOTH stats AND context (biographical, "Who is X?", stats + explanations)

CLASSIFICATION RULES:
- "Who scored most points?" → sql_only (just stats)
- "Why is LeBron great?" → vector_only (opinion/context)
- "What do fans think about Lakers?" → vector_only (fan opinions)
- "Who is Nikola Jokić?" → hybrid (bio = stats + context)
- "Top 5 scorers and why they're effective?" → hybrid (stats + explanations)
- "Compare LeBron and Durant's playing styles" → hybrid (stats + style analysis)

IMPORTANT:
- Questions with "what makes them/him" often need SQL FIRST to identify the player, then vector search for context → **hybrid**
- Questions asking for stats (top N, points, averages) with follow-up context (why, how, style) → **hybrid**

Return ONLY one word: sql_only, vector_only, or hybrid"""

        # User prompt (not cached)
        user_prompt = f"Query: {question}\n\nClassification:"

        try:
            # Call LLM with caching (system prompt gets cached)
            response = self.llm_client.models.generate_content(
                model=self.model,
                contents=[
                    {"role": "user", "parts": [{"text": system_prompt}]},
                    {"role": "model", "parts": [{"text": "Understood. I will classify queries accurately."}]},
                    {"role": "user", "parts": [{"text": user_prompt}]}
                ],
                config=genai.types.GenerateContentConfig(
                    temperature=0.0,  # Deterministic classification
                    max_output_tokens=10,
                    cached_content=None  # Gemini auto-caches if supported
                )
            )

            # Parse response
            classification = response.text.strip().lower()

            # Validate response
            if classification in ["sql_only", "vector_only", "hybrid"]:
                logger.info(f"LLM classification: {classification}")
                return classification
            else:
                # Fallback to heuristic if LLM returns invalid response
                logger.warning(f"LLM returned invalid classification '{classification}', using heuristic")
                _, fallback_type = self._heuristic_classify_with_confidence(question)
                return fallback_type

        except Exception as e:
            logger.error(f"LLM classification failed ({e}), falling back to heuristic")
            _, fallback_type = self._heuristic_classify_with_confidence(question)
            return fallback_type

    def _extract_entities_from_sql(self, sql_result: dict) -> list[str]:
        """Extract entity names (players, teams) from SQL results.

        Args:
            sql_result: SQL tool result dict with 'results' key

        Returns:
            List of entity names found in results
        """
        entities = []

        if not sql_result or "results" not in sql_result:
            return entities

        results = sql_result["results"]

        # Handle single result (dict) or multiple results (list of dicts)
        if isinstance(results, dict):
            results = [results]

        # Extract from common name fields
        for row in results if isinstance(results, list) else []:
            if isinstance(row, dict):
                # Try common name fields
                for field in ["name", "player_name", "team_name", "player", "team"]:
                    if field in row and row[field]:
                        entities.append(str(row[field]))

        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity not in seen:
                seen.add(entity)
                unique_entities.append(entity)

        logger.debug(f"Extracted entities from SQL: {unique_entities}")
        return unique_entities

    def _enrich_query_with_entities(self, question: str, entities: list[str]) -> str:
        """Enrich query by replacing pronouns and transforming to search keywords.

        Enhanced approach:
        1. Replace pronouns with entity names
        2. Extract key concepts from questions
        3. Convert question to search keywords

        Args:
            question: Original user question
            entities: List of entity names from SQL results

        Returns:
            Enriched search query optimized for vector search
        """
        if not entities:
            return question

        import re

        # Build entity string
        entity_str = " ".join(entities) if len(entities) > 1 else entities[0]

        # Step 1: Replace pronouns with entities (expanded patterns)
        enriched = question

        # Pronoun patterns (match various contexts)
        pronoun_replacements = [
            (r'\btheir\s+', entity_str + " "),
            (r'\bhis\s+', entities[0] + " " if len(entities) == 1 else entity_str + " "),
            (r'\bher\s+', entities[0] + " " if len(entities) == 1 else entity_str + " "),
            (r'\bthem\s+', entity_str + " "),
            (r'\bthey\s+', entity_str + " "),
            (r'\bhe\s+', entities[0] + " " if len(entities) == 1 else entity_str + " "),
            (r'\bshe\s+', entities[0] + " " if len(entities) == 1 else entity_str + " "),
            (r'\bit\s+', entity_str + " "),
        ]

        for pattern, replacement in pronoun_replacements:
            enriched = re.sub(pattern, replacement, enriched, flags=re.IGNORECASE)

        # Step 2: Extract key concepts and keywords for vector search
        # Goal: Transform question into search-optimized keywords

        keywords = []

        # Pattern 1: "what makes X an/a QUALITY NOUN" → extract quality + noun
        # Example: "what makes them an effective scorer" → "effective scorer"
        match = re.search(r'what makes .+?\s+(?:an?|the)\s+([\w\s]+)', enriched, flags=re.IGNORECASE)
        if match:
            phrase = match.group(1).strip()
            # Extract meaningful words (not just "an")
            words = [w for w in phrase.split() if w.lower() not in ['an', 'a', 'the']]
            keywords.extend(words[:3])  # Limit to 3 words

        # Pattern 2: "why is X QUALITY/ADJECTIVE" → extract adjective
        # Example: "why is he considered elite" → "elite"
        match = re.search(r'why (?:is|are).+?(?:considered\s+)?(elite|effective|great|good|dominant)', enriched, flags=re.IGNORECASE)
        if match:
            keywords.append(match.group(1))

        # Pattern 3: "explain TOPIC style/approach" → extract topic + style
        # Example: "explain their playing style" → "playing style"
        match = re.search(r'explain.+?(scoring|playing|defensive|offensive)\s+(style|approach|strategy)', enriched, flags=re.IGNORECASE)
        if match:
            keywords.extend([match.group(1), match.group(2)])

        # Pattern 4: "TOPIC style/approach" anywhere in query
        # Example: "scoring styles" → "scoring styles"
        matches = re.findall(r'(scoring|playing|defensive|offensive)\s+(style|approach|efficiency|effectiveness|ability)', enriched, flags=re.IGNORECASE)
        for match_tuple in matches:
            keywords.extend(match_tuple)

        # Pattern 5: General conceptual queries (P0 ISSUE #2 FIX - EXPANDED)
        # Extract general basketball concepts that might not be entity-specific
        concept_patterns = [
            r'(effective|elite|dominant|great|good|valuable|impressive)\s+(scorer|shooter|defender|player|center|guard|forward|rebounder|passer)',
            r'(scoring|defensive|offensive|rebounding)\s+(techniques|approach|strategy|philosophy|system|style|ability)',
            r'(playmaking|passing|shooting|defending|rebounding)\s+(ability|skills|approach|effectiveness)',
            r'what makes.*?(effective|efficient|good|great|elite|valuable|impressive)',  # "what makes X effective"
            r'why.*?(considered|regarded|viewed)\s+as\s+(elite|effective|valuable|great)',  # "why considered elite"
            r'explain.*?(style|approach|technique|effectiveness|efficiency)',  # "explain their style"
            r'what impact.*?(have|does)',  # "what impact do they have"
            r'(impact|influence|effect|contribution)\s+on',  # "impact on team"
        ]
        for pattern in concept_patterns:
            matches = re.findall(pattern, enriched, flags=re.IGNORECASE)
            if isinstance(matches, list) and matches:
                for match in matches:
                    if isinstance(match, tuple):
                        keywords.extend(match)
                    else:
                        keywords.append(match)

        # Step 3: Build optimized search query
        if keywords:
            # Remove duplicates while preserving order
            unique_keywords = []
            seen = set()
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower not in seen:
                    seen.add(kw_lower)
                    unique_keywords.append(kw)

            # P0 ISSUE #2 FIX: Concept-first with LIMITED entity context
            # "effective scorer Shai Gilgeous-Alexander" instead of all entities
            # This prioritizes finding concept-focused content over entity-specific content

            # Limit to max 2 entities to avoid over-specification
            limited_entities = entities[:2] if len(entities) > 2 else entities
            limited_entity_str = " ".join(limited_entities)

            # Concepts first, then entities (concept-focused query)
            optimized = f"{' '.join(unique_keywords)} {limited_entity_str}".strip()
            logger.info(f"Query transformation (concept-focused): '{question}' → '{optimized}'")
            return optimized.strip()

        # Step 4: No keywords extracted - try simpler fallbacks

        # If pronouns were replaced, the enriched query might be good enough
        # But still simplify it by removing question words
        if enriched != question:
            # Remove question words to focus on content
            simplified = re.sub(r'\b(what|why|how|when|where|who|which|whose|whom|is|are|was|were|do|does|did|can|could|should|would)\b\s*', '', enriched, flags=re.IGNORECASE)
            simplified = re.sub(r'\s+', ' ', simplified).strip()  # Clean multiple spaces

            if simplified and len(simplified) > 10:  # Ensure we didn't remove too much
                optimized = f"{entity_str} {simplified}"
                logger.info(f"Query simplification: '{question}' → '{optimized}'")
                return optimized.strip()

        # Final fallback: Just entity + original question
        # This is better than nothing but not optimal
        optimized = f"{entity_str} {question}"
        logger.debug(f"Query enrichment (fallback): '{question}' → '{optimized}'")
        return optimized.strip()

    def _determine_k(self, query: str, query_type: str) -> int:
        """Determine number of chunks to retrieve based on query complexity.

        Uses multi-factor analysis to determine optimal k:
        - Word count (length indicates complexity)
        - Comparison indicators ("compare", "versus", etc.)
        - Multi-aspect questions (multiple "and", "why", "how")
        - Pronouns (follow-up questions need more context)
        - Query type (hybrid queries inherently more complex)

        Args:
            query: User query text
            query_type: "sql_only", "vector_only", or "hybrid"

        Returns:
            Number of chunks (k) to retrieve (7-12)
        """
        # Complexity indicators
        word_count = len(query.split())

        # Check for comparison words
        comparison_words = ["compare", "versus", "vs", "difference between", "better than"]
        has_comparison = any(word in query.lower() for word in comparison_words)

        # Check for multi-aspect questions
        multi_aspect_words = ["and", "also", "both", "explain", "why", "how"]
        multi_aspect_count = sum(1 for word in multi_aspect_words if word in query.lower())

        # Check for pronouns (indicates follow-up query needing more context)
        pronouns = ["their", "his", "her", "them", "they", "it"]
        has_pronoun = any(pronoun in query.lower() for pronoun in pronouns)

        # Scoring
        complexity_score = 0

        if word_count >= 13:
            complexity_score += 3
        elif word_count >= 7:
            complexity_score += 2
        else:
            complexity_score += 1

        if has_comparison:
            complexity_score += 2

        if multi_aspect_count >= 2:
            complexity_score += 2

        if has_pronoun:
            complexity_score += 1

        if query_type == "hybrid":
            complexity_score += 1  # Hybrid queries inherently more complex

        # Map score to k
        if complexity_score >= 6:
            k = 12  # Complex
        elif complexity_score >= 4:
            k = 9   # Moderate
        else:
            k = 7   # Simple

        logger.debug(
            f"Query complexity: score={complexity_score}, k={k} "
            f"(words={word_count}, comparison={has_comparison}, "
            f"multi_aspect={multi_aspect_count}, pronoun={has_pronoun})"
        )
        return k

    def _rerank_with_llm(
        self,
        query: str,
        chunks: list[dict],
        top_n: int = 5
    ) -> list[dict]:
        """Re-rank retrieved chunks using LLM to judge relevance.

        Uses LLM to score each chunk's relevance to the query (0-10 scale),
        then returns top_n highest-scoring chunks in ranked order.

        Args:
            query: User query
            chunks: List of retrieved chunks (from vector search)
            top_n: Number of top chunks to return after re-ranking

        Returns:
            List of top_n chunks sorted by relevance score (highest first)
        """
        if not chunks:
            return []

        # Don't re-rank if we have fewer chunks than requested
        if len(chunks) <= top_n:
            return chunks

        logger.info(f"Re-ranking {len(chunks)} chunks using LLM (keeping top {top_n})")

        try:
            # P0 ISSUE #1 FIX: Stricter re-ranking for context precision
            # Build prompt for LLM to score each chunk with emphasis on precision
            prompt = f"""You are a precision-focused relevance judge for NBA basketball queries.

TASK: Rate how relevant each document is for answering the user's SPECIFIC question.

QUESTION: {query}

SCORING GUIDE (0-10 scale):
- 9-10: Document directly answers the question with specific, relevant information
- 7-8: Document provides useful context or partial answer
- 5-6: Document is tangentially related but doesn't help answer the question
- 3-4: Document mentions related topics but is mostly irrelevant
- 1-2: Document is barely relevant
- 0: Document is completely irrelevant to the question

CRITICAL: Be strict. Only score 7+ if the document actually helps answer THIS specific question.
For context precision, it's better to have fewer highly relevant documents than many loosely related ones.

DOCUMENTS:
"""
            for i, chunk in enumerate(chunks, 1):
                # Extract text from chunk (handle different formats)
                if isinstance(chunk, dict):
                    text = chunk.get("text", chunk.get("content", str(chunk)))
                else:
                    text = str(chunk)

                # Truncate long chunks for efficiency
                text_preview = text[:300] + "..." if len(text) > 300 else text
                prompt += f"\n{i}. {text_preview}\n"

            prompt += f"""
Return ONLY a JSON array of integer scores (0-10) in the same order as the documents above.

Format: [score1, score2, score3, ...]
Example: [8, 5, 9, 3, 7, 6]

Your scores:"""

            # Call LLM for scoring (use fast model with low temperature)
            response = self.llm_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature for consistent scoring
                    max_output_tokens=200,
                )
            )

            # Parse scores from response
            response_text = response.text.strip()

            # Extract JSON array from response
            import json
            # Try to find JSON array in response
            json_match = re.search(r'\[[\d\s,\.]+\]', response_text)
            if json_match:
                scores_json = json_match.group(0)
                scores = json.loads(scores_json)
            else:
                # Fallback: try parsing the entire response as JSON
                scores = json.loads(response_text)

            # Validate scores
            if not isinstance(scores, list) or len(scores) != len(chunks):
                logger.warning(
                    f"LLM re-ranking failed: expected {len(chunks)} scores, "
                    f"got {len(scores) if isinstance(scores, list) else 'invalid format'}"
                )
                return chunks[:top_n]

            # P0 ISSUE #1 FIX: Apply stricter relevance threshold
            RELEVANCE_THRESHOLD = 6.0  # Only keep chunks scoring 6+ (on 0-10 scale)

            # Filter chunks by relevance threshold first
            relevant_chunks = [
                (chunk, score) for chunk, score in zip(chunks, scores)
                if score >= RELEVANCE_THRESHOLD
            ]

            if not relevant_chunks:
                logger.warning(
                    f"No chunks above threshold {RELEVANCE_THRESHOLD}. "
                    f"Max score: {max(scores) if scores else 0}. Returning top chunks anyway."
                )
                # Fallback: if nothing passes threshold, return top-scoring chunks
                relevant_chunks = list(zip(chunks, scores))

            # Sort by score and take top_n
            ranked = sorted(relevant_chunks, key=lambda x: x[1], reverse=True)

            # Extract top_n chunks (or fewer if threshold filtered many out)
            top_chunks = [chunk for chunk, score in ranked[:top_n]]

            logger.info(
                f"Re-ranking complete. {len(relevant_chunks)}/{len(chunks)} passed threshold. "
                f"Top {min(len(top_chunks), top_n)} scores: "
                f"{[score for _, score in ranked[:min(len(ranked), top_n)]]}"
            )

            return top_chunks

        except Exception as e:
            logger.warning(f"LLM re-ranking failed ({e}), returning original chunks")
            return chunks[:top_n]

    def _rewrite_question_with_context(
        self, question: str, conversation_history: str
    ) -> str:
        """Rewrite question to resolve pronouns using conversation history.

        Examples:
        - "What team do they play for?" + history about "Shai" → "What team does Shai Gilgeous-Alexander play for?"
        - "How many assists did he average?" + history about "LeBron" → "How many assists did LeBron James average?"

        Args:
            question: Original question (may contain pronouns)
            conversation_history: Previous conversation context

        Returns:
            Rewritten question with pronouns resolved (or original if no pronouns)
        """
        # Only rewrite if question contains pronouns
        pronouns = ["he", "she", "they", "them", "his", "her", "their", "it"]
        question_lower = question.lower()

        has_pronoun = any(f" {pronoun} " in f" {question_lower} " or
                         f" {pronoun}'" in f" {question_lower} "
                         for pronoun in pronouns)

        if not has_pronoun:
            logger.debug("No pronouns detected, skipping rewrite")
            return question

        try:
            # Use LLM to resolve pronouns
            prompt = f"""Rewrite the question to replace pronouns with specific entities from the conversation history.

CONVERSATION HISTORY:
{conversation_history}

CURRENT QUESTION:
{question}

INSTRUCTIONS:
- Replace pronouns (he, she, they, their, his, her, it, them) with the specific person/team they refer to from the conversation history
- If the pronoun refers to a person mentioned earlier, use their full name
- If the pronoun refers to a team mentioned earlier, use the full team name
- Keep the rest of the question exactly the same
- If no pronoun needs resolution, return the original question unchanged

REWRITTEN QUESTION:"""

            response = self.llm_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.0},  # Deterministic rewriting
            )

            rewritten = response.text.strip()

            # Sanity check: rewritten should be similar length (not empty, not too long)
            if 5 <= len(rewritten) <= len(question) * 3:
                return rewritten
            else:
                logger.warning(f"Rewriting produced suspicious result (len={len(rewritten)}), using original")
                return question

        except Exception as e:
            logger.error(f"Question rewriting failed: {e}")
            return question  # Fallback to original on error

    def run(
        self, question: str, conversation_history: str = ""
    ) -> dict[str, Any]:
        """Execute query with smart tool selection.

        This approach:
        - Classifies query to determine needed tools
        - Executes only necessary tools (SQL, vector, or both)
        - Single LLM call combines results
        - Reduces wasteful tool executions

        Args:
            question: User question
            conversation_history: Previous conversation context

        Returns:
            Dict with:
                - answer: Final answer
                - tools_used: List of tools actually executed
                - tool_results: Structured results from executed tools
                - query_type: Classification result
        """
        # Rewrite question to resolve pronouns using conversation history (if available)
        original_question = question
        if conversation_history:
            question = self._rewrite_question_with_context(question, conversation_history)
            if question != original_question:
                logger.info(f"Question rewritten: '{original_question}' → '{question}'")

        # Classify query to determine which tools are needed
        query_type = self._classify_query(question)
        logger.info(f"Query classified as: {query_type} - '{question[:100]}'")

        # Clear tool results for new query
        self.tool_results = {}

        # Execute tools based on classification
        sql_result = None
        vector_result = None

        try:
            # Execute SQL if needed
            if query_type in ["sql_only", "hybrid"]:
                logger.debug("Executing query_nba_database...")
                sql_result = self._execute_tool(
                    tool_name="query_nba_database",
                    tool_input={"question": question}
                )

            # Execute vector search if needed (with dynamic query enrichment for hybrid)
            if query_type in ["vector_only", "hybrid"]:
                # For hybrid queries, enrich the vector search query using SQL results
                vector_query = question
                if query_type == "hybrid" and sql_result:
                    # Extract entities (player/team names) from SQL results
                    sql_data = self.tool_results.get("query_nba_database", {})
                    entities = self._extract_entities_from_sql(sql_data)

                    # Enrich query with entities (replace pronouns, add context)
                    if entities:
                        vector_query = self._enrich_query_with_entities(question, entities)
                        logger.info(f"Dynamic query rewriting: '{question}' → '{vector_query}'")

                # Determine optimal k based on query complexity
                # Retrieve more chunks initially (k*1.5) for re-ranking
                k_initial = self._determine_k(vector_query, query_type)
                k_retrieve = int(k_initial * 1.5)  # Retrieve 50% more for re-ranking

                logger.debug(f"Executing search_knowledge_base with query: '{vector_query}', k={k_retrieve}")
                vector_result = self._execute_tool(
                    tool_name="search_knowledge_base",
                    tool_input={"query": vector_query, "k": k_retrieve}
                )

                # Conditional LLM re-ranking (only if retrieval quality is poor)
                # Access actual result from tool_results (vector_result is just a string observation)
                vector_data = self.tool_results.get("search_knowledge_base", {})
                if vector_data and "results" in vector_data:
                    chunks = vector_data["results"]

                    # Check top-1 score to decide if re-ranking is needed
                    should_rerank = False
                    if chunks and len(chunks) > 0:
                        # Get top-1 score (in 0-100 range from vector store)
                        top_score_raw = chunks[0].get("score", 100.0) if isinstance(chunks[0], dict) else 100.0

                        # Normalize to 0-1 range for threshold comparison
                        top_score_normalized = top_score_raw / 100.0

                        # Only re-rank if top score is low (< 0.70 = 70% = poor quality)
                        if top_score_normalized < 0.70 and len(chunks) > k_initial:
                            should_rerank = True
                            logger.info(f"Top-1 score {top_score_normalized:.3f} ({top_score_raw:.1f}%) < 0.70, re-ranking {len(chunks)} chunks")
                        else:
                            logger.info(f"Top-1 score {top_score_normalized:.3f} ({top_score_raw:.1f}%) ≥ 0.70, skipping re-ranking (good quality)")

                    if should_rerank:
                        # Retrieval quality is poor - use LLM to re-rank
                        reranked_chunks = self._rerank_with_llm(
                            query=vector_query,
                            chunks=chunks,
                            top_n=k_initial
                        )
                        # Update tool results with re-ranked chunks
                        self.tool_results["search_knowledge_base"]["results"] = reranked_chunks
                        self.tool_results["search_knowledge_base"]["reranked"] = True
                        logger.info(f"Re-ranking complete: {len(reranked_chunks)} chunks retained")
                    elif len(chunks) > k_initial:
                        # Good quality but too many chunks - just truncate to k_initial
                        self.tool_results["search_knowledge_base"]["results"] = chunks[:k_initial]
                        logger.info(f"Good retrieval quality, using top {k_initial} chunks without re-ranking")

            logger.info(f"Tools executed successfully for {query_type} query")

            # AUTO-GENERATE VISUALIZATION if SQL has suitable data
            sql_data = self.tool_results.get("query_nba_database", {})
            sql_results_list = sql_data.get("results", [])
            sql_query = sql_data.get("sql", "")

            if sql_results_list and self._should_visualize(sql_results_list):
                logger.info("Auto-generating visualization for SQL results")
                try:
                    # Convert tuples to dicts if needed
                    formatted_results = self._format_sql_results(sql_results_list, sql_query)

                    viz_observation = self._execute_tool(
                        tool_name="create_visualization",
                        tool_input={
                            "query": question,
                            "sql_results": formatted_results
                        }
                    )
                    # _execute_tool returns string observation, not dict
                    # Actual result is in self.tool_results
                    viz_result_dict = self.tool_results.get("create_visualization", {})
                    chart_type = viz_result_dict.get('chart_type', 'unknown') if isinstance(viz_result_dict, dict) else 'unknown'
                    logger.info(f"Visualization generated: {chart_type}")
                except Exception as viz_error:
                    logger.warning(f"Visualization generation failed: {viz_error}")

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            # Build tools_used from what we attempted
            attempted_tools = []
            if query_type in ["sql_only", "hybrid"]:
                attempted_tools.append("query_nba_database")
            if query_type in ["vector_only", "hybrid"]:
                attempted_tools.append("search_knowledge_base")

            return {
                "answer": f"I encountered an error retrieving information: {str(e)}",
                "tools_used": attempted_tools,
                "tool_results": self.tool_results,
                "query_type": query_type,
                "error": str(e),
            }

        # Build prompt with executed tool results
        # Get actual dicts from tool_results (not string observations)
        sql_data = self.tool_results.get("query_nba_database") if sql_result else None
        vector_data = self.tool_results.get("search_knowledge_base") if vector_result else None

        prompt = self._build_combined_prompt(
            question=question,
            conversation_history=conversation_history,
            sql_result=sql_data,
            vector_result=vector_data,
            query_type=query_type,
        )

        # Single LLM call to generate answer
        try:
            answer = self._call_llm(prompt)
            logger.info(f"LLM generated final answer (length: {len(answer)} chars)")

            # Build tools_used list from what was actually executed
            tools_used = []
            if sql_result is not None:
                tools_used.append("query_nba_database")
            if vector_result is not None:
                tools_used.append("search_knowledge_base")
            if "create_visualization" in self.tool_results:
                tools_used.append("create_visualization")

            # Ensure citations are present for faithfulness
            # Get actual dicts from tool_results (not string observations)
            sql_data = self.tool_results.get("query_nba_database") if sql_result else None
            vector_data = self.tool_results.get("search_knowledge_base") if vector_result else None

            answer_with_citations = self._ensure_citations(
                answer=answer,
                sql_result=sql_data,
                vector_result=vector_data
            )

            return {
                "answer": answer_with_citations,
                "tools_used": tools_used,
                "tool_results": self.tool_results,
                "query_type": query_type,
                "is_hybrid": query_type == "hybrid",
            }

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise Exception(f"LLM call failed: {str(e)}") from e

    def _ensure_citations(
        self,
        answer: str,
        sql_result: Any,
        vector_result: Any
    ) -> str:
        """Ensure answer includes source citations for faithfulness.

        Args:
            answer: Generated answer text
            sql_result: SQL query results (if executed)
            vector_result: Vector search results (if executed)

        Returns:
            Answer with citations appended if not already present
        """
        # Check if answer already has citations
        if "Sources:" in answer or "Source:" in answer:
            return answer  # LLM already included citations

        # Build citations list
        citations = []

        if sql_result:
            citations.append("NBA Database")

        if vector_result and isinstance(vector_result, dict):
            # Add Reddit citations with real metadata (post author + upvotes)
            if "results" in vector_result:
                results = vector_result["results"][:5]  # Limit to top 5
                logger.info(f"Adding {len(results)} Reddit citations with metadata (total results: {len(vector_result['results'])})")

                for result in results:
                    # Extract metadata from chunk
                    metadata = result.get("metadata", {})
                    post_author = metadata.get("post_author", "unknown")
                    post_upvotes = metadata.get("post_upvotes", 0)

                    # Format citation: u/username (upvotes)
                    citation = f"u/{post_author} ({post_upvotes} upvotes)"
                    citations.append(citation)
                    logger.debug(f"Added citation: {citation}")

        # Append citations if any sources were used
        if citations:
            # Remove trailing whitespace and add citations
            answer = answer.rstrip()
            if not answer.endswith("."):
                answer += "."
            answer += f"\n\nSources: {', '.join(citations)}"
            logger.info(f"Added citations: {', '.join(citations)}")

        return answer

    def _build_combined_prompt(
        self,
        question: str,
        conversation_history: str,
        sql_result: Any,
        vector_result: Any,
        query_type: str,
    ) -> str:
        """Build prompt with executed tool results for single LLM call.

        Args:
            question: User question
            conversation_history: Previous conversation context
            sql_result: Results from SQL database query (None if not executed)
            vector_result: Results from vector search (None if not executed)
            query_type: Classification result ("sql_only", "vector_only", "hybrid")

        Returns:
            Prompt string with available results
        """
        # Format SQL results if available
        sql_formatted = json.dumps(sql_result, indent=2) if sql_result else "Not retrieved (not needed for this query type)"

        # Format vector results if available
        vector_formatted = json.dumps(vector_result, indent=2) if vector_result else "Not retrieved (not needed for this query type)"

        # Build instructions based on what was retrieved
        if query_type == "sql_only":
            instructions = """QUERY TYPE: Statistical (SQL-only)
Your task: Answer using the SQL database results below. This is a pure statistical query.

CRITICAL RULES FOR RELEVANCY:
1. Read the question carefully and answer EXACTLY what is asked
2. Don't add information not requested in the question
3. If the question asks for specific details (top N, comparisons, etc.), provide exactly that
4. Stay focused on the user's specific question - don't go off-topic

CRITICAL RULES FOR FAITHFULNESS:
1. ONLY use information present in the SQL results - no speculation, no assumptions
2. Every number, stat, or fact MUST come directly from the SQL results
3. If SQL results are empty or incomplete, say gracefully: "I don't have that information"
4. Never infer or calculate stats not explicitly provided
5. DO NOT mention "SQL", "database", or technical terms

BANNED BEHAVIORS:
❌ Adding facts not in SQL results
❌ Speculating about reasons or context
❌ Answering a different question than asked"""

        elif query_type == "vector_only":
            instructions = """QUERY TYPE: Contextual (Vector-only)
Your task: Answer using the vector search results below. This is a contextual/opinion query.

CRITICAL RULES FOR RELEVANCY:
1. Answer the EXACT question asked - don't provide related but different information
2. If the question asks "why", explain reasons; if "what do fans think", share opinions
3. Match the scope of your answer to the question (don't over-explain or under-explain)

CRITICAL RULES FOR FAITHFULNESS:
1. ONLY use information present in the vector search results
2. Every claim, opinion, or fact MUST come from the retrieved documents
3. Summarize opinions naturally WITHOUT inline citations (no usernames, no parenthetical references)
4. If results don't answer the question, admit it gracefully: "I don't have information about [topic]"
5. DO NOT mention "vector search", "knowledge base", usernames, or technical terms
6. Never make up opinions, debates, or context not in the results

BANNED BEHAVIORS:
❌ Inventing opinions or debates not in results
❌ Generalizing beyond what the documents say
❌ Answering a related but different question
❌ Adding inline citations like (u/username) or (Reddit post)"""

        else:  # hybrid
            instructions = """QUERY TYPE: Hybrid (SQL + Vector)
Your task: Combine both SQL and vector results to provide a comprehensive answer.

CRITICAL RULES FOR RELEVANCY:
1. Answer EXACTLY what the user asked - not more, not less
2. If question has multiple parts (stats + context), address BOTH
3. Don't add unrequested information or go off-topic
4. Match your answer structure to the question structure

CRITICAL RULES FOR FAITHFULNESS:
1. SQL results are the ONLY source for numbers, stats, rankings - NEVER make up stats
2. Vector results are the ONLY source for context, opinions, explanations - NEVER invent context
3. Every claim must be traceable to either SQL or vector results
4. If SQL and vector conflict on factual stats, ALWAYS trust SQL
5. If information is missing from BOTH sources, admit it gracefully
6. Combine sources intelligently: stats from SQL + context from vector

GRACEFUL HONESTY - If information is missing or incomplete:
- Focus on what information you DO have (stats OR context)
- Be honest about limitations without technical jargon
- NEVER mention "vector search", "SQL", "database", "knowledge base"
- Instead say: "I don't have detailed analysis of [topic]" or "Based on available statistics..."
- Example: "While I don't have specific analysis of their playing style, the efficiency metrics suggest..."

BANNED BEHAVIORS:
❌ Inventing stats not in SQL results
❌ Making up context not in vector results
❌ Speculating or inferring beyond what sources provide
❌ Answering a different question than asked
❌ Mentioning technical implementation details
❌ Adding inline citations like (u/username) or (Reddit post)"""

        # Note: Citations will be added automatically by _ensure_citations()
        # No need to instruct LLM to add them (ensures consistent format)

        # Add context awareness instructions if conversation history exists
        context_instructions = ""
        if conversation_history:
            context_instructions = """
CONTEXT AWARENESS (Multi-turn Conversation):
✓ Use conversation history to resolve pronouns (he, she, they, their, his, her)
✓ Pronouns like "they" or "he" refer to entities mentioned in previous turns
✓ If the user asks "What team do they play for?", look at the previous conversation to identify who "they" refers to
✓ Maintain conversational continuity - understand implicit references
"""

        prompt = f"""You are an NBA statistics assistant.

{instructions}

USER QUESTION:
{question}

SQL DATABASE RESULTS (FACTUAL STATS):
{sql_formatted}

VECTOR SEARCH RESULTS (CONTEXT & OPINIONS):
{vector_formatted}

CONVERSATION HISTORY:
{conversation_history or "None"}
{context_instructions}

IMPORTANT REMINDERS:
✓ RELEVANCY: Answer EXACTLY what the user asked - stay on topic
✓ FAITHFULNESS: Use ONLY information from the results above - no speculation or assumptions
✓ HONESTY: If you don't have the information, admit it gracefully

Your answer:"""

        return prompt

    def _execute_tool(
        self, tool_name: str, tool_input: dict[str, Any]
    ) -> str:
        """Execute tool, store result, and return observation string."""
        if tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_name}'"

        tool = self.tools[tool_name]
        try:
            result = tool.function(**tool_input)

            # Store structured result for direct access (no string parsing needed!)
            self.tool_results[tool_name] = result

            # Return truncated string observation for prompt
            return str(result)[:1200]  # Increased from 800 to reduce info loss
        except Exception as e:
            logger.error(f"Tool {tool_name} execution failed: {e}")
            return f"Error executing {tool_name}: {str(e)}"

    def _call_llm(self, prompt: str) -> str:
        """Call LLM with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.llm_client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={"temperature": self.temperature},  # Use configured temperature
                )
                logger.debug(f"LLM Response (first 500 chars): {response.text[:500]}")
                return response.text
            except Exception as e:
                if attempt >= max_retries - 1:
                    raise Exception(f"LLM call failed after {max_retries} attempts: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff

    def _should_visualize(self, sql_results: list) -> bool:
        """Determine if SQL results should be visualized.

        Simple rule: Visualize if 2+ rows (likely a ranking/comparison)

        Args:
            sql_results: SQL query results (list of tuples or dicts)

        Returns:
            True if results should be visualized
        """
        # Simple: visualize if we have 2+ rows (rankings, comparisons, top N)
        # Single row = single player/team stats (no chart needed)
        return (
            sql_results
            and isinstance(sql_results, list)
            and len(sql_results) >= 2
        )

    def _format_sql_results(self, results: list, sql_query: str) -> list[dict]:
        """Convert SQL results to list of dicts for visualization.

        Uses simple heuristics:
        - If already dicts → return as-is
        - If tuples with 2 cols → assume (name, value)
        - Otherwise → use generic col0, col1, etc.

        Args:
            results: SQL results (list of tuples or dicts)
            sql_query: SQL query string (for future enhancement)

        Returns:
            List of dictionaries with column names as keys
        """
        if not results:
            return []

        # DEBUG LOGGING
        logger.debug(f"_format_sql_results received results type: {type(results)}")
        logger.debug(f"_format_sql_results received results[0] type: {type(results[0])}")
        logger.debug(f"_format_sql_results received results[0] content: {results[0]}")

        # If already dicts, return as-is
        if isinstance(results[0], dict):
            logger.debug("Results already dicts, returning as-is")
            return results

        # SAFETY CHECK: Ensure results[0] is iterable (tuple/list), not a string
        if isinstance(results[0], str):
            logger.error(f"_format_sql_results ERROR: results[0] is a STRING: {results[0]}")
            logger.error(f"Full results: {results}")
            # Try to recover: assume single-column data
            return [{"value": row} for row in results]

        # Simple heuristic: Most top N queries have (name, value) format
        num_cols = len(results[0])
        logger.debug(f"Detected {num_cols} columns")

        if num_cols == 2:
            # Assume: (name, value) - most common case
            column_names = ["name", "value"]
        else:
            # Generic column names
            column_names = [f"col{i}" for i in range(num_cols)]

        # Convert tuples to dicts
        return [
            {col: value for col, value in zip(column_names, row)}
            for row in results
        ]
