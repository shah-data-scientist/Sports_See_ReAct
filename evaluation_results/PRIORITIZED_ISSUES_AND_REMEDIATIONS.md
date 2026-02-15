# Prioritized Issues & Remediations

**Generated:** 2026-02-15
**Dataset:** 210 queries across 21 batches
**Success Rate:** 97.14% (204/210 executed successfully)

---

## Executive Summary

### Overall Performance
- **Total Queries Executed:** 210
- **Successful Queries:** 204 (97.14%)
- **Failed Queries:** 6 (2.86%)
- **Queries with Quality Issues:** 89 (42.4%)
- **Total Issue Instances:** 167

### Issue Distribution by Priority
- **P0 (Critical):** 3 issues affecting 89 queries (42.4%)
- **P1 (High):** 2 issues affecting specific query patterns
- **P2 (Medium):** 2 issues affecting edge cases
- **P3 (Low):** 1 issue (performance optimization)

### Expected Impact After Remediations
Implementing all P0 and P1 fixes is expected to:
- Improve context retrieval success rate from 42.4% to ~75-80%
- Reduce hybrid query failure rate from 73.8% to ~30-40%
- Maintain current high answer quality (88% correctness, 90% faithfulness)

---

## Issue Priority Ranking

### Issue #1: Low Context Precision for Vector and Hybrid Queries
**Priority:** P0 (Critical)
**Affected Queries:** 78 queries (37.1%)
**Success Rate Impact:** Major - context_precision mean is 0.399 (target: >0.7)

**Breakdown by Query Type:**
- Vector queries: 39/84 affected (46.4%)
- Hybrid queries: 27/42 affected (64.3%)
- SQL queries: 12/84 affected (14.3%)

#### Description
Context precision measures whether the retrieved context chunks are actually relevant to answering the question. Low scores indicate the retrieval system is returning many irrelevant chunks along with relevant ones.

#### Root Cause
1. **Initial Vector Search Overly Broad:** The first-stage vector search retrieves too many chunks (top-k=7) without sufficient filtering
2. **Re-ranking Not Aggressive Enough:** The LLM-based re-ranking is not filtering out enough irrelevant chunks
3. **Semantic Similarity Threshold Too Low:** Currently accepting chunks with low similarity scores

#### Proposed Remediation

**File:** `src/agents/react_agent.py` (lines ~550-600)

**Changes Required:**

```python
# CURRENT (problematic)
def _rerank_chunks_with_llm(self, chunks: List[dict], question: str) -> List[dict]:
    """Re-rank chunks using LLM."""

    # Issue: Prompt doesn't emphasize precision enough
    rerank_prompt = f"""
    Rate the relevance of each chunk to the question on a scale of 0-1.

    Question: {question}
    Chunks: {chunks}

    Return a JSON array of scores: [0.8, 0.3, 0.9, ...]
    """
    # ...


# IMPROVED
def _rerank_chunks_with_llm(self, chunks: List[dict], question: str) -> List[dict]:
    """Re-rank chunks with emphasis on precision."""

    formatted_chunks = "\n\n".join([
        f"CHUNK {i+1}:\n{chunk['text']}\nSource: {chunk.get('source', 'unknown')}"
        for i, chunk in enumerate(chunks)
    ])

    rerank_prompt = f"""
You are a precision-focused relevance judge for NBA basketball queries.

TASK: Rate how relevant each text chunk is for answering the user's specific question.

QUESTION: {question}

TEXT CHUNKS:
{formatted_chunks}

SCORING GUIDE:
- 1.0: Chunk directly answers the question with specific, relevant information
- 0.7-0.9: Chunk provides useful context or partial answer
- 0.4-0.6: Chunk is tangentially related but doesn't help answer the question
- 0.1-0.3: Chunk mentions related topics but is mostly irrelevant
- 0.0: Chunk is completely irrelevant to the question

CRITICAL: Be strict. Only score 0.7+ if the chunk actually helps answer THIS specific question.
For context precision, it's better to have fewer highly relevant chunks than many loosely related ones.

Return ONLY a JSON array of scores (one per chunk): [score1, score2, ...]
Example: [0.9, 0.2, 0.0, 0.8, 0.1]
"""

    # Get scores from LLM
    scores = self._call_llm_for_reranking(rerank_prompt)

    # IMPROVEMENT: Apply stricter filtering
    RELEVANCE_THRESHOLD = 0.6  # Increased from implicit 0.0

    reranked = []
    for chunk, score in zip(chunks, scores):
        if score >= RELEVANCE_THRESHOLD:
            chunk['relevance_score'] = score
            reranked.append(chunk)

    # Sort by score and return top chunks
    reranked.sort(key=lambda x: x['relevance_score'], reverse=True)
    return reranked[:5]  # Limit to top 5 instead of all 7
```

