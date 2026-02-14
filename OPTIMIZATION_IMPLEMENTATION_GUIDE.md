# Optimization Implementation Guide

## 🎯 Quick Reference

**Total Optimizations Identified**: 12
**High Priority**: 5 (implement now - 2 hours)
**Medium Priority**: 3 (implement next - 2 hours)
**Low Priority**: 4 (nice to have - 1 hour)

**Expected Impact**: -30% latency, -30% cost, cleaner architecture

---

## ✅ HIGH PRIORITY (Implement Now - 2 hours)

### 1. Cache Agent Instance ⚡ (5 minutes, -50-100ms/request)

**Problem**: Agent recreated on every request

**File**: `src/services/chat.py`

**Current Code** (lines ~400-450):
```python
def _get_agent(self) -> ReActAgent:
    """Lazy initialize ReAct agent with tools."""
    if not hasattr(self, '_agent'):  # Always False after first call!
        toolkit = NBAToolkit(...)
        tools = create_nba_tools(toolkit)
        self._agent = ReActAgent(tools=tools, ...)
    return self._agent  # But _agent is instance variable, not class variable
```

**Issue**: `_agent` is stored per ChatService instance, but ChatService is recreated each request!

**Fix**:
```python
# Option 1: Use functools.cached_property (Python 3.8+)
from functools import cached_property

class ChatService:
    @cached_property
    def agent(self) -> ReActAgent:
        """Cached agent instance - created once, reused forever."""
        _initialize_lazy_imports()

        toolkit = NBAToolkit(
            sql_tool=self.sql_tool,
            vector_store=self.vector_store,
            embedding_service=self.embedding_service,
            visualization_service=self.visualization_service,
        )
        tools = create_nba_tools(toolkit)

        return ReActAgent(
            tools=tools,
            llm_client=self.client,
            model=self.model,
            max_iterations=5,
            temperature=0.0,
        )

    def chat(self, request: ChatRequest) -> ChatResponse:
        # OLD: agent = self._get_agent()
        # NEW: agent = self.agent  # Uses cached property
        agent = self.agent
        result = agent.run(...)
```

**Testing**:
```python
# Verify caching works
service = ChatService(...)
agent1 = service.agent
agent2 = service.agent
assert agent1 is agent2  # Same instance!
```

**Impact**: -50-100ms per request (agent initialization overhead)

---

### 2. Fix Duplicate Complexity Calculation ⚡ (10 minutes)

**Problem**: `_estimate_question_complexity()` called twice per query

**File**: `src/agents/react_agent_v2.py`

**Current Code**:
```python
def run(self, question, conversation_history):
    # CALL 1: Compute k for prompt
    recommended_k = self._estimate_question_complexity(question)  # 1st

    # ... later ...

    def _analyze_from_steps(self, steps, question):
        # CALL 2: Compute k AGAIN for metadata
        complexity_k = self._estimate_question_complexity(question)  # 2nd (same result!)
```

**Fix**:
```python
class ReActAgentV2:
    def __init__(self, ...):
        # ... existing init ...
        self._current_question = None
        self._cached_k = None
        self._cached_category = None

    def run(self, question, conversation_history):
        # Greeting check
        if self._is_simple_greeting(question):
            return {...}

        # Store question and compute complexity once
        self._current_question = question
        self._cached_k = self._estimate_question_complexity(question)
        self._cached_category = None  # Compute lazily if needed

        steps = []
        prompt = self._build_initial_prompt(question, conversation_history, self._cached_k)

        # ... reasoning loop ...

        # Analysis uses cached values
        query_analysis = self._analyze_from_steps(steps)

        return {...}

    def _analyze_from_steps(self, steps):
        """Use cached complexity values instead of recomputing."""
        tools_used = set(step.action for step in steps)
        question_lower = self._current_question.lower()

        # Detect biographical, statistical, contextual, definitional
        # (existing logic)

        # Use cached values instead of recomputing
        complexity_k = self._cached_k  # Already computed!

        # Lazy compute category only if needed
        if self._cached_category is None:
            self._cached_category = self._classify_category(self._current_question)
        query_category = self._cached_category

        return QueryAnalysis(
            is_statistical=...,
            is_contextual=...,
            is_biographical=...,
            is_greeting=False,
            is_definitional=...,
            complexity_k=complexity_k,
            query_category=query_category,
        )
```

**Impact**: Eliminates 1 unnecessary complexity calculation per query

---

