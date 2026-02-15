"""
FILE: chat.py
STATUS: Active
RESPONSIBILITY: ReAct agent-based RAG orchestration service
LAST MAJOR UPDATE: 2026-02-14 (Migrated to ReAct architecture)
MAINTAINER: Shahu
"""

import logging
import threading
import time
from typing import Any, Callable, Optional, TypeVar

# LAZY IMPORTS: Heavy modules are imported on-demand
_lazy_imports_initialized = False
genai = None
ClientError = None
EmbeddingService = None
VisualizationService = None
NBAGSQLTool = None
ReActAgent = None
NBAToolkit = None
create_nba_tools = None


def _initialize_lazy_imports():
    """Initialize all heavy imports on first use."""
    global _lazy_imports_initialized, genai, ClientError, EmbeddingService
    global VisualizationService, NBAGSQLTool, ReActAgent, NBAToolkit, create_nba_tools

    if _lazy_imports_initialized:
        return

    # Import heavy modules (only happens once)
    from google import genai as genai_module
    from google.genai.errors import ClientError as ClientErrorModule
    from src.services.embedding import EmbeddingService as EmbeddingServiceModule
    from src.services.visualization import (
        VisualizationService as VisualizationServiceModule,
    )
    from src.tools.sql_tool import NBAGSQLTool as NBAGSQLToolModule
    from src.agents.react_agent import ReActAgent as ReActAgentModule
    from src.agents.tools import NBAToolkit as NBAToolkitModule
    from src.agents.tools import create_nba_tools as create_nba_tools_module

    genai = genai_module
    ClientError = ClientErrorModule
    EmbeddingService = EmbeddingServiceModule
    VisualizationService = VisualizationServiceModule
    NBAGSQLTool = NBAGSQLToolModule
    ReActAgent = ReActAgentModule
    NBAToolkit = NBAToolkitModule
    create_nba_tools = create_nba_tools_module

    _lazy_imports_initialized = True


# Import only lightweight modules at module level
from src.core.config import settings
from src.core.exceptions import IndexNotFoundError, LLMError
from src.core.observability import logfire
from src.core.security import sanitize_query, validate_search_params
from src.models.chat import ChatRequest, ChatResponse, SearchResult, Visualization
from src.models.feedback import ChatInteractionCreate
from src.repositories.feedback import FeedbackRepository
from src.repositories.vector_store import VectorStoreRepository

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_exponential_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_delay: float = 2.0,
    max_delay: float = 30.0,
) -> T:
    """Retry a function with exponential backoff on rate limit errors.

    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (doubles each retry)
        max_delay: Maximum delay in seconds

    Returns:
        Result from successful function call

    Raises:
        LLMError: If all retries exhausted or non-rate-limit error occurs
    """
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            return func()
        except ClientError as e:
            error_msg = str(e)

            # Check if it's a rate limit error
            if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
                if attempt < max_retries:
                    logger.warning(
                        f"Rate limit hit (attempt {attempt + 1}/{max_retries + 1}). "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)
                    continue

            # Non-rate-limit error or final attempt - raise
            raise LLMError(f"LLM call failed: {error_msg}") from e

    raise LLMError(f"All {max_retries + 1} attempts failed due to rate limiting")