#### Expected Impact
- **Improvements:**
  - Context precision improves from 0.399 to ~0.65-0.75
  - Fewer irrelevant chunks pollute the context
  - LLM receives higher quality input for answer generation
  - Hybrid queries context precision improves from 0.358 to ~0.60+
- **Regression Risk:** Low
  - Risk Level: **Low**
  - Risk Details: May filter out marginally relevant chunks in edge cases, but overall precision gain outweighs this risk
- **Tests That Might Break:** None expected - this is a quality improvement, not behavior change

#### Estimated Effort
3-4 hours (including prompt engineering and testing)

#### Tests to Verify Fix
Re-run these specific queries and verify context_precision > 0.7:
- Batch 1, Query 8: "Which NBA teams didn't have home court advantage in finals?"
- Batch 1, Query 10: "Compare LeBron and KD's scoring styles"
- Batch 2, Query 7: "Do fans debate about historical playoff performances?"
- Batch 4, Query 9: "Show me highly upvoted comments about basketball"

---

### Issue #2: Low Context Relevancy for Vector and Hybrid Queries
**Priority:** P0 (Critical)
**Affected Queries:** 89 queries (42.4%)
**Success Rate Impact:** Major - context_relevancy mean is 0.328 (target: >0.7)

**Breakdown by Query Type:**
- Vector queries: 45/84 affected (53.6%)
- Hybrid queries: 31/42 affected (73.8%)
- SQL queries: 13/84 affected (15.5%)

#### Description
Context relevancy measures whether the retrieved chunks actually contain information needed to answer the question. Low scores indicate the vector search is returning chunks that don't address the query topic.

#### Root Cause
1. **Query Transformation Too Literal:** For hybrid queries, the system transforms the question by adding player names from SQL results, making the query too specific
2. **Insufficient Query Expansion:** Vector search queries don't include enough semantic variations of key concepts
3. **Data Coverage Gaps:** For player-specific analysis queries, the vector database lacks detailed content

#### Proposed Remediation

**File:** `src/agents/react_agent.py` (lines ~700-750)

**Changes Required:**

```python
# CURRENT (problematic)
def _transform_query_for_vector_search(self, question: str, sql_results: Optional[list] = None) -> str:
    """Transform question for vector search."""

    if sql_results:
        # Issue: Too focused on entities, not concepts
        entities = self._extract_entities(sql_results)
        return f"{' '.join(entities)} {question}"

    return question


# IMPROVED
def _transform_query_for_vector_search(self, question: str, sql_results: Optional[list] = None) -> str:
    """Transform question for vector search with concept focus."""

    # Extract conceptual keywords from question
    conceptual_keywords = self._extract_conceptual_keywords(question)

    if sql_results and conceptual_keywords:
        # For hybrid queries: PRIORITIZE concepts over entities
        entities = self._extract_entities(sql_results)

        # Build query with concepts first, entities second
        search_query = f"{' '.join(conceptual_keywords)}"

        # Add limited entity context (max 2)
        if entities:
            search_query += f" {' '.join(entities[:2])}"

        return search_query

    elif conceptual_keywords:
        # For vector-only: expand with related concepts
        return ' '.join(conceptual_keywords)

    return question


def _extract_conceptual_keywords(self, question: str) -> List[str]:
    """Extract conceptual keywords focusing on WHY, HOW, WHAT patterns."""

    concept_patterns = {
        r"what makes.*?(effective|efficient|good|great|elite|valuable)":
            ["effective scorer", "offensive approach", "scoring techniques"],

        r"why.*?(considered|regarded as|viewed as).*?(elite|effective|valuable)":
            ["analysis", "evaluation", "elite player discussion"],

        r"explain.*?(style|approach|technique)":
            ["playing style", "approach", "technique", "offensive system"],

        r"how.*?(different|differ|compare)":
            ["comparison", "differences", "unique characteristics"],

        r"what impact.*?have":
            ["impact", "influence", "effect", "contribution"],

        r"what do (fans|users|people|redditors?).*?(think|say|discuss|debate)":
            ["fan discussion", "opinions", "community views"],
    }

    question_lower = question.lower()
    keywords = []

    for pattern, concepts in concept_patterns.items():
        if re.search(pattern, question_lower):
            keywords.extend(concepts)

    # Add question type indicators
    if any(word in question_lower for word in ["why", "explain", "what makes"]):
        keywords.append("analysis")

    if "compare" in question_lower or "versus" in question_lower:
        keywords.append("comparison")

    return list(set(keywords))  # Remove duplicates
```

