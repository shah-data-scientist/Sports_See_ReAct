# Archived Legacy Code

This directory contains code from the pre-LangChain migration architecture.

## 📦 Archived Files

### `query_classifier_legacy.py` (1,068 lines)
**Archived:** 2026-02-14
**Reason:** Replaced by LangChain SQL Agent (create_sql_agent) and vector retriever

**What it was:**
- Pattern-based query classification using 1,068 lines of regex patterns
- Routed queries to: SQL-only, Vector-only, or Hybrid
- Required manual maintenance for each new query type

**Why it was replaced:**
- **Brittle**: Regex patterns couldn't adapt to new query variations
- **Unmaintainable**: Adding new patterns required extensive testing
- **No self-correction**: Failed queries had no recovery mechanism
- **Complex**: 1,068 lines of patterns vs LangChain's dynamic tool selection

**What replaced it:**
- LangChain `create_sql_agent()` with ReAct pattern for SQL queries
- LangChain `VectorStoreRetriever` for vector search
- Agent-based tool selection (no manual classification needed)

**Migration impact:**
- **Code reduction**: -1,068 lines from query_classifier.py
- **Improved accuracy**: Agent can self-correct SQL errors
- **Better UX**: Users see reasoning trace for transparency

---

## 📊 Migration Results

**Testing (9 test cases, 3 from each category):**
- ✅ SQL queries: 3/3 passed (100%)
- ✅ Vector queries: 3/3 passed (100%)
- ✅ Hybrid queries: 3/3 passed (100%)

**Performance:**
- Pattern-based: ~1,330ms average
- LangChain agent: ~4,135ms average (+210%)
- **Optimization applied**: Static schema pre-loading to reduce LLM calls

**Code metrics:**
- Removed: 1,068 lines (query_classifier.py)
- Reduced: 186 lines in sql_tool.py (-28%)
- Total savings: ~1,250 lines

---

**Last Updated:** 2026-02-14  
**Migration Status:** ✅ Complete