class ChatService:
    """Chat service using ReAct agent for dynamic tool selection."""

    def __init__(
        self,
        vector_store: Optional[VectorStoreRepository] = None,
        feedback_repo: Optional[FeedbackRepository] = None,
        enable_sql: bool = True,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.1,
    ):
        """Initialize chat service with ReAct agent.

        Args:
            vector_store: Vector store for document search
            feedback_repo: Feedback repository for interactions
            enable_sql: Enable SQL tool (default True)
            model: LLM model to use
            temperature: LLM temperature
        """
        # Lazy init heavy modules
        _initialize_lazy_imports()

        self.vector_store = vector_store or VectorStoreRepository()
        self.feedback_repo = feedback_repo or FeedbackRepository()
        self._enable_sql = enable_sql
        self.model = model
        self._temperature = temperature

        # Load vector store index from disk
        if not self.vector_store.is_loaded:
            loaded = self.vector_store.load()
            if loaded:
                logger.info(
                    f"Vector store loaded: {self.vector_store.index_size} vectors, "
                    f"{len(self.vector_store.chunks)} chunks"
                )
            else:
                logger.warning(
                    "Vector store files not found - vector search will be unavailable"
                )

        # API key
        self._api_key = settings.google_api_key

        # LLM client (lazy)
        self._client: Optional[Any] = None

        # Services (lazy)
        self._embedding_service: Optional[Any] = None
        self._sql_tool: Optional[Any] = None
        self._visualization_service: Optional[Any] = None

        # ReAct agent (lazy)
        self._agent: Optional[Any] = None

        logger.info(f"ChatService initialized (ReAct mode, SQL={enable_sql})")

    def ensure_ready(self) -> None:
        """Ensure service is ready (vector store loaded).

        Raises:
            IndexNotFoundError: If vector store is not loaded
        """
        if not self.vector_store.is_loaded:
            raise IndexNotFoundError("Vector store index not loaded")

    @property
    def client(self) -> Any:
        """Lazy initialize Google Generative AI client."""
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    @property
    def is_ready(self) -> bool:
        """Check if service is ready to handle requests.

        Returns:
            True if vector store is loaded, False otherwise
        """
        return self.vector_store.is_loaded

    @property
    def embedding_service(self) -> Any:
        """Lazy initialize embedding service."""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    @property
    def sql_tool(self) -> Any:
        """Lazy initialize SQL tool."""
        if self._sql_tool is None:
            self._sql_tool = NBAGSQLTool()
        return self._sql_tool

    @property
    def visualization_service(self) -> Any:
        """Lazy initialize visualization service."""
        if self._visualization_service is None:
            self._visualization_service = VisualizationService()
        return self._visualization_service

    @property
    def agent(self) -> Any:
        """Lazy initialize ReAct agent with tools (cached)."""
        if self._agent is None:
            # Create toolkit with service dependencies
            toolkit = NBAToolkit(
                sql_tool=self.sql_tool,
                vector_store=self.vector_store,
                embedding_service=self.embedding_service,
                visualization_service=self.visualization_service,
            )

            # Create tools
            tools = create_nba_tools(toolkit)

            # Initialize agent (simplified - always calls both tools)
            self._agent = ReActAgent(
                tools=tools,
                llm_client=self.client,
                model=self.model,
                temperature=self._temperature,
            )

            logger.info("ReAct agent initialized with 3 tools (cached)")

        return self._agent

    def _build_conversation_context(
        self, conversation_id: str, turn_number: int
    ) -> str:
        """Build conversation history for context."""
        if turn_number <= 1:
            return ""

        try:
            # Get last 5 turns (or turn_number-1, whichever is smaller)
            history_turns = min(5, turn_number - 1)
            interactions = self.feedback_repo.get_conversation_history(
                conversation_id, limit=history_turns
            )

            if not interactions:
                return ""

            # Format as Q&A pairs
            history_lines = []
            for interaction in reversed(interactions):
                history_lines.append(f"User: {interaction.user_query}")
                history_lines.append(f"Assistant: {interaction.assistant_response}")

            return "\n".join(history_lines)

        except Exception as e:
            logger.error(f"Error building conversation context: {e}")
            return ""

    def _save_interaction(
        self,
        query: str,
        response: str,
        conversation_id: Optional[str],
        turn_number: int,
        processing_time_ms: float,
        query_type: str,
        sources: list[SearchResult],
        generated_sql: Optional[str] = None,
    ):
        """Save chat interaction to database."""
        try:
            if not conversation_id:
                return

            interaction = ChatInteractionCreate(
                conversation_id=conversation_id,
                turn_number=turn_number,
                user_query=query,
                assistant_response=response,
                query_type=query_type,
                sources_used=len(sources),
                processing_time_ms=processing_time_ms,
                model_used=self.model,
                generated_sql=generated_sql,
            )

            self.feedback_repo.create_interaction(interaction)

        except Exception as e:
            logger.error(f"Error saving interaction: {e}")

    def _save_interaction_async(
        self,
        query: str,
        response: str,
        conversation_id: Optional[str],
        turn_number: int,
        processing_time_ms: float,
        query_type: str,
        sources: list[SearchResult],
        generated_sql: Optional[str] = None,
    ):
        """Schedule async DB save (non-blocking, fire-and-forget)."""
        def _save_in_thread():
            """Background thread for DB save."""
            try:
                self._save_interaction(
                    query=query,
                    response=response,
                    conversation_id=conversation_id,
                    turn_number=turn_number,
                    processing_time_ms=processing_time_ms,
                    query_type=query_type,
                    sources=sources,
                    generated_sql=generated_sql,
                )
            except Exception as e:
                logger.error(f"Background DB save failed: {e}")

        # Start background thread (don't wait for completion)
        thread = threading.Thread(target=_save_in_thread, daemon=True)
        thread.start()

    @logfire.instrument("ChatService.chat")
    def chat(self, request: ChatRequest) -> ChatResponse:
        """Process chat request with ReAct agent.

        Args:
            request: Chat request with query and parameters

        Returns:
            Chat response with answer, reasoning trace, and tools used

        Raises:
            ValidationError: If request is invalid
            IndexNotFoundError: If index not loaded
            LLMError: If LLM call fails
        """
        start_time = time.time()

        # Sanitize query (security: XSS, injection prevention)
        query = sanitize_query(request.query)

        # Build conversation history
        conversation_history = ""
        if request.conversation_id:
            conversation_history = self._build_conversation_context(
                request.conversation_id, request.turn_number
            )
            if conversation_history:
                logger.info(
                    f"Including conversation history ({request.turn_number - 1} previous turns)"
                )

        # Run ReAct agent (cached instance)
        logger.info(f"Running ReAct agent for query: '{query[:100]}'")
        agent = self.agent

        try:
            result = agent.run(
                question=query, conversation_history=conversation_history
            )

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            # Extract results directly from structured tool_results (no string parsing!)
            tool_results = result.get("tool_results", {})

            # Extract SQL results (both query and data)
            sql_result = tool_results.get("query_nba_database", {})
            generated_sql = sql_result.get("sql", "")
            sql_results = sql_result.get("results")  # Actual SQL data rows

            # Extract vector search results
            vector_result = tool_results.get("search_knowledge_base", {})
            vector_sources = vector_result.get("results", [])

            # Convert vector sources to SearchResult objects
            sources = []
            if vector_sources:
                for src in vector_sources:
                    sources.append(SearchResult(
                        text=src.get("text", ""),
                        score=src.get("score", 0.0),
                        source=src.get("source", "unknown"),
                        metadata=src.get("metadata", {})
                    ))

            # Extract visualization directly
            viz_result = tool_results.get("create_visualization", {})
            visualization = None
            if viz_result and viz_result.get("plotly_json"):
                visualization = Visualization(
                    pattern="agent_generated",
                    viz_type=viz_result.get("chart_type", "unknown"),
                    plot_json=viz_result["plotly_json"],
                    plot_html=viz_result.get("plotly_html", ""),
                )

            # Build response
            response = ChatResponse(
                answer=result["answer"],
                query=query,
                sources=sources,  # Vector search sources from agent
                processing_time_ms=processing_time_ms,
                model=self.model,
                conversation_id=request.conversation_id,
                turn_number=request.turn_number,
                generated_sql=generated_sql,
                sql_results=sql_results,  # SQL data rows from agent
                visualization=visualization,
                query_type="agent",
                reasoning_trace=result.get("reasoning_trace", []),
                tools_used=result.get("tools_used", []),
            )

            # Save interaction asynchronously (non-blocking)
            if request.conversation_id:
                self._save_interaction_async(
                    query=query,
                    response=result["answer"],
                    conversation_id=request.conversation_id,
                    turn_number=request.turn_number,
                    processing_time_ms=processing_time_ms,
                    query_type="agent",
                    sources=sources,  # Actual vector sources
                    generated_sql=generated_sql,
                )

            logger.info(
                f"Agent completed in {processing_time_ms:.0f}ms "
                f"({result.get('total_steps', 0)} steps, "
                f"tools: {', '.join(result.get('tools_used', []))})"
            )

            return response

        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            raise LLMError(f"Agent failed: {str(e)}") from e