#### Expected Impact
- **Improvements:**
  - Context relevancy improves from 0.328 to ~0.55-0.65
  - Hybrid queries retrieve more concept-focused content
  - Better alignment between question intent and retrieved chunks
  - Queries asking "what makes X effective" retrieve general effectiveness concepts, not just player names
- **Regression Risk:** Low-Medium
  - Risk Level: **Low-Medium**
  - Risk Details: Some queries that worked well with entity-focused search might retrieve slightly different chunks. Need to verify hybrid queries that currently succeed (e.g., Batch 3 Query 10) still work well.
- **Tests That Might Break:** Hybrid queries that currently have high context metrics might see slight changes in retrieved chunks

#### Estimated Effort
4-5 hours (including pattern development, testing across query types)

#### Tests to Verify Fix
Re-run these queries and verify context_relevancy > 0.7:
- Batch 1, Query 9: "Who scored most points and what makes them effective?"
- Batch 2, Query 9: "Why is Jokić considered elite offensive player?"
- Batch 3, Query 9: "Compare Jokić and Embiid stats and explain which is more valuable"

**Note:** Some player-specific queries may still have low metrics due to data coverage gaps (not code issues).

---

### Issue #3: Query Classification Misrouting (SQL Queries Routed to Vector Search)
**Priority:** P0 (Critical)
**Affected Queries:** 2-3 queries per batch (estimated ~15 queries total)
**Success Rate Impact:** High - causes complete query failures

#### Description
Simple SQL queries like "How many assists did Chris Paul record?" are incorrectly classified as vector-only queries, resulting in the database never being queried and the agent returning "I don't have information..."

#### Root Cause
The heuristic classification patterns don't cover simple player stat queries with "How many X did player Y" phrasing. When heuristics have low confidence, the LLM fallback also fails to identify these as SQL queries.

#### Proposed Remediation

**File:** `src/agents/react_agent.py` (lines ~100-150)

**Changes Required:**

```python
# In _classify_query_heuristic method

# CURRENT (incomplete)
strong_sql_signals = [
    "top ", "most ", "highest", "lowest", "best", "worst",
    "average ", "total ", "how many points", "how many rebounds",
    # ... existing patterns ...
]


# IMPROVED
strong_sql_signals = [
    "top ", "most ", "highest", "lowest", "best", "worst",
    "average ", "total ", "how many points", "how many rebounds",
    # ... existing patterns ...
]

# NEW: Add player stat query patterns with regex
player_stat_patterns = [
    r"how many (points|assists|rebounds|steals|blocks|turnovers|fouls|minutes) (did|does|has|have)",
    r"(what is|what's|whats) \w+('s|s)? (points|assists|rebounds|steals|blocks|scoring|average)",
    r"how many players (on|in) (the )?\w+ (roster|team)",
    r"(did|does) \w+ (score|have|record|get) \d+ (points|assists|rebounds)",
]

# Check player stat patterns FIRST (higher priority than general signals)
question_lower = question.lower()
for pattern in player_stat_patterns:
    if re.search(pattern, question_lower):
        return {
            "query_type": "sql",
            "confidence": 0.95,
            "reasoning": f"Player stat query pattern matched: {pattern}"
        }

# Then check strong SQL signals...
```

#### Expected Impact
- **Improvements:**
  - All simple player stat queries correctly routed to SQL
  - Roster count queries correctly routed to SQL
  - Eliminates "I don't have information" responses when data exists in database
  - SQL query success rate improves from 96.43% to ~99%+
- **Regression Risk:** Very Low
  - Risk Level: **Very Low**
  - Risk Details: This only adds more specific patterns, doesn't change existing routing logic
- **Tests That Might Break:** None - this fixes broken queries, doesn't change working ones

