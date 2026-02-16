"""
File: src/agents/tools.py
Description: Tool wrappers for ReAct agent
Created: 2026-02-14
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class NBAToolkit:
    """NBA tools for ReAct agent."""

    def __init__(
        self,
        sql_tool,
        vector_store,
        embedding_service,
        visualization_service,
    ):
        """Initialize toolkit with service dependencies.

        Args:
            sql_tool: NBAGSQLTool instance for SQL queries
            vector_store: VectorStoreRepository for vector search
            embedding_service: EmbeddingService for query embeddings
            visualization_service: VisualizationService for charts
        """
        self.sql_tool = sql_tool
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.visualization_service = visualization_service

    def query_nba_database(self, question: str) -> dict[str, Any]:
        """Query NBA statistics database for numerical data.

        Use this tool for:
        - Player statistics (points, rebounds, assists, etc.)
        - Team rankings and standings
        - Top N queries (top 5 scorers, best defenders)
        - Statistical comparisons (Jokić vs Embiid)
        - Aggregations (average, sum, count)
        - Filters (players over 30 years old)

        Args:
            question: Natural language question about NBA stats

        Returns:
            Dict with sql, results, error, row_count

        Examples:
            - "Who scored the most points this season?"
            - "Top 5 rebounders"
            - "Compare Jokić and Embiid stats"
            - "Average points for Lakers players"
        """
        try:
            # Use LangChain SQL agent for query generation and execution
            result = self.sql_tool.query(question)

            return {
                "sql": result.get("sql", ""),
                "results": result.get("results", []),
                "answer": result.get("answer", ""),  # Agent's formatted answer
                "error": result.get("error"),
                "row_count": len(result.get("results", [])),
                "agent_steps": result.get("agent_steps", 0),  # Number of reasoning steps
            }

        except Exception as e:
            # Log full exception with traceback for debugging
            logger.exception(f"SQL tool execution failed for question: {question[:100]}")
            return {
                "sql": "",
                "results": [],
                "answer": "",
                "error": str(e),
                "row_count": 0,
                "agent_steps": 0,
            }

    def search_knowledge_base(
        self, query: str, k: int = 5
    ) -> dict[str, Any]:
        """Search NBA knowledge base for opinions, context, explanations.

        Use this tool for:
        - Why/how questions (Why is LeBron great?)
        - Fan opinions and discussions
        - Playing styles and strategies
        - Team culture and dynamics
        - Historical context
        - Qualitative assessments

        Args:
            query: Search query
            k: Number of results to return (default 5)

        Returns:
            Dict with results, sources, count

        Examples:
            - "Why is LeBron considered the GOAT?"
            - "What do fans think about the Lakers?"
            - "Explain zone defense strategy"
            - "What is the Warriors team culture like?"
        """
        try:
            # Generate embedding for query
            embedding = self.embedding_service.embed_query(query)

            # Search vector store
            search_results = self.vector_store.search(
                query_embedding=embedding,
                k=k,
                min_score=0.5,
                query_text=query,
            )

            # Format results
            formatted_results = []
            sources = set()

            for chunk, score in search_results:
                formatted_results.append({
                    "text": chunk.text,
                    "score": float(score),
                    "source": chunk.metadata.get("source", "Unknown"),
                    "metadata": {
                        k: v
                        for k, v in chunk.metadata.items()
                        if k in ["title", "author", "upvotes", "post_id"]
                    },
                })
                sources.add(chunk.metadata.get("source", "Unknown"))

            return {
                "results": formatted_results,
                "sources": list(sources),
                "count": len(formatted_results),
                "query": query,
            }

        except Exception as e:
            # Log full exception with traceback for debugging
            logger.exception(f"Vector search failed for query: {query[:100]}")
            return {
                "results": [],
                "sources": [],
                "count": 0,
                "error": str(e),
                "query": query,
            }

    def create_visualization(
        self, query: str, sql_results: list[dict]
    ) -> dict[str, Any]:
        """Generate interactive chart from SQL results.

        Use this tool AFTER query_nba_database returns data for statistical queries.
        Auto-detects visualization type:
        - Top N queries → Horizontal bar chart
        - Comparisons → Radar chart
        - Distributions → Histogram

        Args:
            query: Original user question
            sql_results: Results from query_nba_database

        Returns:
            Dict with plotly_json, chart_type, or error

        Examples:
            - After "Top 5 scorers" → Bar chart
            - After "Compare two players" → Radar chart
        """
        if not sql_results:
            return {
                "error": "No data to visualize",
                "chart_type": None,
                "plotly_json": None,
            }

        try:
            # Auto-detect chart type based on data shape
            chart_type = "horizontal_bar" if len(sql_results) <= 10 else "table"
            title = query if len(query) < 50 else "NBA Statistics"

            # Use simplified visualization service
            viz_result = self.visualization_service.generate_chart(
                chart_type=chart_type,
                data=sql_results,
                title=title,
            )

            if viz_result and viz_result.get("plotly_json"):
                return {
                    "plotly_json": viz_result["plotly_json"],
                    "plotly_html": viz_result.get("plotly_html"),
                    "chart_type": viz_result.get("chart_type", chart_type),
                    "error": None,
                }
            else:
                return {
                    "error": viz_result.get("error", "Could not generate visualization"),
                    "chart_type": None,
                    "plotly_json": None,
                }

        except Exception as e:
            return {
                "error": str(e),
                "chart_type": None,
                "plotly_json": None,
            }


def create_nba_tools(toolkit: NBAToolkit) -> list:
    """Create Tool instances for ReAct agent V2.

    Args:
        toolkit: NBAToolkit instance with service dependencies

    Returns:
        List of Tool objects for agent
    """
    from src.agents.react_agent import Tool

    return [
        Tool(
            name="query_nba_database",
            description=(
                "Query NBA statistics database for numerical data. "
                "Use for player stats, team rankings, top N queries, "
                "comparisons, aggregations, and statistical filters."
            ),
            function=toolkit.query_nba_database,
            parameters={"question": "str"},
            examples=[
                "Who scored the most points?",
                "Top 5 rebounders",
                "Compare Jokić and Embiid stats",
                "Average points for Lakers players",
                "Players with more than 2000 points",
            ],
        ),
        Tool(
            name="search_knowledge_base",
            description=(
                "Search NBA knowledge base for opinions, context, and explanations. "
                "Use for why/how questions, fan opinions, playing styles, "
                "team culture, and qualitative assessments."
            ),
            function=toolkit.search_knowledge_base,
            parameters={"query": "str", "k": "int (default 5)"},
            examples=[
                "Why is LeBron considered the GOAT?",
                "What do fans think about the Lakers?",
                "Explain zone defense strategy",
                "What is the Warriors team culture like?",
                "How does Jokić's playmaking compare to traditional centers?",
            ],
        ),
        Tool(
            name="create_visualization",
            description=(
                "Generate interactive chart from SQL results. "
                "Use AFTER query_nba_database returns data. "
                "Auto-detects chart type (bar, radar, histogram)."
            ),
            function=toolkit.create_visualization,
            parameters={"query": "str", "sql_results": "list[dict]"},
            examples=[
                "Top 5 scorers visualization",
                "Player comparison chart",
            ],
        ),
    ]