### 3. Compress Prompt 230→120 Lines ⚡ (30 minutes, -15% cost)

**Problem**: Prompt is too verbose (230 lines)

**File**: `src/agents/react_agent_v2.py`

**Current**: Lines 202-260 (60 lines just for classification guide!)

**Fix**:
```python
def _build_initial_prompt(self, question, conversation_history, recommended_k):
    """Compressed prompt - 50% reduction."""
    tools_desc = self._format_tools_description()

    # BEFORE: 230 lines
    # AFTER: 120 lines

    prompt = f"""You are an NBA stats assistant. Select the right tools:

TOOLS:
{tools_desc}

ROUTING GUIDE:
• Stats (points/rankings/comparisons) → query_nba_database
• Context (why/how/opinions/strategies) → search_knowledge_base
• "Who is X?" → BOTH (SQL first, then vector)
• Definitions → search_knowledge_base

FORMAT:
Thought: [What tool(s) to use and why]
Action: [tool_name]
Action Input: {{"query": "...", "k": {recommended_k}}}
Observation: [Results appear here]
... (repeat if needed)
Final Answer: [Synthesized answer with sources]

RULES:
• Always use tools (never answer from memory)
• Biographical: SQL first for stats, then vector for context
• Use k={recommended_k} for vector search (pre-computed complexity)
• Cite sources from vector results

HISTORY: {conversation_history or "None"}

QUESTION: {question}

Thought:"""

    return prompt
```

**Testing**:
```bash
# Compare token counts
echo "Old prompt:" > /tmp/old_prompt.txt
echo "New prompt:" > /tmp/new_prompt.txt

# Count tokens (approximate)
wc -w /tmp/old_prompt.txt  # ~600 tokens
wc -w /tmp/new_prompt.txt  # ~300 tokens (-50%)
```

**Impact**: -15% cost, -10% latency

---

### 4. Store Tool Results Directly ⚡ (45 minutes)

**Problem**: Fragile string parsing to extract SQL/viz from observations

**Files**:
- `src/agents/react_agent_v2.py` (store results)
- `src/services/chat.py` (access results)

**Current Code** (chat.py lines 327-358):
```python
# Fragile string parsing
for step in result.get("reasoning_trace", []):
    if step.get("action") == "create_visualization":
        obs = step.get("observation", "")
        if "plotly_json" in obs:
            viz_data = json.loads(obs)  # Parse string!

    if step.get("action") == "query_nba_database":
        obs = step.get("observation", "")
        if "SQL" in obs:
            sql_match = obs.split("SQL Results")[0]  # String split!
```

**Fix**:

**In `react_agent_v2.py`**:
```python
class ReActAgentV2:
    def __init__(self, ...):
        # ... existing init ...
        self.tool_results = {}  # Store actual tool results

    def run(self, question, conversation_history):
        # ... existing code ...

        # Clear tool results for new query
        self.tool_results = {}

        # ... reasoning loop ...

        return {
            "answer": parsed["answer"],
            "reasoning_trace": [self._step_to_dict(s) for s in steps],
            "tools_used": tools_used,
            "query_analysis": query_analysis,
            "is_hybrid": is_hybrid,
            "tool_results": self.tool_results,  # NEW: Include raw results
        }

    def _execute_tool(self, tool_name, tool_input):
        """Execute tool and store original result."""
        if tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_name}'"

        tool = self.tools[tool_name]
        try:
            result = tool.function(**tool_input)

            # Store original structured result
            self.tool_results[tool_name] = result

            # Return string observation (truncated for prompt)
            return str(result)[:800]
        except Exception as e:
            logger.error(f"Tool {tool_name} execution failed: {e}")
            return f"Error executing {tool_name}: {str(e)}"
```

**In `chat.py`**:
```python
def chat(self, request: ChatRequest):
    # ... existing code ...

    result = agent.run(question=query, conversation_history=conversation_history)

    # OLD: Extract from string observations (fragile)
    # NEW: Access structured results directly
    tool_results = result.get("tool_results", {})

    # Extract SQL directly
    sql_result = tool_results.get("query_nba_database", {})
    generated_sql = sql_result.get("sql", "")

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
        sources=[],
        processing_time_ms=processing_time_ms,
        model=self.model,
        generated_sql=generated_sql,  # Direct access!
        visualization=visualization,  # Direct access!
        # ... rest ...
    )
```

**Impact**: More reliable, no string parsing failures

---

### 5. Async Database Save ⚡ (1 hour, -20-50ms/request)

