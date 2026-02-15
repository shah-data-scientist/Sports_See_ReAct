# Batch #1 - Issues & Remediations

**Generated:** 2026-02-15 18:16:10

**Batch Summary:**
- **Total Queries:** 10
- **Success Rate:** 100% (all queries executed)
- **Critical Issues:** 6 (affecting 3 queries)
- **Warnings:** 0

---

## Executive Summary

### Issue Distribution by Query Type

| Query Type | Queries | Critical Issues | Success Rate |
|------------|---------|-----------------|--------------|
| SQL        | 4       | 0               | 100% ✅      |
| Vector     | 4       | 2               | 75% ⚠️       |
| Hybrid     | 2       | 4               | 0% ❌        |

**Key Finding:** Hybrid queries are struggling with context precision and relevancy, indicating vector search is returning irrelevant chunks.

---

## Critical Issues (6)

### Issue #1: Low Context Metrics on Hybrid Queries (Queries #9, #10)

**Affected Queries:**
- Query #9: "Who scored the most points this season and what makes them an effective scorer?"
  - context_precision: 0.143
  - context_relevancy: 0.000
- Query #10: "Compare LeBron James and Kevin Durant's scoring and explain their scoring styles"
  - context_precision: 0.000
  - context_relevancy: 0.000

**Pattern Identified:**
Both hybrid queries successfully retrieve SQL data but fail to get relevant vector search results for the contextual part ("what makes them effective", "explain their scoring styles").

**Root Cause Analysis:**
1. **Query Transformation Issue**: The agent transforms the full question into a vector search query, but may not be extracting the right terms
   - Example: "Who scored the most points and what makes them effective?" → "Shai Gilgeous-Alexander effective scorer"
   - The transformation focuses on the player name from SQL results, but loses focus on "scoring effectiveness" concepts

2. **Re-ranking Failure**: Re-ranking is returning all 0 scores (observed in logs)
   - LLM re-ranking prompt may not be effective
   - Re-ranking may be filtering out all chunks

3. **Vector Database Coverage**: The vector database may not have detailed content about "what makes player X effective" for specific players

**Evidence:**
```
Query #9 answer: "I don't have detailed analysis of what specifically makes him an effective scorer."
Query #10 answer: "I don't have specific analysis of their playing styles."
```

**Proposed Remediation #1A: Improve Query Transformation**

**File:** [src/agents/react_agent.py](src/agents/react_agent.py) (lines ~700-750)

**Current Behavior:**
- Extracts player name from SQL results
- Adds contextual keywords from original question
- May be too specific to the player instead of the concept

**Proposed Fix:**
Improve query transformation to focus on **concepts** rather than just player names when SQL data is available.

**Code Change:**
```python
def _transform_query_for_vector_search(self, question: str, sql_results: list) -> str:
    """Transform question for vector search based on SQL results."""

    # Extract player/team names from SQL results
    entities = self._extract_entities_from_sql_results(sql_results)

    # Extract conceptual keywords from question
    # Focus on WHY, HOW, WHAT questions
    conceptual_keywords = self._extract_conceptual_keywords(question)

    # PRIORITIZE concepts over entities for hybrid queries
    if conceptual_keywords:
        # Example: "what makes them effective" → "effective scorer techniques"
        # Example: "explain their scoring styles" → "scoring styles offensive approach"
        search_query = f"{' '.join(conceptual_keywords)}"

        # Add entities as secondary context
        if entities:
            search_query += f" {' '.join(entities[:2])}"  # Limit to 2 entities
    else:
        # Fallback to current behavior
        search_query = f"{' '.join(entities)} {question}"

    return search_query

def _extract_conceptual_keywords(self, question: str) -> list:
    """Extract conceptual keywords from question."""
    # Keywords indicating conceptual queries
    concept_patterns = {
        r"what makes.*effective": ["effective", "scoring techniques", "offensive approach"],
        r"why.*considered": ["analysis", "evaluation", "discussion"],
        r"explain.*style": ["playing style", "approach", "technique"],
        r"how.*different": ["comparison", "differences", "unique"],
    }

    question_lower = question.lower()
    keywords = []

    for pattern, concepts in concept_patterns.items():
        if re.search(pattern, question_lower):
            keywords.extend(concepts)

    return keywords
```

**Expected Impact:**
- ✅ Better vector search queries focusing on concepts
- ✅ Higher context_relevancy (target: >0.7)
- ✅ More informative answers for hybrid queries

**Estimated Effort:** 2-3 hours

---

**Proposed Remediation #1B: Fix Re-ranking Returning All 0 Scores**

**File:** [src/agents/react_agent.py](src/agents/react_agent.py) (lines ~550-600)

**Current Behavior:**
- Re-ranking LLM returns all 0 scores
- Results in no relevant chunks being identified

**Root Cause:**
The re-ranking prompt may be asking for binary relevance (0 or 1) instead of a relevance score, or the LLM is being too strict.

**Proposed Fix:**
Improve re-ranking prompt to request scores on a scale and provide clearer instructions.

