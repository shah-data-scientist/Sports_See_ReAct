"""
FILE: chat.py
STATUS: Active
RESPONSIBILITY: Hybrid RAG pipeline (SQL + Vector Search) orchestration service
LAST MAJOR UPDATE: 2026-02-12
MAINTAINER: Shahu
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar

# LAZY IMPORTS: Heavy modules are imported on-demand, not at module load time
# This prevents 30-second startup hangs in Streamlit
# Modules are imported inside functions/methods that actually use them
_lazy_imports_initialized = False
genai = None
ClientError = None
EmbeddingService = None
QueryClassifier = None
QueryType = None
ClassificationResult = None
QueryExpander = None
VisualizationService = None
NBAGSQLTool = None


def _initialize_lazy_imports():
    """Initialize all heavy imports on first use."""
    global _lazy_imports_initialized, genai, ClientError, EmbeddingService
    global QueryClassifier, QueryType, ClassificationResult, QueryExpander, VisualizationService, NBAGSQLTool

    if _lazy_imports_initialized:
        return

    # Import heavy modules (only happens once)
    from google import genai as genai_module
    from google.genai.errors import ClientError as ClientErrorModule
    from src.services.embedding import EmbeddingService as EmbeddingServiceModule
    from src.services.query_classifier import ClassificationResult as ClassificationResultModule
    from src.services.query_classifier import QueryClassifier as QueryClassifierModule
    from src.services.query_classifier import QueryType as QueryTypeModule
    from src.services.query_expansion import QueryExpander as QueryExpanderModule
    from src.services.visualization_service import VisualizationService as VisualizationServiceModule
    from src.tools.sql_tool import NBAGSQLTool as NBAGSQLToolModule

    genai = genai_module
    ClientError = ClientErrorModule
    EmbeddingService = EmbeddingServiceModule
    QueryClassifier = QueryClassifierModule
    QueryType = QueryTypeModule
    ClassificationResult = ClassificationResultModule
    QueryExpander = QueryExpanderModule
    VisualizationService = VisualizationServiceModule
    NBAGSQLTool = NBAGSQLToolModule

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

T = TypeVar('T')


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
            # Check if this is a rate limit error (429)
            error_str = str(e)
            is_rate_limit = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str

            if not is_rate_limit:
                # Not a rate limit error, raise immediately
                logger.error("Non-rate-limit Gemini API error: %s", e)
                raise LLMError(f"LLM API error: {e}") from e

            if attempt >= max_retries:
                # Exhausted all retries
                logger.error(
                    "Rate limit error after %d retries: %s",
                    max_retries,
                    e
                )
                raise LLMError(
                    f"Rate limit exceeded after {max_retries} retries. "
                    "Please try again in a few moments."
                ) from e

            # Wait with exponential backoff
            wait_time = min(delay, max_delay)
            logger.warning(
                "Rate limit hit (attempt %d/%d), retrying in %.1fs: %s",
                attempt + 1,
                max_retries + 1,
                wait_time,
                error_str[:100]
            )
            time.sleep(wait_time)
            delay *= 2


# System prompt templates
# Phase 12 improvements: Query-type-specific prompts with mandatory data usage
# - SYSTEM_PROMPT_TEMPLATE: Default/fallback for general queries
# - SQL_ONLY_PROMPT: Force extraction of SQL results (COUNT/AVG/SUM)
# - HYBRID_PROMPT: Mandate blending of SQL stats + vector context
# - CONTEXTUAL_PROMPT: For qualitative analysis with citations

# Default prompt (fallback for general queries)
# Phase 12C: Answer relevancy fix - direct, focused instructions
# Phase 13: Add source grounding to prevent hallucination
SYSTEM_PROMPT_TEMPLATE = """You are '{app_name} Analyst AI', an expert NBA sports analysis assistant with a professional yet personable voice—insightful, authoritative, but never boring.

{conversation_history}

CONTEXT:
---
{context}
---

USER QUESTION:
{question}

CRITICAL INSTRUCTIONS - SYNTHESIS & VOICE:

**MANDATORY: You MUST ONLY answer based on the provided CONTEXT above.**

1. **SYNTHESIZE, don't list**: Weave facts together into flowing paragraphs. Use transitions (however, moreover, interestingly, etc.). Paint a picture, don't create a shopping list.

2. **Add personality**: Be professional but approachable. A touch of wit is welcome—help readers connect with the content. Show enthusiasm for the sport.

3. **Remove inline citations**: NO "[Source: X]" within text. Write naturally. List all sources ONCE at the very end of your message.

4. **Structure for clarity**:
   - Start with the key insight or answer
   - Build with supporting details
   - Use transitions between ideas
   - End with interesting implications or takeaways

5. **Citation format at message end**:
   (Place on separate line at bottom, smaller text style)
   Sources: Source1, Source2, Source3

6. Resolve pronouns using conversation history (he, his, them)

7. Respond in English

FORBIDDEN: Do NOT provide information from general knowledge not in the CONTEXT above.

ANSWER:"""

# SQL-only prompt: Force extraction of statistical data
# Phase 12C: Answer relevancy fix - clear, direct extraction
# Phase 13: Add source grounding for statistical context
SQL_ONLY_PROMPT = """You are '{app_name} Analyst AI', an expert NBA sports analysis assistant with a professional yet engaging voice. You excel at making statistics tell a story.

{conversation_history}

STATISTICAL DATA (FROM SQL DATABASE):
---
{context}
---

USER QUESTION:
{question}

CRITICAL INSTRUCTIONS - SYNTHESIS & PRESENTATION:

**ANSWER THE QUESTION USING THE STATISTICAL DATA ABOVE**

1. **Tell the story with data**: Don't just list numbers. Synthesize them. "The top 5 scorers..." not "1. Player A scored X, 2. Player B scored Y..."