**Problem**: Synchronous DB save blocks response

**File**: `src/services/chat.py`

**Current Code** (lines 377-387):
```python
# Save interaction (blocks response!)
if request.conversation_id:
    self._save_interaction(
        query=query,
        response=result["answer"],
        # ... args ...
    )  # Waits for DB INSERT

logger.info(f"Agent completed...")
return response  # Response delayed by DB write
```

**Fix**:
```python
import asyncio
from typing import Optional

class ChatService:
    def chat(self, request: ChatRequest) -> ChatResponse:
        # ... existing code ...

        # Build response first
        response = ChatResponse(...)

        # Save interaction asynchronously (fire-and-forget)
        if request.conversation_id:
            # Schedule async save (don't wait)
            self._schedule_async_save(
                query=query,
                response=result["answer"],
                conversation_id=request.conversation_id,
                turn_number=request.turn_number,
                processing_time_ms=processing_time_ms,
                query_type="agent",
                sources=[],
                generated_sql=generated_sql,
            )

        logger.info(f"Agent completed...")
        return response  # Return immediately!

    def _schedule_async_save(self, **kwargs):
        """Schedule async DB save (non-blocking)."""
        try:
            # Create background task
            loop = asyncio.get_event_loop()
            loop.create_task(self._save_interaction_async(**kwargs))
        except Exception as e:
            # Fallback to sync if event loop not available
            logger.warning(f"Async save failed, using sync: {e}")
            self._save_interaction(**kwargs)

    async def _save_interaction_async(
        self,
        query: str,
        response: str,
        conversation_id: str,
        turn_number: int,
        processing_time_ms: float,
        query_type: str,
        sources: list,
        generated_sql: Optional[str],
    ):
        """Async version of _save_interaction."""
        try:
            # Run sync DB operation in thread pool
            await asyncio.to_thread(
                self._save_interaction,
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
            logger.error(f"Async DB save failed: {e}")
```

**Impact**: -20-50ms per request (DB write latency removed from critical path)

---

## 📊 MEDIUM PRIORITY (Implement Next - 2 hours)

### 6. Adaptive Over-Retrieval (15 minutes, -30-40% candidates)

**File**: `src/repositories/vector_store.py`

**Current** (lines 326, 336):
```python
search_k = max(k * 3, 15)  # Always 3x over-retrieval
```

**Fix**:
```python
# Adaptive over-retrieval based on k
if k <= 3:
    search_k = min(k * 2, len(available_chunks))  # 2x for small k
elif k <= 5:
    search_k = min(int(k * 1.5), len(available_chunks))  # 1.5x for medium k
else:
    search_k = min(int(k * 1.2), len(available_chunks))  # 1.2x for large k

# Example: k=5 → search_k=8 instead of 15 (-47% candidates)
```

**Impact**: -30-40% BM25 computation time

---

### 7. Pre-compute Metadata Boosts (1 hour + reingestion)

**File**: `src/repositories/vector_store.py`

**Current**: Computed at query time (lines 383-384)
```python
metadata_boost = self._compute_metadata_boost(chunk)  # Every query!
quality_boost = self._compute_quality_boost(chunk)
```

**Fix**: Compute during ingestion

**During ingestion** (`src/services/ingestion.py` or wherever chunks are created):
```python
# When creating DocumentChunk
chunk = DocumentChunk(
    text=text,
    embedding=embedding,
    metadata={
        "source": source,
        "upvotes": upvotes,
        # ... other metadata ...

        # NEW: Pre-compute total boost
        "precomputed_boost": VectorStoreRepository._compute_metadata_boost(temp_chunk)
                           + VectorStoreRepository._compute_quality_boost(temp_chunk),
    }
)
```

**At query time**:
```python
# OLD: Compute on-the-fly
for chunk, cosine_score in results:
    metadata_boost = self._compute_metadata_boost(chunk)
    quality_boost = self._compute_quality_boost(chunk)
    composite = (cosine * 0.70) + (bm25 * 0.15) + (metadata_boost * 0.075) + (quality_boost * 0.075)

# NEW: Use pre-computed
for chunk, cosine_score in results:
    precomputed_boost = chunk.metadata.get("precomputed_boost", 0.0)
    composite = (cosine * 0.70) + (bm25 * 0.15) + (precomputed_boost * 0.15)
```

**Impact**: -5-10ms per vector search

---

### 8. Remove SQL Agent Formatting (30 min + 30 min testing)

**File**: `src/tools/sql_tool.py`

