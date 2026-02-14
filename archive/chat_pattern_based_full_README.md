# Archived Pattern-Based ChatService

**Archived on**: 2026-02-14
**File**: chat_pattern_based_full.py (1,444 lines)

## What was archived:
Complete pattern-based ChatService implementation with:
- QueryClassifier integration (regex-based routing)
- Fixed pipeline: classify → route → generate
- Pattern-based query classification (STATISTICAL/CONTEXTUAL/HYBRID)
- Biographical query handling
- Follow-up query rewriting

## Key methods archived:
- `chat()` - Main chat method with classification routing (lines 1111-1444)
- `query_classifier` property (lines 497-501)
- `_rewrite_biographical_for_sql()` (line 691)
- Classification logic (lines 1182-1188)

## Why archived:
Replaced with ReAct (Reasoning + Acting) agent architecture that uses LLM-driven tool selection instead of regex patterns.

## New implementation:
See current `src/services/chat.py` for ReAct agent-based implementation.