2. **Add context & perspective**:
   - What do these numbers mean?
   - Why do they matter?
   - What's the bigger picture?
   - Use professional analysis tone with light wit where appropriate
   - **Tone for EXACT statistics** (Issue #6 Fix): Use DEFINITIVE language ("Player X scored 30 points", NOT "appears to have scored around 30 points")
   - Reserve hedging ("possibly", "approximately", "seems to") ONLY for comparisons, projections, or interpretations

3. **Format for readability**:
   - Present numbers clearly (bullet points or flowing text)
   - Use transitions between ideas
   - Build toward insights, not just facts
   - **Top-N Queries** (Issue #4 Fix): If question asks for "top N" or "list of N items":
     * FIRST: Present the COMPLETE list of ALL N items with their stats
     * THEN: Add analysis/context AFTER the complete list
     * CRITICAL: Complete the full list BEFORE adding commentary

4. **Citation format**:
   - NO inline citations in text
   - List sources ONCE at the very end on separate line:
   - "Sources: Database Name, Source2, Source3"

5. Resolve pronouns using conversation history (he, his, them)
6. Respond in English

MANDATORY: Only use the STATISTICAL DATA provided.
Do NOT add general knowledge or information not provided.

**MANDATORY RESPONSE RULES** (Issue #5 Fix - NEVER DECLINE):
1. ALWAYS check the STATISTICAL DATA section FIRST before responding
2. If data EXISTS in STATISTICAL DATA → PRESENT IT IMMEDIATELY (no hedging, no apologies, no "I can't...")
3. If SQL returned results for a FILTERED query → The filter criteria were SATISFIED, present results confidently
4. If data is TRULY MISSING (0 rows or empty) → State clearly: "This specific data is not available in the database."

**FORBIDDEN PHRASES when data IS present in STATISTICAL DATA:**
❌ "I can't provide..."
❌ "I'm unable to find..."
❌ "I cannot give you..."
❌ "The data doesn't include..." (when SQL successfully returned filtered results)
❌ "The database does not include..." (when SQL succeeded with WHERE clauses)
❌ "I don't have access to..."

**REQUIRED FORMAT when data IS present:**
✅ "Based on the statistics: [answer with numbers]"
✅ "[Direct answer]. According to the data: [details]"
✅ "The data shows [answer]."
✅ "X players meet this criteria: [list them]" (for filtered queries)

Examples:
- Question: "How many players have more than 500 assists?"
- STATISTICAL DATA: "Found 15 matching records: ..."
- ✅ CORRECT: "15 players have more than 500 assists this season. The leaders include..."
- ❌ WRONG: "I can't provide a specific number..."

- Question: "Find players between 25-30 years old with 1500+ points"
- STATISTICAL DATA: "Found 14 matching records: 1. name: Shai Gilgeous-Alexander, 2. name: Jayson Tatum..."
- ✅ CORRECT: "14 players between 25 and 30 years old have scored more than 1500 points this season: Shai Gilgeous-Alexander, Jayson Tatum..."
- ❌ WRONG: "The database does not include age or points scored" (SQL ALREADY FILTERED by these!)

ANSWER:"""

# Hybrid prompt: Mandate blending of SQL + vector
# Phase 18: Enhanced faithfulness with numbered citations (2026-02-13)
HYBRID_PROMPT = """You are '{app_name} Analyst AI', an expert NBA sports analysis assistant with a professional, engaging voice. You synthesize statistics and insights into compelling narratives.

{conversation_history}

STATISTICAL DATA (FROM SQL DATABASE):
---
{sql_context}
---

CONTEXTUAL KNOWLEDGE (Analysis & Insights):
---
{vector_context}
---

USER QUESTION:
{question}

CRITICAL INSTRUCTIONS - FAITHFULNESS & SYNTHESIS:

**1. FAITHFULNESS (HIGHEST PRIORITY):**
   - **ONLY use information from the two sources above** (Statistical Data + Contextual Knowledge)
   - **FORBIDDEN:** Do NOT add information from general knowledge or external sources
   - Database statistics are exact - cite them precisely
   - If sources conflict: Present both perspectives with separate citations
   - If information is missing: State explicitly what is not in the sources

**2. ANSWER RELEVANCY:**
   - **Start with direct answer** combining both data sources in first sentence
   - Statistics answer the WHAT and numbers
   - Context explains the WHY, HOW, and implications
   - Stay focused on the user's question

**3. SYNTHESIS (Required):**
   - **YOU MUST USE BOTH DATA SOURCES - WEAVE THEM TOGETHER**
   - Don't say "Stat X" then "Context Y" separately
   - Blend into flowing, coherent paragraphs
   - Example: "Player X averaged 28.5 PPG[1], showcasing the efficiency that fans praised throughout the playoffs[2]."

**4. NUMBERED CITATIONS (Required):**
   - Add [1], [2], [3] etc. after statements
   - Number sources sequentially (SQL Database = [1], then documents = [2], [3], etc.)
   - Example: "According to statistics, Player X averaged 28.5 PPG[1]. Fans praised his efficiency[2]."

**5. COMPLETENESS:**
   - If sources partially answer: Provide what you can, acknowledge gaps
   - **Do NOT fully decline if sources have ANY relevant information**

**6. SOURCE LIST (Required at end):**
   After your answer, add:

   Sources:
   1. NBA Statistics Database
   2. [Second source name]
   3. [Third source name]

7. Add personality with transitions: "Interestingly", "Moreover", "However"
8. Resolve pronouns using conversation history (he, his, them)
9. Respond in English

EXAMPLE (GOOD - Faithful + Synthesized + Cited):
"LeBron James scored 1,708 points this season[1], continuing his role as one of the league's elite scorers. His offensive toolkit is remarkably diverse—he attacks the basket with power, but also possesses an underrated three-point shot[2]. This versatility keeps defenders guessing and creates opportunities for his teammates[2]. The consistency he brings year after year is a testament to his professionalism and basketball IQ[3].

Sources:
1. NBA Statistics Database
2. ESPN Analysis
3. Basketball Community Discussion"

YOUR ANSWER (with numbered citations [1], [2], etc.):"""

# Contextual prompt: For qualitative analysis and biographical info
# Phase 12C: Answer relevancy fix - focused qualitative analysis
# Phase 13: Add source grounding to prevent hallucination
# Phase 17: Enhanced for biographical queries to synthesize stats + context
# Phase 18: Enhanced faithfulness with numbered citations (2026-02-13)
CONTEXTUAL_PROMPT = """You are '{app_name} Analyst AI', an expert NBA sports analysis assistant with a professional, personable voice. You excel at synthesizing opinions, insights, and biographical information into engaging narratives.

{conversation_history}

CONTEXTUAL KNOWLEDGE (Opinions, Analysis, Discussions, Biographical Info):
---
{context}
---

USER QUESTION:
{question}

CRITICAL INSTRUCTIONS - FAITHFULNESS & ANSWER QUALITY:

**1. FAITHFULNESS (HIGHEST PRIORITY):**
   - **ONLY use information from the CONTEXTUAL KNOWLEDGE above**
   - **FORBIDDEN:** Do NOT add information from general knowledge or external sources
   - **If sources conflict:** Present both perspectives with separate citations
   - **If information is missing:** Explicitly state: "The sources do not provide information about [aspect]"

**2. ANSWER RELEVANCY:**
   - **Start with direct answer** in the first sentence
   - Then provide supporting details from sources
   - Stay focused on the user's question - do not drift off-topic

**3. NUMBERED CITATIONS (Required):**
   - Add [1], [2], [3] etc. after each statement that uses source information
   - Example: "Player X averaged 28 points in the playoffs[1]. Fans praised his efficiency[2]."
   - Number sources sequentially as you use them (first source = [1], second = [2], etc.)

**4. COMPLETENESS:**
   - If sources partially answer the question:
     * Answer what you CAN from the sources
     * Acknowledge gaps: "The sources provide information about X but not about Y"
   - **Do NOT fully decline if sources have ANY relevant information**

**5. SYNTHESIS (Not listing):**
   - Weave facts and opinions into cohesive narrative
   - Use transitions: "Interestingly", "Moreover", "However"
   - For biographical queries: Include both narrative AND statistics if available
   - Add personality but stay grounded in sources

**6. SOURCE LIST (Required at end):**
   After your answer, add a blank line and list sources:

   Sources:
   1. [First source name]
   2. [Second source name]
   3. [Third source name]

7. Resolve pronouns using conversation history (he, his, them)
8. Respond in English

ANSWER (with numbered citations [1], [2], etc.):"""


class ChatService:
    """Service for RAG-powered chat functionality.

    Orchestrates the complete RAG pipeline with proper error handling
    and dependency injection.

    Attributes:
        vector_store: Repository for vector search
        embedding_service: Service for generating embeddings
    """

    def __init__(
        self,
        vector_store: Optional[Any] = None,  # VectorStoreRepository
        embedding_service: Optional[Any] = None,  # EmbeddingService
        feedback_repository: Optional[Any] = None,  # FeedbackRepository
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_sql: bool = True,
        enable_vector_fallback: bool = True,
        conversation_history_limit: int = 5,
    ):
        """Initialize chat service.

        Args:
            vector_store: Vector store repository (created if not provided)
            embedding_service: Embedding service (created if not provided)
            feedback_repository: Feedback repository for conversation history (created if not provided)
            api_key: Google API key (default from settings)
            model: Chat model name (default from settings)
            enable_sql: Enable SQL tool for statistical queries (default: True)
            enable_vector_fallback: Enable fallback to vector search when SQL fails (default: True)
            conversation_history_limit: Number of previous turns to include in context (default: 5)
        """
        # Initialize lazy imports on first ChatService instantiation
        _initialize_lazy_imports()

        self._api_key = api_key or settings.google_api_key
        self._model = model or settings.chat_model
        self._temperature = settings.temperature
        self._enable_sql = enable_sql
        self._enable_vector_fallback = enable_vector_fallback
        self._conversation_history_limit = conversation_history_limit

        # Dependencies (lazy initialization)
        self._vector_store = vector_store
        self._embedding_service = embedding_service
        self._feedback_repository = feedback_repository
        self._client: Optional[Any] = None  # genai.Client
        self._sql_tool: Optional[Any] = None  # NBAGSQLTool
        self._query_classifier: Optional[Any] = None  # QueryClassifier
        self._query_expander: Optional[Any] = None  # QueryExpander
        self._visualization_service: Optional[Any] = None  # VisualizationService

    @property
    def vector_store(self) -> VectorStoreRepository:
        """Get vector store repository (lazy initialization)."""
        if self._vector_store is None:
            self._vector_store = VectorStoreRepository()
            self._vector_store.load()
        return self._vector_store

    @property
    def embedding_service(self) -> Any:  # EmbeddingService
        """Get embedding service (lazy initialization)."""
        if self._embedding_service is None:
            # EmbeddingService uses Mistral - don't pass Google API key!
            # Let it use settings.mistral_api_key by default
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    @property
    def client(self) -> Any:  # genai.Client
        """Get Gemini client (lazy initialization)."""
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    @property
    def model(self) -> str:
        """Get chat model name."""
        return self._model

    @property
    def sql_tool(self) -> Optional[Any]:  # NBAGSQLTool
        """Get SQL tool (lazy initialization)."""
        if not self._enable_sql:
            return None
        if self._sql_tool is None:
            try:
                self._sql_tool = NBAGSQLTool(google_api_key=self._api_key)
                logger.info("SQL tool initialized successfully")
            except Exception as e:
                logger.warning(f"SQL tool initialization failed: {e}")
                self._sql_tool = None
        return self._sql_tool

    @property
    def query_classifier(self) -> Any:  # QueryClassifier
        """Get query classifier (lazy initialization)."""
        if self._query_classifier is None:
            self._query_classifier = QueryClassifier()
        return self._query_classifier

    @property
    def query_expander(self) -> Any:  # QueryExpander
        """Get query expander (lazy initialization)."""
        if self._query_expander is None:
            self._query_expander = QueryExpander()
        return self._query_expander

    @property
    def visualization_service(self) -> Any:  # VisualizationService
        """Get visualization service (lazy initialization)."""
        if self._visualization_service is None:
            self._visualization_service = VisualizationService()
        return self._visualization_service

    @property
    def feedback_repository(self) -> FeedbackRepository:
        """Get feedback repository (lazy initialization)."""
        if self._feedback_repository is None:
            self._feedback_repository = FeedbackRepository()
        return self._feedback_repository

    @property
    def is_ready(self) -> bool:
        """Check if service is ready (index loaded)."""
        return self.vector_store.is_loaded

    def _format_superscript_citations(self, answer: str) -> str:
        """Convert [1], [2], etc. to HTML superscript for better readability.

        Example:
          Input:  "Player X scored 30 points[1]. He was efficient[2]."
          Output: "Player X scored 30 points<sup>1</sup>. He was efficient<sup>2</sup>."

        Args:
            answer: Raw LLM response with [1], [2], etc. markers

        Returns:
            Formatted answer with <sup> tags
        """
        import re

        # Pattern: [1], [2], [10], etc. (handles multi-digit)
        pattern = r'\[(\d+)\]'

        # Replace [1] → <sup>1</sup>
        formatted = re.sub(pattern, r'<sup>\1</sup>', answer)

        return formatted

    @staticmethod
    def _remove_excessive_hedging(answer: str) -> str:
        """Remove excessive hedging language from statistical responses (Issue #6 Fix).

        Removes weak qualifiers when presenting exact statistics:
        - "appears to have scored" → "scored"
        - "seems to be around" → "is"
        - "approximately X points" → "X points"

        Args:
            answer: LLM response

        Returns:
            Response with hedging removed
        """
        import re

        # Patterns to remove (hedging phrases before facts)
        hedging_patterns = [
            # "appears/seems to" phrases
            (r'\b(appears to have|seems to have|appears to be|seems to be)\b', ''),
            # Numeric qualifiers
            (r'\b(approximately|roughly|around|about)\s+(\d+)', r'\2'),
            # Possibility markers
            (r'\b(possibly|probably|likely|perhaps)\s+', ''),
            # Modal verbs
            (r'\b(may have|might have|could have)\b', 'has'),
            (r'\b(may be|might be|could be)\b', 'is'),
            # "I think/believe" subjective markers
            (r'\b(I think|I believe|I suspect)\s+', ''),
            # "It seems/appears that" constructions
            (r'\b(it seems that|it appears that|it looks like)\s+', ''),
            # "kind of/sort of" qualifiers
            (r'\b(kind of|sort of)\s+', ''),
            # "tend to/tends to" patterns
            (r'\b(tend to|tends to)\s+', ''),
            # "generally/usually" when presenting specific stats
            (r'\b(generally|usually|typically)\s+(scored|averaged|had)', r'\2'),
        ]

        result = answer
        for pattern, replacement in hedging_patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        # Clean up double spaces
        result = re.sub(r'\s{2,}', ' ', result)

        return result

    def _assess_source_quality(self, sources: List[SearchResult], min_acceptable_score: float = 50.0) -> Dict[str, Any]:
        """Assess if retrieved sources are sufficient quality to answer confidently.

        Args:
            sources: Retrieved search results
            min_acceptable_score: Minimum similarity score to consider "good" (default: 50%)

        Returns:
            Dict with:
              - has_good_sources: bool (at least one source above threshold)
              - avg_score: float (average similarity across all sources)
              - good_count: int (number of sources above threshold)
              - total_count: int (total sources retrieved)
              - quality_level: str ("high", "medium", "low", "none")
        """
        if not sources:
            return {
                "has_good_sources": False,
                "avg_score": 0.0,
                "good_count": 0,
                "total_count": 0,
                "quality_level": "none",
            }

        scores = [s.score for s in sources]
        avg_score = sum(scores) / len(sources)
        good_count = sum(1 for s in scores if s >= min_acceptable_score)

        # Determine quality level
        if avg_score >= 65.0 and good_count >= len(sources) * 0.8:
            quality_level = "high"  # 80%+ sources are good, avg high
        elif avg_score >= 50.0 or good_count >= len(sources) * 0.5:
            quality_level = "medium"  # 50%+ sources are acceptable
        else:
            quality_level = "low"  # Majority of sources are poor matches

        return {
            "has_good_sources": good_count > 0,
            "avg_score": avg_score,
            "good_count": good_count,
            "total_count": len(sources),
            "quality_level": quality_level,
        }

    def ensure_ready(self) -> None:
        """Ensure service is ready.

        Raises:
            IndexNotFoundError: If index is not loaded
        """
        if not self.is_ready:
            # Try to load
            if not self.vector_store.load():
                raise IndexNotFoundError("Vector index not loaded. Run indexer first.")

    def _build_conversation_context(self, conversation_id: str, current_turn: int) -> str:
        """Build conversation history context for the prompt.

        Args:
            conversation_id: Conversation ID
            current_turn: Current turn number

        Returns:
            Formatted conversation history string, or empty string if no history
        """
        # Get previous messages (excluding current turn)
        messages = self.feedback_repository.get_messages_by_conversation(conversation_id)

        # Filter to only previous turns (not including current)
        previous_messages = [msg for msg in messages if msg.turn_number and msg.turn_number < current_turn]

        # Limit to last N turns
        if len(previous_messages) > self._conversation_history_limit:
            previous_messages = previous_messages[-self._conversation_history_limit :]

        # No history to show
        if not previous_messages:
            return ""

        # Format history
        history_lines = ["CONVERSATION HISTORY:"]
        for msg in previous_messages:
            history_lines.append(f"User: {msg.query}")
            history_lines.append(f"Assistant: {msg.response}")

        history_lines.append("---\n")
        return "\n".join(history_lines)

    @staticmethod
    @staticmethod
    def _rewrite_biographical_for_sql(query: str) -> str:
        """Rewrite biographical queries to fetch comprehensive player stats.

        "Who is LeBron?" → "Show name, team, age, points, rebounds, assists,
        steals, blocks, field goal percentage, games played for LeBron"

        This ensures the SQL tool generates a query that fetches full stats
        instead of just SELECT name.
        """
        import re

        # Extract player/team name from query
        q = query.strip()
        name = None

        # Pattern: "Who is [Name]?" or "Tell me about [Name]"
        for pattern in [
            r"(?:who is|who's|tell me about|info on|about)\s+(.+?)[\?\.]?$",
        ]:
            match = re.search(pattern, q, re.IGNORECASE)
            if match:
                name = match.group(1).strip().rstrip("?.")
                break

        if not name:
            # Fallback: use the whole query
            name = q

        return (
            f"Show name, team, age, games played, points, rebounds, assists, "
            f"steals, blocks, field goal percentage, three point percentage, "
            f"free throw percentage for {name}"
        )

    @staticmethod
    def _is_followup_query(query: str) -> bool:
        """Detect if a query is a conversational follow-up requiring context.

        Checks for pronouns, short fragments, corrections, and other
        indicators that the query depends on previous conversation turns.

        Args:
            query: User query string

        Returns:
            True if query appears to be a follow-up
        """
        q = query.strip().lower()
        words = q.split()

        # Very short queries (< 5 words) are likely follow-ups
        if len(words) <= 4 and not any(
            kw in q for kw in ["top", "best", "worst", "who scored", "list", "show all"]
        ):
            return True

        # Pronouns referencing previous context (word-boundary aware)
        pronoun_patterns = [
            "his ", "her ", "their ", "its ", "he ", "she ", "they ",
            "him ", "them ", "that player", "that team", "the same",
        ]
        q_padded = f" {q} "
        if any(f" {p}" in q_padded for p in pronoun_patterns):
            return True

        # Follow-up phrases
        followup_phrases = [
            "what about", "and what", "how about", "how does that",
            "compare him", "compare her", "compare them",
            "what else", "anything else", "tell me more",
            "actually", "i meant", "no i mean", "sorry i meant",
            "only from", "just the", "sort them", "filter",
            "now show", "now tell", "and also", "but what",
        ]
        if any(q.startswith(p) or f" {p}" in q for p in followup_phrases):
            return True

        return False

    def _rewrite_followup_query(
        self, query: str, conversation_history: str
    ) -> str:
        """Rewrite a follow-up query into a self-contained question using conversation history.

        Uses Gemini to resolve pronouns, references, and implicit context
        from the conversation history.

        Args:
            query: The follow-up query (e.g., "What about his assists?")
            conversation_history: Formatted conversation history string

        Returns:
            Rewritten self-contained query, or original query if rewriting fails
        """
        rewrite_prompt = (
            "You are a query rewriter. Given a conversation history and a follow-up question, "
            "rewrite the follow-up into a COMPLETE, SELF-CONTAINED question that can be understood "
            "without any prior context.\n\n"
            "Rules:\n"
            "- Replace all pronouns (he, his, she, her, they, them, it) with the actual entity names\n"
            "- Expand short fragments into full questions\n"
            "- Preserve the user's intent exactly\n"
            "- Keep the rewritten query concise (one sentence)\n"
            "- Output ONLY the rewritten question, nothing else\n\n"
            f"{conversation_history}\n"
            f"Follow-up question: {query}\n\n"
            "Rewritten question:"
        )

        try:
            logger.info("Rewriting follow-up query using conversation context")

            def _call_llm():
                return self.client.models.generate_content(
                    model=self._model,
                    contents=rewrite_prompt,
                    config={
                        "temperature": 0.0,
                        "max_output_tokens": 150,
                    },
                )

            response = retry_with_exponential_backoff(_call_llm)

            if response.text:
                rewritten = response.text.strip().strip('"').strip("'")
                # Sanity check: rewritten query should not be empty or too long
                if 3 < len(rewritten) < 500:
                    logger.info(f"Query rewritten: '{query}' → '{rewritten}'")
                    return rewritten

            logger.warning("Query rewriting returned empty result, using original query")
            return query

        except Exception as e:
            logger.warning(f"Query rewriting failed ({e}), using original query")
            return query

    def _save_interaction(
        self,
        query: str,
        response: str,
        sources: list[SearchResult],
        processing_time_ms: float,
        conversation_id: str | None,
        turn_number: int | None,
    ) -> None:
        """Save a chat interaction to the database for conversation history.

        Args:
            query: User query
            response: Generated response
            sources: Search result sources
            processing_time_ms: Processing time in milliseconds
            conversation_id: Conversation ID (optional)
            turn_number: Turn number in conversation (optional)
        """
        try:
            source_texts = [s.source for s in sources] if sources else []
            interaction = ChatInteractionCreate(
                query=query,
                response=response,
                sources=source_texts,
                processing_time_ms=int(processing_time_ms),
                conversation_id=conversation_id,
                turn_number=turn_number,
            )
            self.feedback_repository.save_interaction(interaction)
            logger.debug("Interaction saved for conversation %s turn %s", conversation_id, turn_number)
        except Exception as e:
            # Don't fail the request if interaction saving fails
            logger.warning(f"Failed to save interaction: {e}")

    def _format_sql_results(self, sql_results: list[dict]) -> str:
        """Format SQL results with special handling for scalar values (COUNT, AVG, SUM).

        Args:
            sql_results: List of result dictionaries from SQL query

        Returns:
            Formatted string for LLM prompt
        """
        if not sql_results:
            return "No results found."

        num_rows = len(sql_results)

        # SPECIAL CASE 1: Single scalar result (COUNT, AVG, SUM, MAX, MIN)
        if num_rows == 1 and len(sql_results[0]) == 1:
            key, value = list(sql_results[0].items())[0]
            key_lower = key.lower()

            # Format based on aggregation type
            if "count" in key_lower:
                return f"COUNT Result: {value} (total number of records matching the criteria)"
            elif "avg" in key_lower or "average" in key_lower:
                return f"AVERAGE Result: {value:.2f}"
            elif "sum" in key_lower or "total" in key_lower:
                return f"SUM/TOTAL Result: {value}"
            elif "max" in key_lower or "maximum" in key_lower:
                return f"MAXIMUM Result: {value}"
            elif "min" in key_lower or "minimum" in key_lower:
                return f"MINIMUM Result: {value}"
            else:
                return f"Result: {value}"

        # SPECIAL CASE 2: Single record (player/team lookup)
        if num_rows == 1:
            row = sql_results[0]
            row_text = "\n".join(f"  • {k}: {v}" for k, v in row.items())
            return f"Found 1 matching record:\n\n{row_text}"

        # GENERAL CASE: Multiple records (top N, rankings, comparisons)
        formatted_rows = []
        for i, row in enumerate(sql_results[:20], 1):
            row_parts = [f"{k}: {v}" for k, v in row.items()]
            formatted_rows.append(f"{i}. {', '.join(row_parts)}")

        result = "\n".join(formatted_rows)

        if num_rows > 20:
            result += f"\n\n(Showing top 20 of {num_rows} total results)"
            return f"Found {num_rows} matching records (showing top 20):\n\n{result}"
        else:
            return f"Found {num_rows} matching records:\n\n{result}"

    @logfire.instrument("ChatService.search {query=}")
    def search(
        self,
        query: str,
        k: int | None = None,
        min_score: float | None = None,
        max_expansions: int | None = None,
    ) -> list[SearchResult]:
        """Search for relevant documents with smart metadata filtering.

        Args:
            query: Search query
            k: Number of results (default from settings)
            min_score: Minimum similarity score (0-1)
            max_expansions: Pre-computed expansion limit from ClassificationResult

        Returns:
            List of search results

        Raises:
            ValidationError: If query is invalid
            IndexNotFoundError: If index not loaded
            SearchError: If search fails
        """
        # Validate inputs
        query = sanitize_query(query)
        k = k or settings.search_k
        validate_search_params(k, min_score)

        self.ensure_ready()

        # PHASE 7: Expand query for better keyword matching (replaces metadata filtering)
        # Use pre-computed max_expansions from QueryClassifier
        if max_expansions:
            expanded_query = self.query_expander.expand_weighted(query, max_expansions=max_expansions)
        else:
            expanded_query = self.query_expander.expand_smart(query)

        if expanded_query != query:
            logger.info(f"Expanded query: '{query}' -> '{expanded_query[:100]}...'")
            if max_expansions:
                logger.info(f"  (using max_expansions={max_expansions})")

        # PHASE 6 metadata filtering DISABLED - caused false negatives
        # (Only 3 chunks tagged as player_stats, all were headers not actual data)
        # Query expansion provides better precision without excluding relevant chunks

        # Generate query embedding using expanded query
        query_embedding = self.embedding_service.embed_query(expanded_query)

        # Search WITHOUT metadata filters (Phase 7 approach)
        # Phase 13: Pass query_text for 3-signal hybrid scoring (cosine + BM25 + metadata)
        results = self.vector_store.search(
            query_embedding=query_embedding,
            k=k,
            min_score=min_score,
            metadata_filters=None,
            query_text=expanded_query,
        )

        # Convert to response models
        return [
            SearchResult(
                text=chunk.text,
                score=score,
                source=chunk.metadata.get("source", "unknown"),
                metadata={
                    k: v
                    for k, v in chunk.metadata.items()
                    if k != "source" and isinstance(v, str | int | float)
                },
            )
            for chunk, score in results
        ]

    @logfire.instrument("ChatService.generate_response")
    def generate_response(
        self,
        query: str,
        context: str,
        conversation_history: str = "",
        prompt_template: str | None = None,
    ) -> str:
        """Generate LLM response with context.

        Args:
            query: User query
            context: Retrieved context
            conversation_history: Conversation history context (optional)
            prompt_template: Optional custom prompt template (for Phase 8 testing)

        Returns:
            Generated response text

        Raises:
            LLMError: If LLM call fails
        """
        # Build prompt (use custom template if provided, otherwise default)
        template = prompt_template if prompt_template is not None else SYSTEM_PROMPT_TEMPLATE
        prompt = template.format(
            app_name=settings.app_name,
            conversation_history=conversation_history,
            context=context,
            question=query,
        )

        try:
            logger.info("Calling Gemini LLM with model %s", self._model)

            # Wrap API call with retry logic for rate limit handling
            def _call_llm():
                return self.client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config={
                        "temperature": self._temperature,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 2048,
                    },
                )

            response = retry_with_exponential_backoff(_call_llm)

            if response.text:
                return response.text

            logger.warning("Gemini returned no text")
            return "I could not generate a response."

        except Exception as e:
            logger.error("LLM call failed: %s", e)
            raise LLMError(f"LLM call failed: {e}") from e

    @logfire.instrument("ChatService.generate_response_hybrid")
    def generate_response_hybrid(
        self,
        query: str,
        sql_context: str,
        vector_context: str,
        conversation_history: str = "",
    ) -> str:
        """Generate LLM response for hybrid queries (SQL + Vector).

        Args:
            query: User query
            sql_context: SQL query results context
            vector_context: Vector search context
            conversation_history: Conversation history context (optional)

        Returns:
            Generated response text

        Raises:
            LLMError: If LLM call fails
        """
        # Build prompt with separate SQL and vector contexts
        prompt = HYBRID_PROMPT.format(
            app_name=settings.app_name,
            conversation_history=conversation_history,
            sql_context=sql_context,
            vector_context=vector_context,
            question=query,
        )

        try:
            logger.info("Calling Gemini LLM with model %s (hybrid query)", self._model)

            # Wrap API call with retry logic for rate limit handling
            def _call_llm():
                return self.client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config={
                        "temperature": self._temperature,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 2048,
                    },
                )

            response = retry_with_exponential_backoff(_call_llm)

            if response.text:
                return response.text

            logger.warning("Gemini returned no text")
            return "I could not generate a response."

        except Exception as e:
            logger.error("LLM call failed: %s", e)
            raise LLMError(f"LLM call failed: {e}") from e

    @logfire.instrument("ChatService.chat")
    def chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request through hybrid RAG pipeline (SQL + Vector Search).

        Args:
            request: Chat request with query and parameters

        Returns:
            Chat response with answer and sources

        Raises:
            ValidationError: If request is invalid
            IndexNotFoundError: If index not loaded
            SearchError: If search fails
            LLMError: If LLM call fails
        """
        start_time = time.time()

        # Sanitize query
        query = sanitize_query(request.query)

        # ──── PHASE 15: Detect simple greetings (don't need RAG search) ────
        # Examples: "hi", "hello", "thanks", etc. should get simple responses
        if self.query_classifier._is_greeting(query):
            processing_time = (time.time() - start_time) * 1000
            greeting_responses = {
                "hi": "Hi there! Ask me anything about basketball stats, teams, or players.",
                "hello": "Hello! What would you like to know about basketball?",
                "hey": "Hey! Feel free to ask me basketball questions.",
                "thanks": "You're welcome! Feel free to ask more questions.",
                "thank you": "Happy to help! What else can I answer for you?",
                "goodbye": "Goodbye! See you next time!",
                "bye": "See you later!",
            }
            # Find best matching greeting response
            query_lower = query.strip().lower()
            response_text = next(
                (v for k, v in greeting_responses.items() if k in query_lower),
                "Hi! Ask me about basketball!"
            )
            logger.info(f"Detected greeting: '{query}' - returning simple response")
            return ChatResponse(
                answer=response_text,
                query=query,
                sources=[],
                processing_time_ms=int(processing_time),
                model=self.model,
                conversation_id=None,
                turn_number=1,
                query_type="greeting",
            )

        # Build conversation context if conversation_id provided
        conversation_history = ""
        if request.conversation_id:
            conversation_history = self._build_conversation_context(
                request.conversation_id,
                request.turn_number
            )
            if conversation_history:
                logger.info(f"Including conversation history ({request.turn_number - 1} previous turns)")

        # Rewrite follow-up queries to resolve pronouns/references BEFORE classification
        # This ensures the classifier and SQL tool receive a self-contained query
        effective_query = query
        if conversation_history and self._is_followup_query(query):
            effective_query = self._rewrite_followup_query(query, conversation_history)

        # ── Single classify() call returns all query metadata ─────────────────
        # ClassificationResult bundles: query_type, is_biographical, is_greeting, complexity_k
        # This eliminates duplicate _is_biographical() and _estimate_question_complexity() calls.
        if self._enable_sql:
            classification = self.query_classifier.classify(effective_query)
        else:
            classification = ClassificationResult(QueryType.CONTEXTUAL)

        query_type = classification.query_type
        is_biographical = classification.is_biographical
        logger.warning(f"[DEBUG-CLASSIFY] query_type={query_type} ({type(query_type)}), is_biographical={is_biographical}, enable_sql={self._enable_sql}")

        # Adaptive k: use request.k if explicitly set, otherwise use classifier's complexity estimate
        adaptive_k = request.k if request.k and request.k > 0 else classification.complexity_k
        logger.info(f"Using k={adaptive_k} (complexity-based: simple=3, moderate=5, complex=7-9)")

        # Route to appropriate data source(s)
        search_results = []
        sql_failed = False  # Track SQL failure for fallback
        sql_success = False  # Track SQL success
        sql_context = ""
        vector_context = ""
        generated_sql = None  # Track generated SQL for Phase 2 analysis
        sql_result_data = None  # Track SQL results for visualization

        # Statistical query → SQL tool (use effective_query for resolved pronouns)
        if query_type in (QueryType.STATISTICAL, QueryType.HYBRID):
            if self.sql_tool:
                try:
                    # For biographical queries, rewrite to fetch comprehensive stats
                    sql_query_text = effective_query
                    if is_biographical:
                        sql_query_text = self._rewrite_biographical_for_sql(effective_query)
                        logger.info(f"Biographical SQL rewrite: '{effective_query}' → '{sql_query_text}'")

                    logger.info(f"Routing to SQL tool (query_type: {query_type.value})")
                    sql_result = self.sql_tool.query(sql_query_text)

                    # Capture generated SQL for evaluation/analysis
                    if sql_result["sql"]:
                        generated_sql = sql_result["sql"]
                        logger.debug(f"Generated SQL: {generated_sql}")

                    if sql_result["error"]:
                        logger.warning(f"SQL query failed: {sql_result['error']} - falling back to vector search")
                        sql_failed = True
                    elif not sql_result["results"]:
                        logger.warning("SQL query returned no results - falling back to vector search")
                        sql_failed = True
                    else:
                        # Use new _format_sql_results() method with scalar handling
                        sql_context = self._format_sql_results(sql_result["results"])
                        logger.info(f"SQL query returned {len(sql_result['results'])} rows")
                        sql_success = True
                        # Store SQL results for visualization
                        sql_result_data = sql_result["results"]

                except Exception as e:
                    logger.error(f"SQL tool error: {e} - falling back to vector search")
                    sql_failed = True

        # Contextual/Hybrid query → Vector search
        # Also fallback to vector if SQL failed for STATISTICAL queries (when fallback enabled)
        # OR always add vector search for HYBRID queries
        should_use_vector = (
            query_type == QueryType.CONTEXTUAL or
            query_type == QueryType.HYBRID or
            (query_type == QueryType.STATISTICAL and sql_failed and self._enable_vector_fallback)
        )

        if should_use_vector:
            if sql_failed and query_type == QueryType.STATISTICAL:
                logger.info("SQL fallback activated - using vector search for statistical query")
            else:
                logger.info(f"Routing to vector search (query_type: {query_type.value})")

            search_results = self.search(
                query=effective_query,
                k=adaptive_k,
                min_score=request.min_score,
                max_expansions=classification.max_expansions,  # Pass pre-computed expansion limit
            )

            # Format vector search context with quality assessment (Phase 18)
            if search_results:
                # Assess source quality
                quality_assessment = self._assess_source_quality(search_results, min_acceptable_score=50.0)

                # Build quality warning prefix based on level
                quality_prefix = ""
                if quality_assessment["quality_level"] == "low":
                    quality_prefix = (
                        f"⚠️ SOURCE QUALITY WARNING: Retrieved sources have low similarity (avg: {quality_assessment['avg_score']:.1f}%).\n"
                        f"Instructions: If sources contain ANY relevant information, provide a PARTIAL answer starting with: "
                        f"'I have limited information about this topic. Based on the available sources:' "
                        f"Otherwise, respond: 'I do not have sufficient information to answer this question reliably.'\n\n"
                    )
                elif quality_assessment["quality_level"] == "medium":
                    quality_prefix = (
                        f"ℹ️ SOURCE QUALITY: Retrieved sources have moderate similarity (avg: {quality_assessment['avg_score']:.1f}%).\n"
                        f"Instructions: Answer using available information. If aspects are missing, acknowledge: "
                        f"'The sources provide information about X but not about Y.'\n\n"
                    )
                else:  # high quality
                    quality_prefix = (
                        f"✅ SOURCE QUALITY: Retrieved sources have high similarity (avg: {quality_assessment['avg_score']:.1f}%).\n"
                        f"Instructions: Answer confidently using the high-quality sources.\n\n"
                    )

                logger.info(f"Source quality: {quality_assessment['quality_level']} (avg: {quality_assessment['avg_score']:.1f}%)")

                # Prepend quality context to vector_context
                vector_context = quality_prefix + "\n\n---\n\n".join(
                    [f"Source: {r.source} (Score: {r.score:.1f}%)\n{r.text}" for r in search_results]
                )

        # Select prompt template and format context based on query type
        if query_type == QueryType.STATISTICAL and sql_success:
            # SQL-only: Use SQL_ONLY_PROMPT
            prompt_template = SQL_ONLY_PROMPT
            context = sql_context
        elif query_type == QueryType.HYBRID and sql_success and vector_context:
            # Hybrid: Use HYBRID_PROMPT with separate SQL and vector sections
            prompt_template = HYBRID_PROMPT
            # HYBRID_PROMPT expects separate sql_context and vector_context parameters
            # We'll handle this in generate_response call
            context = None  # Signal to use sql_context + vector_context
        elif query_type == QueryType.CONTEXTUAL and vector_context:
            # Contextual: Use CONTEXTUAL_PROMPT
            prompt_template = CONTEXTUAL_PROMPT
            context = vector_context
        else:
            # Fallback: Use default SYSTEM_PROMPT_TEMPLATE
            prompt_template = SYSTEM_PROMPT_TEMPLATE
            # Combine contexts for fallback
            context_parts = []
            if sql_context:
                context_parts.append(f"STATISTICAL DATA (FROM SQL DATABASE):\n{sql_context}")
            if vector_context:
                context_parts.append(f"DOCUMENTS AND ANALYSIS:\n{vector_context}")
            context = "\n\n=== === ===\n\n".join(context_parts) if context_parts else "No relevant information found."

        # Generate response with appropriate prompt
        if context is None:
            # HYBRID case: pass sql_context and vector_context separately
            answer = self.generate_response_hybrid(
                query=query,
                sql_context=sql_context,
                vector_context=vector_context,
                conversation_history=conversation_history,
            )
        else:
            # All other cases: use standard generate_response
            answer = self.generate_response(
                query=query,
                context=context,
                conversation_history=conversation_history,
                prompt_template=prompt_template,
            )

        # SMART FALLBACK: If SQL succeeded but LLM couldn't USE the data, retry with vector search
        # Only trigger if LLM explicitly says it can't PARSE/USE provided data, NOT when data doesn't exist
        decline_phrases = [
            "cannot parse",
            "unable to interpret the data",
            "the provided data is unclear",
            "no statistical data provided",  # LLM didn't see SQL context
            "the data format is unclear",
        ]
        should_fallback = sql_success and not sql_failed and any(phrase in answer.lower() for phrase in decline_phrases)

        if should_fallback:
            logger.warning("SQL succeeded but LLM couldn't parse results - retrying with vector search")

            # Get vector search results (if not already retrieved)
            if not search_results:
                search_results = self.search(
                    query=effective_query,
                    k=adaptive_k,
                    min_score=request.min_score,
                    max_expansions=classification.max_expansions,  # Pass pre-computed expansion limit
                )

            if search_results:
                # Retry with vector context using CONTEXTUAL_PROMPT
                fallback_vector_context = "\n\n---\n\n".join(
                    [f"Source: {r.source} (Score: {r.score:.1f}%)\n{r.text}" for r in search_results]
                )

                # Regenerate response with vector context
                answer = self.generate_response(
                    query=query,
                    context=fallback_vector_context,
                    conversation_history=conversation_history,
                    prompt_template=CONTEXTUAL_PROMPT,
                )
                logger.info("Vector search fallback succeeded")

        # Apply post-processing to answer
        # Issue #6: Remove excessive hedging language from statistical responses
        if query_type in (QueryType.STATISTICAL, QueryType.HYBRID):
            answer = self._remove_excessive_hedging(answer)

        # Apply superscript formatting to citations (Phase 18)
        answer = self._format_superscript_citations(answer)

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Generate visualization for statistical queries with SQL results
        visualization = None
        if query_type in (QueryType.STATISTICAL, QueryType.HYBRID):
            if sql_success and sql_result_data:
                try:
                    logger.info("Generating visualization for SQL results")
                    viz_data = self.visualization_service.generate_visualization(
                        query=query,
                        sql_result=sql_result_data
                    )
                    visualization = Visualization(
                        pattern=viz_data["pattern"],
                        viz_type=viz_data["viz_type"],
                        plot_json=viz_data["plot_json"],
                        plot_html=viz_data["plot_html"],
                    )
                    logger.info(f"Visualization generated: {viz_data['viz_type']} ({viz_data['pattern']})")
                except Exception as e:
                    # Don't fail the whole request if visualization fails
                    logger.warning(f"Visualization generation failed: {e}")
            else:
                # Log why visualization was skipped
                if not sql_success:
                    logger.info(
                        "Visualization skipped: SQL query failed, used vector fallback. "
                        "Visualizations require structured data from SQL results."
                    )
                elif not sql_result_data:
                    logger.info("Visualization skipped: SQL query returned no results")

        # Auto-save interaction for conversation history (enables follow-up resolution)
        if request.conversation_id:
            response_sources = search_results if request.include_sources else []
            self._save_interaction(
                query=query,
                response=answer,
                sources=response_sources,
                processing_time_ms=processing_time_ms,
                conversation_id=request.conversation_id,
                turn_number=request.turn_number,
            )

        # Map query_type enum to string for API response (Phase 18)
        query_type_str = query_type.value if query_type else None
        logger.warning(f"[DEBUG-RETURN] BEFORE ChatResponse: query_type={query_type}, query_type_str={query_type_str}, type={type(query_type)}")

        return ChatResponse(
            answer=answer,
            sources=search_results if request.include_sources else [],
            query=query,
            processing_time_ms=processing_time_ms,
            model=self._model,
            conversation_id=request.conversation_id,
            turn_number=request.turn_number,
            generated_sql=generated_sql,
            visualization=visualization,
            query_type=query_type_str,
        )
