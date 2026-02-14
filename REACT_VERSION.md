# Sports_See - ReAct Agent Architecture

**This is the ReAct architecture implementation version.**

## What's Different?

This repository implements a **ReAct (Reasoning + Acting) agent pattern** using LangChain, replacing the pattern-based classification system.

### Key Changes:
- ✅ LLM-driven tool selection (replaces regex classification)
- ✅ Parallel SQL + Vector execution
- ✅ Smart synthesis with SQL > Vector hierarchy
- ✅ Simplified codebase (~1000 lines removed)

### Original Repository:
- **Location**: `../Sports_See/`
- **Architecture**: Pattern-based classification with fallback logic

### This Repository:
- **Location**: `Sports_See_ReAct/`
- **Architecture**: ReAct agent with LLM-driven routing

---

## Development Approach:

**Phase 1**: Implement ReAct (in progress)
**Phase 2**: Validate against original
**Phase 3**: Benchmark performance
**Phase 4**: Migrate if successful

---

Created: 2026-02-14