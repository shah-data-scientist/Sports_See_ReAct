"""
File: src/agents/results_formatter.py
Description: Results formatting and output preparation for NBA queries
Responsibilities: Citations, visualization checks, SQL result formatting, prompt building
Created: 2026-02-16
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ResultsFormatter:
    """Formatter for NBA query results and outputs.

    Handles citations, visualization decisions, and result formatting
    for SQL and vector search results.
    """

    @staticmethod
    def ensure_citations(
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

    @staticmethod
    def should_visualize(sql_results: list) -> bool:
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

    @staticmethod
    def format_sql_results(results: list, sql_query: str) -> list[dict]:
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
        logger.debug(f"format_sql_results received results type: {type(results)}")
        logger.debug(f"format_sql_results received results[0] type: {type(results[0])}")
        logger.debug(f"format_sql_results received results[0] content: {results[0]}")

        # If already dicts, return as-is
        if isinstance(results[0], dict):
            logger.debug("Results already dicts, returning as-is")
            return results

        # SAFETY CHECK: Ensure results[0] is iterable (tuple/list), not a string
        if isinstance(results[0], str):
            logger.error(f"format_sql_results ERROR: results[0] is a STRING: {results[0]}")
            logger.error(f"format_sql_results ERROR: Full results: {results}")
            return []

        # Convert tuples to dicts
        if isinstance(results[0], (tuple, list)):
            # Simple heuristic: 2 columns = (name, value)
            if len(results[0]) == 2:
                logger.debug("Converting 2-column tuples to dicts with 'name' and 'value'")
                return [{"name": row[0], "value": row[1]} for row in results]

            # More columns: use generic col0, col1, etc.
            logger.debug(f"Converting {len(results[0])}-column tuples to dicts with col0, col1, etc.")
            return [
                {f"col{i}": val for i, val in enumerate(row)}
                for row in results
            ]

        logger.warning(f"Unexpected result type: {type(results[0])}, returning as-is")
        return results

    @staticmethod
    def build_combined_prompt(
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
4. Never make up stats or numbers - if it's not in the SQL results, don't say it
5. When citing stats, match the SQL results exactly (don't round or modify numbers)

FORMAT:
- Be concise and direct
- Answer in 1-2 sentences for simple queries
- For rankings/lists, format clearly (e.g., "1. Player A - X pts, 2. Player B - Y pts")
"""

        elif query_type == "vector_only":
            instructions = """QUERY TYPE: Contextual (Vector-only)
Your task: Answer using the NBA discussions/context below. This is an opinion/explanation query.

CRITICAL RULES FOR RELEVANCY:
1. Answer the specific question asked - don't go off-topic
2. Focus on the most relevant information from the context
3. If context doesn't fully answer the question, say so gracefully

CRITICAL RULES FOR FAITHFULNESS:
1. ONLY use information from the retrieved context - no speculation
2. If context has conflicting opinions, acknowledge the disagreement
3. Attribute information to sources when possible (e.g., "According to fans...", "Discussed on Reddit...")
4. If context is insufficient, say: "I don't have enough information on this topic"

FORMAT:
- Provide a clear, concise answer (2-4 sentences)
- Cite sources if available (e.g., user comments, upvotes)
"""

        else:  # hybrid
            instructions = """QUERY TYPE: Hybrid (Stats + Context)
Your task: Combine SQL stats with NBA context to provide a complete answer.

CRITICAL RULES FOR RELEVANCY:
1. Balance statistical data with contextual explanations
2. Answer exactly what's asked - don't over-explain if question is simple
3. Use stats to support context, or context to explain stats

CRITICAL RULES FOR FAITHFULNESS:
1. Stats: ONLY use SQL results - no speculation on numbers
2. Context: ONLY use retrieved discussions - no invented opinions
3. Clearly separate facts (from SQL) from opinions (from context)
4. If either SQL or context is missing key info, acknowledge the limitation

FORMAT:
- Lead with the most important information (stat or context depending on question)
- Support with additional details
- Keep it concise (3-5 sentences unless question requires more depth)
"""

        # Build full prompt
        prompt = f"""{instructions}

CONVERSATION HISTORY:
{conversation_history if conversation_history else "No prior conversation"}

USER QUESTION:
{question}

SQL DATABASE RESULTS:
{sql_formatted}

NBA CONTEXT (Reddit/Discussions):
{vector_formatted}

YOUR ANSWER:"""

        return prompt