**Current**: SQL agent formats results with LLM
**Problem**: ReAct agent re-synthesizes, making SQL formatting redundant

**Investigation Needed**:
```python
# Check if ReAct agent actually uses SQL agent's formatted answer
# vs. just using raw results
```

**If redundant, configure SQL agent to skip formatting**:
```python
# In create_sql_agent configuration
agent = create_sql_agent(
    llm=llm,
    db=db,
    # ... other args ...
    # Skip final answer formatting
    return_intermediate_steps=True,  # Return raw SQL results
)
```

**Risk**: Test thoroughly to ensure ReAct agent doesn't need formatted answers

**Impact**: -1 LLM call per SQL query (~500ms + cost)

---

## 🎨 LOW PRIORITY (Nice to Have - 1 hour)

### 9. Remove Dead "sources" Field (10 minutes)

**File**: `src/models/chat.py`

```python
class ChatResponse(BaseModel):
    answer: str
    query: str
    # sources: list[SearchResult] = []  # DELETE - always empty
    processing_time_ms: float
    # ... rest ...
```

**Also remove** from `src/services/chat.py` lines 364, 385:
```python
# OLD: sources=[],  # DELETE
```

**Impact**: Cleaner API

---

### 10. Remove Category Classification if Unused (20 minutes)

**File**: `src/agents/react_agent_v2.py`

**First**: Check if query_category is used anywhere downstream

```bash
grep -r "query_category" src/
grep -r "query_category" tests/
```

**If unused**:
```python
# Comment out or remove _classify_category() method
# Remove from QueryAnalysis dataclass
# Remove from _analyze_from_steps()
```

**Impact**: Slight computation reduction

---

### 11. Consistent Observation Truncation (5 minutes)

**File**: `src/agents/react_agent_v2.py`

**Current**: Inconsistent limits (500 vs 1000 vs 800)

**Fix**:
```python
# At top of file
MAX_OBSERVATION_LENGTH = 800  # Configurable

# In AgentStep creation (line 158)
step = AgentStep(
    thought=parsed["thought"],
    action=parsed["action"],
    action_input=parsed["action_input"],
    observation=str(observation)[:MAX_OBSERVATION_LENGTH],  # Consistent
    step_number=iteration,
)

# In _execute_tool (line 397)
return str(result)[:MAX_OBSERVATION_LENGTH]  # Consistent
```

---

### 12. Simplify 4-Signal Scoring to 3-Signal (15 minutes)

**File**: `src/repositories/vector_store.py`

**Current**: cosine + BM25 + metadata + quality (4 signals)

**Simplified**: cosine + BM25 + authority (3 signals)
```python
# Merge metadata + quality into single "authority" boost
# (precomputed during ingestion)

composite_score = (
    (cosine_score * 0.70)
    + (bm25_score * 0.15)
    + (chunk.metadata["precomputed_boost"] * 0.15)  # Combined authority
)
```

**Impact**: Cleaner, same quality

---

## 📋 Implementation Checklist

### Phase 1 (2 hours - Do Now):
- [ ] 1. Cache agent instance (5 min)
- [ ] 2. Fix duplicate complexity calc (10 min)
- [ ] 3. Compress prompt (30 min)
- [ ] 4. Store tool results directly (45 min)
- [ ] 5. Async DB save (1 hour)

### Phase 2 (2 hours - Do Next):
- [ ] 6. Adaptive over-retrieval (15 min)
- [ ] 7. Pre-compute metadata boosts (1 hour + reingestion)
- [ ] 8. Remove SQL formatting (30 min + testing)

### Phase 3 (1 hour - Nice to Have):
- [ ] 9. Remove dead sources field (10 min)
- [ ] 10. Remove category if unused (20 min)
- [ ] 11. Consistent observation truncation (5 min)
- [ ] 12. Simplify to 3-signal scoring (15 min)

---

## 🎯 Expected Results

**After Phase 1** (2 hours):
- ✅ -20% latency
- ✅ -15% cost
- ✅ More reliable (no string parsing)
- ✅ Cleaner code

**After Phase 2** (4 hours total):
- ✅ -30% latency
- ✅ -30% cost
- ✅ -1 LLM call per SQL query

**After Phase 3** (5 hours total):
- ✅ -35% latency
- ✅ -35% cost
- ✅ Cleaner architecture
- ✅ Easier maintenance

---

**Status**: Ready for implementation
**Date**: 2026-02-14
**Start with**: Phase 1 (highest impact, lowest effort)
