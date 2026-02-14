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
    """Simplified agent for NBA statistics queries - "Always Both" architecture.

    This agent ALWAYS executes both SQL and Vector search for every query,
    then lets the LLM intelligently combine the results in a single call.

    Key simplifications:
    - No query classification (always both tools)
    - No routing logic (fixed execution path)
    - No iteration loop (single LLM call)
    - No complexity estimation (fixed k=7)
    - 67% less code than previous version
    """

    def __init__(
        self,
        tools: list[Tool],
        llm_client: genai.Client,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.1,
    ):
        """Initialize simplified agent.

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

    def run(
        self, question: str, conversation_history: str = ""
    ) -> dict[str, Any]:
        """Execute query with BOTH tools always (simplified architecture).

        This is the "Always Both" approach:
        - Always executes SQL database query
        - Always executes vector search
        - Single LLM call combines both results
        - No classification, no routing, no iteration

        Args:
            question: User question
            conversation_history: Previous conversation context

        Returns:
            Dict with:
                - answer: Final answer
                - tools_used: Always both tools
                - tool_results: Structured results from both tools
        """
        logger.info(f"Executing BOTH tools for query: '{question[:100]}'")

        # Clear tool results for new query
        self.tool_results = {}

        # ALWAYS execute BOTH tools (no classification needed)
        try:
            # Execute SQL database query
            logger.debug("Executing query_nba_database...")
            sql_result = self._execute_tool(
                tool_name="query_nba_database",
                tool_input={"question": question}
            )

            # Execute vector search (fixed k=7 for all queries)
            logger.debug("Executing search_knowledge_base...")
            vector_result = self._execute_tool(
                tool_name="search_knowledge_base",
                tool_input={"query": question, "k": 7}
            )

            logger.info("Both tools executed successfully")

            # AUTO-GENERATE VISUALIZATION if SQL has suitable data
            sql_data = self.tool_results.get("query_nba_database", {})
            sql_results_list = sql_data.get("results", [])
            sql_query = sql_data.get("sql", "")

            if sql_results_list and self._should_visualize(sql_results_list):
                logger.info("Auto-generating visualization for SQL results")
                try:
                    # Convert tuples to dicts if needed
                    formatted_results = self._format_sql_results(sql_results_list, sql_query)

                    viz_result = self._execute_tool(
                        tool_name="create_visualization",
                        tool_input={
                            "query": question,
                            "sql_results": formatted_results
                        }
                    )
                    logger.info(f"Visualization generated: {viz_result.get('chart_type', 'unknown')}")
                except Exception as viz_error:
                    logger.warning(f"Visualization generation failed: {viz_error}")

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {
                "answer": f"I encountered an error retrieving information: {str(e)}",
                "tools_used": ["query_nba_database", "search_knowledge_base"],
                "tool_results": self.tool_results,
                "error": str(e),
            }

        # Build prompt with BOTH results
        prompt = self._build_combined_prompt(
            question=question,
            conversation_history=conversation_history,
            sql_result=sql_result,
            vector_result=vector_result,
        )

        # Single LLM call to combine both results
        try:
            answer = self._call_llm(prompt)
            logger.info(f"LLM generated final answer (length: {len(answer)} chars)")

            # Build tools_used list (includes visualization if generated)
            tools_used = ["query_nba_database", "search_knowledge_base"]
            if "create_visualization" in self.tool_results:
                tools_used.append("create_visualization")

            return {
                "answer": answer,
                "tools_used": tools_used,
                "tool_results": self.tool_results,
                "is_hybrid": True,  # Always hybrid now
            }

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise Exception(f"LLM call failed: {str(e)}") from e

    def _build_combined_prompt(
        self,
        question: str,
        conversation_history: str,
        sql_result: Any,
        vector_result: Any,
    ) -> str:
        """Build prompt with BOTH tool results for single LLM call.

        Args:
            question: User question
            conversation_history: Previous conversation context
            sql_result: Results from SQL database query
            vector_result: Results from vector search

        Returns:
            Prompt string with both results
        """
        # Format SQL results for readability
        sql_formatted = json.dumps(sql_result, indent=2) if sql_result else "No results"

        # Format vector results for readability
        vector_formatted = json.dumps(vector_result, indent=2) if vector_result else "No results"

        prompt = f"""You are an NBA statistics assistant. You have been provided with results from TWO sources:

1. SQL DATABASE (factual statistics - THIS IS YOUR SOURCE OF TRUTH FOR NUMBERS)
2. VECTOR SEARCH (contextual information, opinions, analysis)

CRITICAL RULES:
1. SQL results are ALWAYS the source of truth for statistics, scores, numbers
2. If SQL has the answer, use it (you may ignore vector if irrelevant)
3. If SQL and vector conflict on factual stats, TRUST SQL
4. Use vector results for context, opinions, "why/how" questions, background info
5. Combine both intelligently when both add value
6. If both sources are empty or irrelevant, say you don't have enough information

USER QUESTION:
{question}

SQL DATABASE RESULTS (FACTUAL STATS):
{sql_formatted}

VECTOR SEARCH RESULTS (CONTEXT & OPINIONS):
{vector_formatted}

CONVERSATION HISTORY:
{conversation_history or "None"}

Based on the above information, provide a complete, accurate answer to the user's question.
Focus on being helpful and concise. If the results don't answer the question, say so clearly.

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

        # If already dicts, return as-is
        if isinstance(results[0], dict):
            return results

        # Simple heuristic: Most top N queries have (name, value) format
        num_cols = len(results[0])

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