**Code Change:**
```python
# CURRENT (problematic)
rerank_prompt = f"""
Rate the relevance of each chunk to the question on a scale of 0-1.

Question: {question}

Chunks: {chunks}

Return a JSON array of scores: [0.8, 0.3, 0.9, ...]
"""

# IMPROVED
rerank_prompt = f"""
You are a relevance judge for NBA basketball queries.

TASK: Rate how relevant each text chunk is to answering the user's question.

QUESTION: {question}

TEXT CHUNKS:
{formatted_chunks}

SCORING GUIDE:
- 1.0: Chunk directly answers the question with specific information
- 0.7-0.9: Chunk contains relevant context or partial answer
- 0.4-0.6: Chunk is tangentially related
- 0.1-0.3: Chunk mentions related topics but doesn't help answer
- 0.0: Chunk is completely irrelevant

IMPORTANT: Be generous with scores above 0.5 for chunks that provide ANY useful context.

Return ONLY a JSON array of scores (one per chunk): [score1, score2, ...]
Example: [0.9, 0.6, 0.1, 0.8, 0.3]
"""
```

**Expected Impact:**
- ✅ Re-ranking returns varied scores instead of all 0s
- ✅ Relevant chunks are retained
- ✅ context_precision improves (target: >0.7)

**Estimated Effort:** 1 hour

---

### Issue #2: Low Context Metrics on Vector Query #8

**Affected Query:**
- Query #8: "Which NBA teams didn't have home court advantage in finals according to discussions?"
  - context_precision: 0.000
  - context_relevancy: 0.000
  - **Unexpected SQL execution**: Agent generated SQL when this should be vector-only

**Pattern Identified:**
This is a **vector-only** question (asks about "discussions"), but the agent incorrectly routed it as **hybrid** and generated SQL.

**Root Cause:**
Query classification heuristics may have low confidence, triggering LLM classification, which incorrectly identified it as hybrid.

**Evidence:**
```sql
SELECT abbreviation FROM teams WHERE abbreviation NOT IN (...)
```
This SQL doesn't answer "according to discussions" - it lists teams NOT mentioned in a hardcoded list, which is wrong.

**Proposed Remediation #2: Improve Classification for "Discussion" Queries**

**File:** [src/agents/react_agent.py](src/agents/react_agent.py) (lines ~250-300)

**Current Behavior:**
- Heuristic patterns may not strongly identify "according to discussions" as vector-only
- LLM classification may default to hybrid when uncertain

**Proposed Fix:**
Add stronger heuristic patterns for discussion/opinion-based queries.

**Code Change:**
```python
# In _classify_query_heuristic method

# Add discussion patterns to VECTOR_ONLY patterns
DISCUSSION_PATTERNS = [
    r"according to discussions?",
    r"what do (fans|users|people|redditors?) (think|say|believe|discuss)",
    r"(opinions?|debates?|views?) (about|on)",
    r"fan (reactions?|discussions?|sentiment)",
]

# Boost confidence for discussion patterns
for pattern in DISCUSSION_PATTERNS:
    if re.search(pattern, question.lower()):
        return {
            "query_type": "vector_only",
            "confidence": 0.95,  # High confidence
            "reasoning": f"Discussion-based query: '{pattern}'"
        }
```

**Expected Impact:**
- ✅ "Discussion" queries routed to vector-only (no SQL)
- ✅ Faster processing (no SQL generation)
- ✅ More accurate answers

**Estimated Effort:** 30 minutes

---

## Warnings (0)

No warnings detected in this batch.

---

## Additional Observations

### Visualization Failures (Non-blocking)

**Pattern:** 3 visualization generation failures with error: `'str' object has no attribute 'get'`

**Affected Queries:** #2, #3, #10

**Impact:** Low - queries still succeed, visualization is optional

**Root Cause:** Likely data type mismatch in visualization service when processing SQL results.

**Proposed Remediation #3: Fix Visualization Data Type Handling**

**File:** [src/services/visualization.py](src/services/visualization.py)

**Estimated Effort:** 1 hour

**Priority:** Low (visualization is optional, doesn't block answers)

---

### API Rate Limiting

**Pattern:** One 429 error during RAGAS context relevancy calculation

**Impact:** Low - one metric failed for one query, didn't prevent evaluation

**Mitigation:** Already implemented (retries with backoff)

**Recommendation:** Monitor rate limiting in future batches. If frequent, consider:
- Adding longer delays between RAGAS calls
- Using batch processing for RAGAS metrics
- Upgrading to paid Gemini tier

---

## Remediation Priority Ranking

| Priority | Issue | Impact | Effort | ROI |
|----------|-------|--------|--------|-----|
| **P0 - Critical** | #1A: Improve query transformation | 🔴 High | 2-3h | ⭐⭐⭐ |
| **P0 - Critical** | #1B: Fix re-ranking all 0 scores | 🔴 High | 1h | ⭐⭐⭐ |
| **P1 - High** | #2: Improve discussion query classification | 🟡 Medium | 30m | ⭐⭐ |
| **P2 - Low** | #3: Fix visualization data types | 🟢 Low | 1h | ⭐ |

**Recommended Action:**
1. Apply **Remediation #1A + #1B** (fix hybrid query vector search)
2. Apply **Remediation #2** (fix discussion query classification)
3. Re-run Batch #1 to verify fixes
4. Continue to Batch #2 if improvements confirmed

**Estimated Total Effort:** 4-5 hours

---

## Success Metrics After Remediation

**Target Improvements:**
- ✅ Hybrid queries: context_precision > 0.7 (currently 0.07)
- ✅ Hybrid queries: context_relevancy > 0.7 (currently 0.0)
- ✅ Vector-only routing accuracy: 100% (currently 75% - query #8 misrouted)
- ✅ Overall RAGAS scores: maintain >0.85 average

**Re-test Queries:**
- Query #8 (vector classification)
- Query #9 (hybrid context relevancy)
- Query #10 (hybrid context precision)

---

**Generated:** 2026-02-15 18:16:10
**Batch:** #1
**Status:** Awaiting user decision on remediations
