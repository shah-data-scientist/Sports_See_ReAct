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
from google.genai import types

from src.agents.query_classifier import QueryClassifier
from src.agents.results_formatter import ResultsFormatter

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# Re-ranking Configuration
RERANKING_QUALITY_THRESHOLD = 0.70  # Re-rank if top-1 score < this (70%)
RERANKING_OVERFETCH_MULTIPLIER = 1.5  # Retrieve k*1.5 chunks for re-ranking
SCORE_NORMALIZATION_FACTOR = 100.0  # Raw scores are 0-100, normalize to 0-1



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

        # Initialize query classifier
        self.classifier = QueryClassifier(client=llm_client, model=model)

        # Tool results storage (structured access for direct extraction)
        self.tool_results: dict[str, Any] = {}

    def _execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool and store its result.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result dictionary

        Raises:
            ValueError: If tool not found
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available: {list(self.tools.keys())}")

        tool = self.tools[tool_name]

        try:
            logger.debug(f"Executing tool: {tool_name} with input: {tool_input}")

            # Call the tool's function with the input parameters
            result = tool.function(**tool_input)

            # Store result for later access
            self.tool_results[tool_name] = result

            logger.debug(f"Tool {tool_name} executed successfully")
            return result

        except Exception as e:
            logger.exception(f"Tool {tool_name} execution failed: {e}")
            # Return error result
            error_result = {"error": str(e), "success": False}
            self.tool_results[tool_name] = error_result
            return error_result

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

            # P0 ISSUE #1 FIX REVISED: Threshold removed after empirical analysis
            # RATIONALE: LLM re-ranking scores 0-3 (not 0-10), making any threshold >1 too strict.
            # Evidence shows LLM gracefully handles low-quality chunks (says "I don't have information").
            # Re-ranking still improves ordering; threshold was filtering out useful chunks.
            # See: evaluation_results/POST_FIX_COMPARISON.md and analyze_low_quality_chunks.py

            # Keep all chunks but sort by relevance score (no threshold filtering)
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

    def _call_llm(self, prompt: str) -> str:
        """Call LLM with a prompt and return the response.

        Args:
            prompt: Prompt to send to the LLM

        Returns:
            LLM response text
        """
        try:
            response = self.llm_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=2048,
                )
            )
            return response.text.strip()
        except Exception as e:
            logger.exception(f"LLM call failed: {e}")
            raise

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
        query_type = self.classifier.classify(question)
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
                # Retrieve more chunks initially for re-ranking
                k_initial = self._determine_k(vector_query, query_type)
                k_retrieve = int(k_initial * RERANKING_OVERFETCH_MULTIPLIER)  # Retrieve 50% more for re-ranking

                logger.debug(f"Executing search_knowledge_base with query: '{vector_query}', k={k_retrieve}")
                vector_result = self._execute_tool(
                    tool_name="search_knowledge_base",
                    tool_input={"query": vector_query, "k": k_retrieve}
                )

                # Conditional LLM re-ranking (only if retrieval quality is poor)
                # Access actual result from tool_results (vector_result is just a string observation)
                vector_data = self.tool_results.get("search_knowledge_base", {})
                if vector_data and "results" in vector_data:
                    chunks = vector_data.get("results", [])  # Safe access with default

                    # Check top-1 score to decide if re-ranking is needed
                    should_rerank = False
                    if chunks and len(chunks) > 0 and isinstance(chunks[0], dict):
                        # Get top-1 score (in 0-100 range from vector store)
                        top_score_raw = chunks[0].get("score", SCORE_NORMALIZATION_FACTOR)

                        # Normalize to 0-1 range for threshold comparison
                        top_score_normalized = top_score_raw / SCORE_NORMALIZATION_FACTOR

                        # Only re-rank if top score is low (poor quality)
                        if top_score_normalized < RERANKING_QUALITY_THRESHOLD and len(chunks) > k_initial:
                            should_rerank = True
                            logger.info(f"Top-1 score {top_score_normalized:.3f} ({top_score_raw:.1f}%) < {RERANKING_QUALITY_THRESHOLD}, re-ranking {len(chunks)} chunks")
                        else:
                            logger.info(f"Top-1 score {top_score_normalized:.3f} ({top_score_raw:.1f}%) ≥ {RERANKING_QUALITY_THRESHOLD}, skipping re-ranking (good quality)")

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

            if sql_results_list and ResultsFormatter.should_visualize(sql_results_list):
                logger.info("Auto-generating visualization for SQL results")
                try:
                    # Convert tuples to dicts if needed
                    formatted_results = ResultsFormatter.format_sql_results(sql_results_list, sql_query)

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

        prompt = ResultsFormatter.build_combined_prompt(
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

            answer_with_citations = ResultsFormatter.ensure_citations(
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