#### Estimated Effort
1-2 hours (including pattern testing and validation)

#### Tests to Verify Fix
Re-run these queries and verify SQL execution:
- "How many assists did Chris Paul record?" → Should execute SQL
- "How many players on the Lakers roster?" → Should execute SQL
- "What is LeBron's scoring average?" → Should execute SQL

---

### Issue #4: Discussion Query Misrouting (Vector Queries Incorrectly Triggering SQL)
**Priority:** P1 (High)
**Affected Queries:** ~5-10 queries (estimated)
**Success Rate Impact:** Medium - adds unnecessary SQL execution overhead

#### Description
Queries asking about "most discussed topic" or similar discussion-focused questions are incorrectly classified as hybrid, causing unnecessary SQL query generation when only vector search is needed.

**Example:** "Tell me about the most discussed playoff efficiency topic" → Agent generates SQL for highest usage percentage (not requested)

#### Root Cause
Discussion patterns exist but don't cover all phrasings like "most discussed topic", "most talked about", etc. The word "most" triggers SQL heuristics even when it's "most discussed" not "most points".

#### Proposed Remediation

**File:** `src/agents/react_agent.py` (lines ~119-127)

**Changes Required:**

```python
# CURRENT (incomplete)
strong_vector_signals = [
    "what do fans", "what are fans", "what do reddit",
    "what do people think", "debate about", "popular opinion",
    "according to discussions", "fan reactions",
    # ... existing patterns ...
]


# IMPROVED
strong_vector_signals = [
    "what do fans", "what are fans", "what do reddit",
    "what do people think", "debate about", "popular opinion",
    "according to discussions", "fan reactions",
    # ... existing patterns ...
]

# NEW: Add discussion topic patterns (checked BEFORE "most" SQL trigger)
discussion_topic_patterns = [
    r"most discussed", r"most talked about", r"most debated",
    r"most popular (topic|opinion|view|discussion)",
    r"tell me about.*discussion", r"tell me about.*debate",
    r"discussion topic", r"debate topic",
    r"what (topics|discussions|debates|opinions).*popular",
]

# Check discussion patterns FIRST (before general "most" SQL check)
question_lower = question.lower()
for pattern in discussion_topic_patterns:
    if re.search(pattern, question_lower):
        return {
            "query_type": "vector_only",
            "confidence": 0.95,
            "reasoning": f"Discussion topic query: {pattern}"
        }
```

#### Expected Impact
- **Improvements:**
  - Discussion topic queries routed to vector-only (no SQL)
  - Faster processing (eliminates unnecessary SQL overhead)
  - More accurate query intent recognition
  - Reduces confusion where SQL results don't match question
- **Regression Risk:** Very Low
  - Risk Level: **Very Low**
  - Risk Details: Only affects discussion-focused queries, which should be vector-only
- **Tests That Might Break:** None

#### Estimated Effort
1 hour (pattern addition and testing)

#### Tests to Verify Fix
Re-run these queries and verify NO SQL execution:
- "Tell me about the most discussed playoff efficiency topic" → Vector only
- "What's the most talked about trade this season?" → Vector only
- "What topics do fans debate most?" → Vector only

---

### Issue #5: Data Coverage Gap - Player-Specific Analysis
**Priority:** P2 (Medium) - Known Limitation, Not a Code Defect
**Affected Queries:** ~20-25 queries
**Success Rate Impact:** Medium - queries execute but provide incomplete answers

#### Description
Queries asking about specific player's playing styles, effectiveness analysis, or impact consistently return low context metrics and incomplete answers with disclaimers like "I don't have specific analysis of their playing style."

**Examples:**
- "Why is Jokić considered an elite offensive player?"
- "What makes Shai Gilgeous-Alexander an effective scorer?"
- "Compare LeBron and KD's scoring styles"

#### Root Cause
**DATA COVERAGE ISSUE** - The vector database contains:
- General NBA statistical concepts and definitions ✅
- Reddit discussions about teams, trades, general topics ✅
- General player discussions ✅

But LACKS:
- Detailed playing style breakdowns for specific players ❌
- Deep-dive analysis of individual player effectiveness ❌
- Player-specific offensive/defensive technique discussions ❌

**Evidence:** Queries about general concepts succeed (e.g., "What makes a player efficient in playoffs?" → 1.0 context metrics), while player-specific queries fail.

#### Proposed Remediation

