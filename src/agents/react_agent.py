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
        """Classify query to determine which tools are needed.

        Uses simple heuristics (not complex regex patterns):
        - SQL-only: top N, rankings, stats, numbers, comparisons
        - Vector-only: why/how, opinions, debates, context, explanations
        - Hybrid: biographical ("Who is X?"), stats + context

        Args:
            question: User question (lowercase for matching)

        Returns:
            "sql_only", "vector_only", or "hybrid"
        """
        q_lower = question.lower()

        # Strong vector-only signals (override other signals)
        # These indicate pure opinion/contextual queries
        strong_vector_signals = [
            "what do fans", "what are fans", "what do reddit",
            "what do people think", "what are people", "debate about",
            "popular opinion", "fans think", "fans believe"
        ]

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

        # Hybrid signals (biographical - need both stats and context)
        hybrid_signals = ["who is", "tell me about", "what about"]

        # Check strong vector signals first (highest priority)
        if any(signal in q_lower for signal in strong_vector_signals):
            return "vector_only"

        # Check hybrid (biographical queries)
        if any(signal in q_lower for signal in hybrid_signals):
            return "hybrid"

        # Count signals for each type
        vector_count = sum(1 for signal in vector_signals if signal in q_lower)
        sql_count = sum(1 for signal in sql_signals if signal in q_lower)

        # If strong vector signal (why/how/think) present, prioritize vector
        # even if SQL signals are also present
        has_strong_opinion = any(word in q_lower for word in ["why", "how", "think", "believe", "opinion"])
        if has_strong_opinion and vector_count > 0:
            # If also asking for stats (e.g., "why did he score so many points?"), it's hybrid
            if any(word in q_lower for word in ["scored", "points", "stats", "average"]):
                return "hybrid"
            return "vector_only"

        # If both have signals, it's hybrid
        if vector_count > 0 and sql_count > 0:
            return "hybrid"

        # If only vector signals, it's vector-only
        if vector_count > 0:
            return "vector_only"

        # Default to SQL (most queries are statistical)
        return "sql_only"

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

            # Execute vector search if needed
            if query_type in ["vector_only", "hybrid"]:
                logger.debug("Executing search_knowledge_base...")
                vector_result = self._execute_tool(
                    tool_name="search_knowledge_base",
                    tool_input={"query": question, "k": 7}
                )

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
        prompt = self._build_combined_prompt(
            question=question,
            conversation_history=conversation_history,
            sql_result=sql_result,
            vector_result=vector_result,
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

            return {
                "answer": answer,
                "tools_used": tools_used,
                "tool_results": self.tool_results,
                "query_type": query_type,
                "is_hybrid": query_type == "hybrid",
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

CRITICAL RULES:
1. Use SQL results as your primary source
2. Be concise and factual
3. If SQL results are empty or don't answer the question, say so clearly"""

        elif query_type == "vector_only":
            instructions = """QUERY TYPE: Contextual (Vector-only)
Your task: Answer using the vector search results below. This is a contextual/opinion query.

CRITICAL RULES:
1. Use vector search results for opinions, debates, explanations
2. Cite sources when mentioning specific information
3. If vector results don't answer the question, say so clearly"""

        else:  # hybrid
            instructions = """QUERY TYPE: Hybrid (SQL + Vector)
Your task: Combine both SQL and vector results to provide a comprehensive answer.

CRITICAL RULES:
1. SQL results are ALWAYS the source of truth for statistics, scores, numbers
2. Use vector results for context, opinions, "why/how" explanations, background
3. If SQL and vector conflict on factual stats, TRUST SQL
4. Combine both intelligently when both add value
5. If both sources are empty or irrelevant, say you don't have enough information"""

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

Based on the above information, provide a complete, accurate answer to the user's question.
Focus on being helpful and concise.

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