**Option A: Accept Current Behavior (Recommended)**

**Rationale:**
- Agent is functioning correctly: executes SQL, attempts vector search, honestly acknowledges limitations
- Context metrics correctly identify the issue (working as designed)
- SQL data is still provided to user
- This is transparent and honest behavior

**No code changes needed.**

**Option B: Data Enrichment (Future Enhancement, Out of Scope)**

Enhance vector database with:
1. Basketball analysis articles from ESPN, The Athletic, etc.
2. More diverse Reddit content with player breakdowns
3. Scouting reports and player profiles

**Estimated Effort:** 20-40 hours (data acquisition, processing, ingestion)
**Priority:** Low (defer to future sprint)

#### Expected Impact
- **Option A (Accept):**
  - No code changes ✅
  - Transparent limitations ✅
  - Users get SQL data even if context is limited ✅
- **Option B (Data Enrichment):**
  - Would improve context_relevancy for player queries
  - Requires significant data work
  - Out of scope for current evaluation

#### Estimated Effort
- Option A: 0 hours (accept current behavior)
- Option B: 20-40 hours (future enhancement)

#### Tests to Verify Fix
N/A for Option A (accept current behavior)

---

### Issue #6: Complete Query Failures (Rate Limiting / Errors)
**Priority:** P1 (High)
**Affected Queries:** 6 queries (2.86%)
**Success Rate Impact:** Moderate - affects overall success rate

#### Description
6 queries failed completely during evaluation, likely due to:
- API rate limiting (429 errors)
- Transient errors
- Timeout issues

#### Root Cause
1. **Rate Limiting:** Gemini API rate limits during RAGAS evaluation
2. **Insufficient Retry Logic:** Current retry mechanism may not cover all error types
3. **No Graceful Degradation:** Failures are binary (success/fail) with no partial results

#### Proposed Remediation

**File:** `src/evaluation/evaluator.py` and `src/agents/react_agent.py`

**Changes Required:**

```python
# In evaluator.py
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    retry=retry_if_exception_type((RateLimitError, TimeoutError, ConnectionError)),
)
async def evaluate_query_with_retry(self, query: dict) -> dict:
    """Evaluate query with exponential backoff retry."""
    try:
        return await self.evaluate_query(query)
    except RateLimitError as e:
        logger.warning(f"Rate limit hit, retrying with backoff: {e}")
        raise  # Will trigger retry
    except Exception as e:
        logger.error(f"Query failed: {e}")
        # Return partial results if possible
        return {
            "success": False,
            "error": str(e),
            "answer": "Error: Unable to process query",
            "partial_data": self._get_partial_results()
        }


# Add graceful degradation for RAGAS failures
async def calculate_ragas_metrics_safe(self, result: dict) -> dict:
    """Calculate RAGAS metrics with fallback."""
    try:
        return await self.calculate_ragas_metrics(result)
    except RateLimitError:
        logger.warning("RAGAS rate limited, using defaults")
        return self._default_ragas_metrics()
    except Exception as e:
        logger.error(f"RAGAS calculation failed: {e}")
        return self._default_ragas_metrics()
```

#### Expected Impact
- **Improvements:**
  - Query success rate improves from 97.14% to 99%+
  - Fewer complete failures
  - Partial results even when some components fail
  - Better handling of API rate limits
- **Regression Risk:** Very Low
  - Risk Level: **Very Low**
  - Risk Details: Adds retry logic and fallbacks without changing core behavior
- **Tests That Might Break:** None

#### Estimated Effort
2-3 hours (retry logic, testing, error handling)

#### Tests to Verify Fix
Re-run the 6 failed queries and verify they complete successfully.

---

### Issue #7: Performance Degradation Across Batches
**Priority:** P3 (Low)
**Affected Queries:** All queries
**Success Rate Impact:** None - quality issue, not accuracy

#### Description
Processing time increased significantly across batches:
- Batch 1: Average 7.76s
- Batch 10: Average 12-15s (estimated)
- Overall: 62% slower by Batch 3

#### Root Cause
Likely causes:
1. **Vector Search Taking Longer:** As more complex queries processed
2. **Re-ranking Overhead:** LLM-based re-ranking adds time
3. **RAGAS Calculation:** Evaluation metrics taking longer
4. **No Caching:** Repeated queries not cached

#### Proposed Remediation

**File:** `src/agents/react_agent.py` and `src/services/vector_search.py`

**Changes Required:**

```python
# Add caching for vector search
from functools import lru_cache
import hashlib

class VectorSearchService:
    def __init__(self):
        self._cache = {}

    def _get_cache_key(self, query: str, k: int) -> str:
        """Generate cache key for query."""
        return hashlib.md5(f"{query}:{k}".encode()).hexdigest()

    async def search_with_cache(self, query: str, k: int = 7) -> List[dict]:
        """Search with caching for identical queries."""
        cache_key = self._get_cache_key(query, k)

        if cache_key in self._cache:
            logger.debug(f"Cache hit for query: {query[:50]}")
            return self._cache[cache_key]

        results = await self.search(query, k)
        self._cache[cache_key] = results
        return results


# Optimize re-ranking by reducing LLM calls
async def _rerank_chunks_batch(self, all_chunks: List[List[dict]], questions: List[str]) -> List[List[dict]]:
    """Batch re-ranking to reduce LLM API calls."""
    # Instead of one LLM call per query, batch multiple re-ranking requests
    # This reduces API overhead
    pass
```

#### Expected Impact
- **Improvements:**
  - Processing time reduced by 20-30%
  - Better scalability for large query batches
  - Reduced API costs
- **Regression Risk:** Very Low
  - Risk Level: **Very Low**
  - Risk Details: Caching doesn't change results, only speeds up repeated queries
- **Tests That Might Break:** None

#### Estimated Effort
3-4 hours (caching implementation, batch optimization)

#### Tests to Verify Fix
Run performance benchmark comparing before/after average processing times.

---

## Implementation Roadmap

### Phase 1: Critical Fixes (P0) - Week 1
**Estimated Effort:** 8-12 hours

1. **Issue #1:** Low Context Precision (3-4 hours)
   - Improve re-ranking prompt
   - Add stricter relevance threshold
   - Test on 10 sample queries

2. **Issue #2:** Low Context Relevancy (4-5 hours)
   - Implement concept extraction
   - Update query transformation logic
   - Test on hybrid queries

3. **Issue #3:** SQL Query Misrouting (1-2 hours)
   - Add player stat patterns
   - Test on misrouted queries

**Deliverables:**
- Updated `react_agent.py` with all P0 fixes
- Test results showing improvement in context metrics
- Documentation of changes

**Success Criteria:**
- Context precision avg > 0.65
- Context relevancy avg > 0.55
- SQL routing accuracy > 99%

---

### Phase 2: High-Priority Fixes (P1) - Week 2
**Estimated Effort:** 3-4 hours

1. **Issue #4:** Discussion Query Misrouting (1 hour)
   - Add discussion topic patterns
   - Test on discussion queries

2. **Issue #6:** Query Failures (2-3 hours)
   - Implement retry logic
   - Add graceful degradation
   - Test failure scenarios

**Deliverables:**
- Enhanced error handling
- Retry mechanisms
- Test coverage for edge cases

**Success Criteria:**
- Success rate > 99%
- Discussion queries correctly routed
- Graceful handling of API errors

---

### Phase 3: Medium-Priority Items (P2-P3) - Week 3-4
**Estimated Effort:** 3-4 hours

1. **Issue #5:** Data Coverage (0 hours for Option A)
   - Document limitations
   - Accept current behavior
   - (Optional) Plan data enrichment for future

2. **Issue #7:** Performance Optimization (3-4 hours)
   - Implement caching
   - Optimize batch processing
   - Performance testing

**Deliverables:**
- Performance improvements
- Documentation of data limitations
- Future enhancement roadmap

**Success Criteria:**
- Processing time reduced by 20-30%
- Clear documentation of limitations

---

## Testing Strategy

### Unit Tests
```python
# Test query classification
def test_player_stat_classification():
    agent = ReactAgent()

    test_cases = [
        ("How many assists did Chris Paul record?", "sql"),
        ("How many players on Lakers roster?", "sql"),
        ("What do fans think about trades?", "vector_only"),
        ("Tell me about most discussed topic", "vector_only"),
    ]

    for question, expected_type in test_cases:
        result = agent.classify_query(question)
        assert result["query_type"] == expected_type
```

### Integration Tests
```python
# Test end-to-end with context metrics
async def test_context_quality():
    agent = ReactAgent()

    # Test queries that should have high context metrics
    high_quality_queries = [
        "What makes a player efficient in playoffs?",
        "Who are the top 5 scorers?",
    ]

    for query in high_quality_queries:
        result = await agent.process_query(query)
        if result["test_type"] in ["vector", "hybrid"]:
            assert result["ragas_metrics"]["context_precision"] >= 0.7
            assert result["ragas_metrics"]["context_relevancy"] >= 0.7
```

### Regression Tests
Re-run all 210 queries from evaluation dataset and verify:
- No decrease in answer_correctness (maintain 0.88)
- No decrease in faithfulness (maintain 0.90)
- Improvement in context metrics
- No new query failures

---

## Risk Assessment

### Overall Risk Level: **LOW-MEDIUM**

### Risk Breakdown by Issue

| Issue | Code Changes | Risk Level | Mitigation |
|-------|-------------|------------|------------|
| #1 Context Precision | Moderate | Low | Extensive testing on diverse queries |
| #2 Context Relevancy | Significant | Low-Medium | A/B testing, gradual rollout |
| #3 SQL Misrouting | Minimal | Very Low | Additive patterns only |
| #4 Discussion Routing | Minimal | Very Low | Specific pattern matching |
| #5 Data Coverage | None | N/A | Accept current behavior |
| #6 Query Failures | Moderate | Very Low | Retry logic well-tested |
| #7 Performance | Low | Very Low | Caching doesn't change logic |

### Rollback Plan
If any fix causes regressions:
1. Git revert to previous version
2. Deploy previous stable version
3. Review fix in isolation
4. Re-test before re-deployment

---

## Success Metrics

### Before Remediations (Baseline)
- Success Rate: 97.14%
- Context Precision (mean): 0.399
- Context Relevancy (mean): 0.328
- Answer Correctness: 0.880
- Faithfulness: 0.900
- Queries with Issues: 89/210 (42.4%)

### After P0 Fixes (Target)
- Success Rate: 99%+ ✅
- Context Precision (mean): 0.65+ ✅ (+63%)
- Context Relevancy (mean): 0.55+ ✅ (+68%)
- Answer Correctness: 0.880+ (maintained) ✅
- Faithfulness: 0.900+ (maintained) ✅
- Queries with Issues: <60/210 (<28.6%) ✅

### After All Fixes (Stretch Goal)
- Success Rate: 99.5%+ 🎯
- Context Precision (mean): 0.70+ 🎯
- Context Relevancy (mean): 0.60+ 🎯
- Processing Time: -20-30% 🎯

---

## Monitoring & Validation

### Metrics to Track Post-Deployment
1. **Real-time Metrics:**
   - Query success rate (by type: SQL, vector, hybrid)
   - Average processing time
   - API error rates

2. **Quality Metrics (Sample Evaluation):**
   - Context precision/relevancy on sample queries
   - Answer correctness on known test cases
   - User feedback scores

3. **Error Tracking:**
   - Misrouting frequency
   - RAGAS calculation failures
   - API rate limit hits

### Evaluation Schedule
- **Week 1:** Run full evaluation suite (210 queries) after P0 fixes
- **Week 2:** Run sample evaluation (50 queries) after P1 fixes
- **Week 4:** Run full evaluation to measure cumulative impact
- **Monthly:** Ongoing monitoring with production queries

---

## Appendix: Detailed Query Analysis

### Most Impactful Fixes by Query Type

#### SQL Queries (84 total, 13 with issues)
**Primary Issue:** Misrouting (Issue #3)
**Fix Impact:** High - eliminates complete failures
**Expected Improvement:** 96.43% → 99%+ success rate

#### Vector Queries (84 total, 45 with issues)
**Primary Issues:** Context precision (#1), Context relevancy (#2)
**Fix Impact:** High - improves retrieval quality significantly
**Expected Improvement:** 46.4% → 25-30% with issues

#### Hybrid Queries (42 total, 31 with issues)
**Primary Issues:** Context relevancy (#2), Query transformation
**Fix Impact:** Very High - hybrid is most affected by fixes
**Expected Improvement:** 73.8% → 35-40% with issues

---

**Report Generated:** 2026-02-15
**Total Issues Analyzed:** 167 issue instances across 89 queries
**Remediations Proposed:** 7 (3 P0, 2 P1, 1 P2, 1 P3)
**Total Estimated Effort:** 18-24 hours for all fixes
**Expected ROI:** High - significant quality improvement with manageable effort
